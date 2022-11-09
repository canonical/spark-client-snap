#!/usr/bin/env python3

import os
import sys
from typing import List, Dict
import re
import pwd
import subprocess
import logging
import io
from tempfile import NamedTemporaryFile
import yaml

USER_HOME_DIR_ENT_IDX = 5

EXIT_CODE_BAD_KUBECONFIG = -100
EXIT_CODE_BAD_CONF_ARG = -200
EXIT_CODE_GET_SECRET_FAILED = -300
EXIT_CODE_PUT_SECRET_ENV_FILE_FAILED = -400
EXIT_CODE_PUT_SECRET_LITERAL_FAILED = -500
EXIT_CODE_DEL_SECRET_FAILED = -600
EXIT_CODE_GET_K8S_PROPS_FAILED = -700
EXIT_CODE_GET_PRIMARY_RESOURCES_FAILED = -800
EXIT_CODE_SET_PRIMARY_RESOURCES_FAILED = -900

def read_property_file_unsafe(name: str) -> Dict :
    defaults = dict()
    with open(name) as f:
        for line in f:
            kv = list(filter(None, re.split('=| ', line.strip())))
            k = kv[0]
            v = '='.join(kv[1:])
            defaults[k] = os.path.expandvars(v)
    return defaults

def read_property_file(name: str) -> Dict:
    return read_property_file_unsafe(name) if name and os.path.isfile(name) else dict()

def write_property_file(fp: io.TextIOWrapper, props: Dict, log: bool = None) -> None:
    for k in props.keys():
        v = props[k]
        line = f"{k}={v.strip()}"
        fp.write(line+'\n')
        if (log):
            logging.info(line)

def print_properties(props: Dict) -> None:
    for k in props.keys():
        v = props[k]
        print(f"{k}={v}")

def merge_configurations(dictionaries_to_merge: List[Dict]) -> Dict:
    result = dict()
    for override in dictionaries_to_merge:
        result.update(override)
    return result

def get_static_defaults_conf_file() -> str:
    SPARK_STATIC_DEFAULTS_FILE = f"{os.environ.get('SNAP')}/conf/spark-defaults.conf"
    return SPARK_STATIC_DEFAULTS_FILE

def get_dynamic_defaults_conf_file() -> str:
    SPARK_DYNAMIC_DEFAULTS_FILE = f"{os.environ.get('SNAP_USER_DATA')}/spark-defaults.conf"
    return SPARK_DYNAMIC_DEFAULTS_FILE

def get_env_defaults_conf_file() -> str:
    SPARK_ENV_DEFAULTS_FILE = os.environ.get('SNAP_SPARK_ENV_CONF')
    return SPARK_ENV_DEFAULTS_FILE

def get_snap_temp_dir() -> str:
    return '/tmp/snap.spark-client'

def parse_conf_overrides(conf_args: List) -> Dict:
    conf_overrides = dict()
    if conf_args:
        for c in conf_args:
            try:
                kv = c.split('=')
                k = kv[0]
                v = '='.join(kv[1:])
                conf_overrides[k] = os.environ.get(v, v)
            except IndexError as e:
                logging.error('Configuration related arguments parsing error. Please check input arguments and try again.')
                sys.exit(EXIT_CODE_BAD_CONF_ARG)
    return conf_overrides

def reconstruct_submit_args(args: List, conf: Dict) -> List:
    submit_args = args
    conf_arg = ''
    for k in conf.keys():
        conf_arg += f' --conf {k}={conf[k].strip()}'
    submit_args = [conf_arg] + submit_args
    return submit_args

def get_kube_config() -> str:
    USER_HOME_DIR = pwd.getpwuid(os.getuid())[USER_HOME_DIR_ENT_IDX]
    DEFAULT_KUBECONFIG = f'{USER_HOME_DIR}/.kube/config'
    kubeconfig = os.environ.get('KUBECONFIG') or DEFAULT_KUBECONFIG
    return kubeconfig

def get_kubectl_cmd() -> str:
    kubectl_cmd = '{}/kubectl'.format(os.environ['SNAP'])
    return kubectl_cmd

