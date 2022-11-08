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

def generate_spark_default_conf() -> Dict:
    generated_defaults = dict()
    USER_HOME_DIR = pwd.getpwuid(os.getuid())[USER_HOME_DIR_ENT_IDX]
    SCALA_HIST_FILE_DIR = os.environ.get('SNAP_USER_COMMON', USER_HOME_DIR)
    generated_defaults['spark.driver.extraJavaOptions'] = f'-Dscala.shell.histfile={SCALA_HIST_FILE_DIR}/.scala_history'
    return generated_defaults

def read_property_file(name: str) -> Dict :
    defaults = dict()
    with open(name) as f:
        for line in f:
            kv = list(filter(None, re.split('=| ', line.strip())))
            k = kv[0]
            v = '='.join(kv[1:])
            defaults[k] = os.path.expandvars(v)
    return defaults

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
    kubectl_cmd = get_kubectl_cmd()
    context = conf.get('spark.kubernetes.context')
    if context:
        master_kubectl_cmd = f"{kubectl_cmd} --kubeconfig {kubeconfig} --context {context} config view --minify -o jsonpath=\"{{.clusters[0]['cluster.server']}}\""
    else:
        master_kubectl_cmd = f"{kubectl_cmd} --kubeconfig {kubeconfig} config view --minify -o jsonpath=\"{{.clusters[0]['cluster.server']}}\""
    try:
       default_master = subprocess.check_output(master_kubectl_cmd, shell=True)
       k8s_master_uri = 'k8s://' + default_master.decode("utf-8")
    except subprocess.CalledProcessError as e:
       logging.error(f'Cannot determine default kubernetes control plane url. Probably bad or missing kubeconfig file {kubeconfig}')
       logging.warning(f'Please set the KUBECONFIG environment variable to point to the kubeconfig. Or fix the default kubeconfig {kubeconfig}')
       logging.error(e.output)
       sys.exit(EXIT_CODE_BAD_KUBECONFIG)
    return k8s_master_uri

def UmaskNamedTemporaryFile(*args, **kargs):
    fdesc = NamedTemporaryFile(*args, **kargs)
    umask = os.umask(0o666)
    os.umask(umask)
    os.chmod(fdesc.name, 0o666 & ~umask)
    return fdesc

def build_kubectl_cmd(namespace: str, k8s_context: str) -> str:
    kubeconfig = get_kube_config()
    kubectl_cmd = get_kubectl_cmd()
    cmd = f"{kubectl_cmd} --kubeconfig {kubeconfig} --namespace={namespace}"
    if k8s_context:
        cmd += f" --context {k8s_context}"
    return cmd

def build_secret_name(username: str, namespace: str) -> str:
    return f"spark-client-sa-conf-{username or 'spark'}"

def execute_kubectl_cmd(cmd: str, exit_code_on_error: int) -> str:
    logging.debug(cmd)
    # kubeconfig = get_kube_config()
    try:
        out = subprocess.check_output(cmd, shell=True)
        result = out.decode('utf-8') if out else None
    except subprocess.CalledProcessError as e:
        # logging.error(
        #     f'Probably bad or missing kubeconfig file {kubeconfig}')
        # logging.warning(
        #     f'Please set the KUBECONFIG environment variable to point to the kubeconfig. Or fix the default kubeconfig {kubeconfig}')
        logging.error(e.output)
        sys.exit(exit_code_on_error)

    return result

def setup_kubernetes_secret_literal(username: str, namespace: str, k8s_context: str, conf : List[str]) -> None:
    kubectl_cmd = build_kubectl_cmd(namespace, k8s_context)
    secret_name = build_secret_name(username, namespace)
    cmd = f"{kubectl_cmd} create secret generic {secret_name}"

    if conf:
        for c in conf:
            cmd += f" --from-literal={c}"

    defaults = generate_spark_default_conf()
    for k in defaults.keys():
        cmd += f" --from-literal={k}={defaults[k]}"

    cmd += f" --from-literal=spark.kubernetes.authenticate.driver.serviceAccountName={username}"
    cmd += f" --from-literal=spark.kubernetes.namespace={namespace}"

    execute_kubectl_cmd(cmd, EXIT_CODE_PUT_SECRET_LITERAL_FAILED)