def autodetect_kubernetes_master(conf: Dict) -> str:
    kubeconfig = get_kube_config()
    namespace = conf.get('spark.kubernetes.namespace')
    context = conf.get('spark.kubernetes.context')
    primary_sa = retrieve_primary_service_account_details(namespace, kubeconfig, context)
    primary_namespace = primary_sa.get('spark.kubernetes.namespace') or 'default'
    kubectl_cmd = build_kubectl_cmd(kubeconfig, primary_namespace, context)
    master_cmd = f"{kubectl_cmd} config view --minify -o jsonpath=\"{{.clusters[0]['cluster.server']}}\""
    default_master = execute_kubectl_cmd(master_cmd, EXIT_CODE_BAD_KUBECONFIG)
    return f'k8s://{default_master}'

def UmaskNamedTemporaryFile(*args, **kargs):
    fdesc = NamedTemporaryFile(*args, **kargs)
    umask = os.umask(0o666)
    os.umask(umask)
    os.chmod(fdesc.name, 0o666 & ~umask)
    return fdesc

def build_kubectl_cmd(kube_config: str, namespace: str, k8s_context: str) -> str:
    kubeconfig = kube_config or get_kube_config()
    kubectl_cmd = get_kubectl_cmd()
    cmd = f"{kubectl_cmd} --kubeconfig {kubeconfig}"
    if namespace:
        cmd += f" --namespace {namespace}"
    if k8s_context:
        cmd += f" --context {k8s_context}"
    return cmd

def build_secret_name(username: str) -> str:
    return f"spark-client-sa-conf-{username or 'spark'}"

def execute_kubectl_cmd(cmd: str, exit_code_on_error: int, log_on_error: bool = True) -> str:
    logging.debug(cmd)
    # kubeconfig = get_kube_config()
    try:
        out = subprocess.check_output(cmd, shell=True)
        result = out.decode('utf-8') if out else None
    except subprocess.CalledProcessError as e:
        if log_on_error:
            logging.error(e.output)
        sys.exit(exit_code_on_error)

    return result

def setup_kubernetes_secret(username: str, namespace: str, kubeconfig: str, k8s_context: str, properties_file: str, conf : List[str]) -> None:
    kubectl_cmd = build_kubectl_cmd(kubeconfig, namespace, k8s_context)
    secret_name = build_secret_name(username)
    props_from_file = read_property_file(properties_file)
    props_from_conf = parse_conf_overrides(conf)
    props = merge_configurations([props_from_file, props_from_conf])
    with UmaskNamedTemporaryFile(mode='w', prefix='spark-dynamic-conf-k8s-', suffix='.conf') as t:
        logging.debug(f'Spark dynamic props available for reference at {get_snap_temp_dir()}{t.name}\n')
        write_property_file(t.file, props)
        t.flush()
        cmd = f"{kubectl_cmd} create secret generic {secret_name} --from-env-file={t.name}"
        logging.debug(cmd)
        execute_kubectl_cmd(cmd, EXIT_CODE_PUT_SECRET_ENV_FILE_FAILED)

def retrieve_kubernetes_secret(username: str, namespace: str, kubeconfig: str, k8s_context: str, keys: List[str]) -> Dict:
    kubectl_cmd = build_kubectl_cmd(kubeconfig, namespace, k8s_context)
    secret_name = build_secret_name(username)
    result = dict()

    if not keys or len(keys) == 0:
        cmd = f"{kubectl_cmd} get secret {secret_name} -o yaml"
        out_yaml_str = execute_kubectl_cmd(cmd, EXIT_CODE_GET_SECRET_FAILED)
        secret = yaml.safe_load(out_yaml_str)
        keys = secret['data'].keys() if secret.get('data') else []

    for k in keys:
        k1 = k.replace('.', '\\.')
        cmd = f"{kubectl_cmd} get secret {secret_name} -o jsonpath='{{.data.{k1}}}' | base64 --decode"
        result[k] = execute_kubectl_cmd(cmd, EXIT_CODE_GET_SECRET_FAILED)

    return result

def delete_kubernetes_secret(username: str, namespace: str, kubeconfig: str, k8s_context: str) -> None:
    kubectl_cmd = build_kubectl_cmd(kubeconfig, namespace, k8s_context)
    secret_name = build_secret_name(username)
    cmd = f"{kubectl_cmd} delete secret {secret_name}"
    execute_kubectl_cmd(cmd, EXIT_CODE_DEL_SECRET_FAILED, log_on_error=False)

def get_management_label(label: bool = True) -> str:
    return 'app.kubernetes.io/managed-by=spark-client' if label else 'app.kubernetes.io/managed-by'

def get_primary_label(label: bool = True) -> str:
    return 'app.kubernetes.io/spark-client-primary=1' if label else 'app.kubernetes.io/spark-client-primary'

def retrieve_primary_service_account_details(namespace: str, kubeconfig: str, k8s_context: str) -> Dict:
    kubectl_cmd = build_kubectl_cmd(kubeconfig, namespace, k8s_context)
    label = get_primary_label()
    cmd = f"{kubectl_cmd}  get serviceaccount -l {label} -A -o yaml"
    out_yaml_str = execute_kubectl_cmd(cmd, EXIT_CODE_GET_PRIMARY_RESOURCES_FAILED)
    out = yaml.safe_load(out_yaml_str)
    result = dict()
    if len(out['items']) > 0:
        result['spark.kubernetes.authenticate.driver.serviceAccountName'] = out['items'][0]['metadata']['name']
        result['spark.kubernetes.namespace'] = out['items'][0]['metadata']['namespace']
    return result

def is_primary_sa_defined(namespace: str, kubeconfig: str, k8s_context: str) -> bool:
    conf = retrieve_primary_service_account_details(namespace, kubeconfig, k8s_context)
    return len(conf.keys()) > 0

def get_dynamic_defaults():
    kubeconfig = get_kube_config()
    setup_dynamic_defaults = retrieve_primary_service_account_details(None, kubeconfig, None)
    primary_username = setup_dynamic_defaults.get('spark.kubernetes.authenticate.driver.serviceAccountName') or 'spark'
    primary_namespace = setup_dynamic_defaults.get('spark.kubernetes.namespace') or 'default'
    setup_dynamic_defaults_conf = retrieve_kubernetes_secret(primary_username, primary_namespace, kubeconfig, None, None)
    return merge_configurations([setup_dynamic_defaults, setup_dynamic_defaults_conf])


def print_help_for_missing_or_inaccessible_kubeconfig_file(kubeconfig: str):
    print('\nERROR: Missing kubeconfig file {}. Or default kubeconfig file {}/.kube/config not found.'.format(kubeconfig, pwd.getpwuid(os.getuid())[5]))
    print('\n')
    print('Looks like either kubernetes is not set up properly or default kubeconfig file is not accessible!')
    print('Please take the following remedial actions.')
    print('	1. Please set up kubernetes and make sure kubeconfig file is available, accessible and correct.')
    print('	2. sudo snap connect spark-client:dot-kube-config')

def print_help_for_bad_kubeconfig_file(kubeconfig: str):
    print('\nERROR: Invalid or incomplete kubeconfig file {}. One or more of the following entries might be missing or invalid.\n'.format(kubeconfig))
    print('	- current-context')
    print('	- context.name')
    print('	- context.namespace')
    print('	- context.cluster')
    print('	- cluster.name')
    print('	- cluster.server')
    print(' - cluster.certificate-authority-data')
    print('Please take the following remedial actions.')
    print('	1. Please set up kubernetes and make sure kubeconfig file is available, accessible and correct.')
    print('	2. sudo snap connect spark-client:dot-kube-config')

def select_context_id(kube_cfg: Dict) -> int:
    NO_CONTEXT = -1
    SINGLE_CONTEXT = 0
    context_names = [n['name'] for n in kube_cfg['contexts']]

    selected_context_id = NO_CONTEXT
    if len(context_names) == 1:
        return SINGLE_CONTEXT

    context_list_ux = '\n'.join(["{}. {}".format(context_names.index(a), a) for a in context_names])
    while selected_context_id == NO_CONTEXT:
        print (context_list_ux)
        print('\nPlease select a kubernetes context by index:')
        selected_context_id = input()

        try:
           int(selected_context_id)
        except ValueError:
            print('Invalid context index selection, please try again....')
            selected_context_id = NO_CONTEXT
            continue

        if int(selected_context_id) not in range(len(context_names)):
            print('Invalid context index selection, please try again....')
            selected_context_id = NO_CONTEXT
            continue

    return int(selected_context_id)