def setup_kubernetes_secret_env_file(username: str, namespace: str, k8s_context: str, properties_file: str) -> None:
    if not properties_file:
        return
    kubectl_cmd = build_kubectl_cmd(namespace, k8s_context)
    secret_name = build_secret_name(username, namespace)
    cmd = f"{kubectl_cmd} create secret generic {secret_name} --from-env-file={properties_file}"
    execute_kubectl_cmd(cmd, EXIT_CODE_PUT_SECRET_ENV_FILE_FAILED)

def retrieve_kubernetes_secret(username: str, namespace: str, k8s_context: str, keys: List[str]) -> Dict:
    kubectl_cmd = build_kubectl_cmd(namespace, k8s_context)
    secret_name = build_secret_name(username, namespace)
    result = dict()

    if not keys or len(keys) == 0:
        cmd = f"{kubectl_cmd} get secret {secret_name} -o yaml"
        out_yaml_str = execute_kubectl_cmd(cmd, EXIT_CODE_GET_SECRET_FAILED)
        secret = yaml.safe_load(out_yaml_str)
        keys = secret['data'].keys()

    for k in keys:
        k1 = k.replace('.', '\\.')
        cmd = f"{kubectl_cmd} get secret {secret_name} -o jsonpath='{{.data.{k1}}}' | base64 --decode"
        result[k] = execute_kubectl_cmd(cmd, EXIT_CODE_GET_SECRET_FAILED)

    return result

def delete_kubernetes_secret(username: str, namespace: str, k8s_context: str) -> None:
    kubectl_cmd = build_kubectl_cmd(namespace, k8s_context)
    secret_name = build_secret_name(username, namespace)
    cmd = f"{kubectl_cmd} delete secret {secret_name}"
    execute_kubectl_cmd(cmd, EXIT_CODE_DEL_SECRET_FAILED)

def get_management_label(label: bool = True) -> str:
    return 'app.kubernetes.io/managed-by=spark-client' if label else 'app.kubernetes.io/managed-by'

def get_primary_label(label: bool = True) -> str:
    return 'app.kubernetes.io/spark-client-primary=1' if label else 'app.kubernetes.io/spark-client-primary'

def retrieve_k8s_resources_by_label(namespace: str, k8s_context: str) -> Dict:
    kubectl_cmd = build_kubectl_cmd(namespace, k8s_context)
    label = get_management_label()
    conf = dict()

    cmd = f"{kubectl_cmd} get serviceaccount -l {label} -o jsonpath={{.items[0].metadata.name}}"
    conf['spark.kubernetes.authenticate.driver.serviceAccountName'] = execute_kubectl_cmd(cmd, EXIT_CODE_GET_K8S_PROPS_FAILED)

    cmd = f"{kubectl_cmd} get rolebinding -l {label} -o jsonpath={{.items[0].metadata.name}}"
    conf['spark-client.rolebinding'] = execute_kubectl_cmd(cmd, EXIT_CODE_GET_K8S_PROPS_FAILED)

    return conf

def retrieve_primary_service_account_details() -> Dict:
    kubeconfig = get_kube_config()
    kubectl_cmd = get_kubectl_cmd()
    label = get_primary_label()
    cmd = f"{kubectl_cmd} --kubeconfig {kubeconfig}  get serviceaccount -l {label} -A -o yaml"
    out_yaml_str = execute_kubectl_cmd(cmd, EXIT_CODE_GET_PRIMARY_RESOURCES_FAILED)
    out = yaml.safe_load(out_yaml_str)
    result = dict()
    if len(out['items']) > 0:
        result['spark.kubernetes.authenticate.driver.serviceAccountName'] = out['items'][0]['metadata']['name']
        result['spark.kubernetes.namespace'] = out['items'][0]['metadata']['namespace']
    return result

def is_primary_sa_defined() -> bool:
    conf = retrieve_primary_service_account_details()
    return len(conf.keys()) > 0