def get_defaults_from_kubeconfig(kube_config: str, context: str = None) -> Dict:
    USER_HOME_DIR = pwd.getpwuid(os.getuid())[USER_HOME_DIR_ENT_IDX]
    DEFAULT_KUBECONFIG = f'{USER_HOME_DIR}/.kube/config'
    kubeconfig = kube_config or DEFAULT_KUBECONFIG
    try:
        with open(kubeconfig) as f:
            kube_cfg = yaml.safe_load(f)
            context_names = [n['name'] for n in kube_cfg['contexts']]
            certs = [n['cluster']['certificate-authority-data'] for n in kube_cfg['clusters']]
            current_context = context or kube_cfg['current-context']
    except IOError as ioe:
        print_help_for_missing_or_inaccessible_kubeconfig_file(kubeconfig)
        sys.exit(-1)
    except KeyError as ke:
        print_help_for_bad_kubeconfig_file(kubeconfig)
        sys.exit(-2)

    try:
        context_id = context_names.index(current_context)
    except ValueError:
        print(f'WARNING: Current context in provided kubeconfig file {kubeconfig} is invalid!')
        print(f'\nProceeding with explicit context selection....')
        context_id = select_context_id(kube_cfg)

    defaults = {}
    defaults['context'] = context_names[context_id]
    defaults['namespace'] = 'default'
    defaults['cert'] = certs[context_id]
    defaults['config'] = kubeconfig
    defaults['user'] = 'spark'

    return defaults

def set_up_user(username: str, name_space: str, kube_config: str, k8s_context: str, defaults: Dict, mark_primary: bool) -> None:
    namespace = name_space or defaults['namespace']
    kubeconfig = kube_config or defaults['config']
    context_name = k8s_context or defaults['context']
    kubectl_cmd = build_kubectl_cmd(kubeconfig, namespace, context_name)

    rolebindingname = username + '-role'
    roleaccess='view'
    label = get_management_label()

    os.system(f"{kubectl_cmd} create serviceaccount {username}")
    os.system(f"{kubectl_cmd} create rolebinding {rolebindingname} --role={roleaccess} --serviceaccount={namespace}:{username}")

    primary_label_to_remove = get_primary_label(label=False)
    primary_label_full = get_primary_label()

    primary = retrieve_primary_service_account_details(namespace, kubeconfig, context_name)
    is_primary_defined = len(primary.keys()) > 0

    logging.debug(f"is_primary_defined={is_primary_defined}")
    logging.debug(f"mark_primary={mark_primary}")

    if is_primary_defined and mark_primary:
        sa_to_unlabel = primary['spark.kubernetes.authenticate.driver.serviceAccountName']
        namespace_of_sa_to_unlabel = primary['spark.kubernetes.namespace']
        rolebindingname_to_unlabel = sa_to_unlabel + '-role'
        kubectl_cmd_unlabel = build_kubectl_cmd(kubeconfig, namespace_of_sa_to_unlabel, context_name)

        os.system(f"{kubectl_cmd_unlabel} label serviceaccount --namespace={namespace_of_sa_to_unlabel} {sa_to_unlabel} {primary_label_to_remove}-")
        os.system(f"{kubectl_cmd_unlabel} label rolebinding --namespace={namespace_of_sa_to_unlabel} {rolebindingname_to_unlabel} {primary_label_to_remove}-")

        os.system(f"{kubectl_cmd} label serviceaccount {username} {label} {primary_label_full}")
        os.system(f"{kubectl_cmd} label rolebinding {rolebindingname} {label} {primary_label_full}")
    elif is_primary_defined and not mark_primary:
        os.system(f"{kubectl_cmd} label serviceaccount {username} {label}")
        os.system(f"{kubectl_cmd} label rolebinding {rolebindingname} {label}")
    elif not is_primary_defined:
        os.system(f"{kubectl_cmd} label serviceaccount {username} {label} {primary_label_full}")
        os.system(f"{kubectl_cmd} label rolebinding {rolebindingname} {label} {primary_label_full}")
    else:
        logging.warning("Labeling logic issue.....")


def cleanup_user(username: str, namespace: str, kubeconfig: str, k8s_context: str) -> None:
    kubectl_cmd = build_kubectl_cmd(kubeconfig, namespace, k8s_context)
    rolebindingname = username + '-role'

    os.system(f"{kubectl_cmd} delete serviceaccount {username}")
    os.system(f"{kubectl_cmd} delete rolebinding {rolebindingname}")
    delete_kubernetes_secret(username, namespace, kubeconfig, k8s_context)
