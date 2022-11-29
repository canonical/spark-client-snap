#!/usr/bin/env python3

import errno
import io
import logging
import os
import pwd
import re
import subprocess
import sys
from tempfile import NamedTemporaryFile
from typing import Dict, List, Optional, Union

import helpers.constants as constants
import yaml

PathLike = Union[str, "os.PathLike[str]"]


def is_property_with_options(key: str) -> bool:
    """Check if a given property is known to be options-like requiring special parsing.

    Args:
        key: Property for which special options-like parsing decision has to be taken
    """
    return key in [
        constants.OPTION_SPARK_DRIVER_DEFAULT_JAVA_OPTIONS,
        constants.OPTION_SPARK_DRIVER_EXTRA_JAVA_OPTIONS,
        constants.OPTION_SPARK_EXECUTOR_DEFAULT_JAVA_OPTIONS,
        constants.OPTION_SPARK_EXECUTOR_EXTRA_JAVA_OPTIONS,
    ]


def get_properties_with_options(conf: Dict) -> Dict:
    """Extract properties which are known to be options-like requiring special parsing.

    Args:
        conf: All configuration properties as a dict
    """
    result = dict()
    for k in conf.keys():
        if is_property_with_options(k):
            result[k] = conf[k]
    return result


def read_property_file_unsafe(name: str) -> Dict:
    """Read properties in given file into a dictionary.

    Args:
        name: file name to be read
    """
    defaults = dict()
    with open(name) as f:
        for line in f:
            kv = list(filter(None, re.split("=| ", line.strip())))
            k = kv[0].strip()
            if is_property_with_options(k):
                kv2 = line.split("=", 1)
                v = kv2[1].strip()
            else:
                v = kv[1].strip()
            defaults[k] = os.path.expandvars(v)
    return defaults


def read_property_file(name: Optional[str]) -> Dict:
    """Safely read properties in given file into a dictionary.

    Args:
        name: file name to be read safely
    """
    return read_property_file_unsafe(name) if name and os.path.isfile(name) else dict()


def write_property_file(fp: io.TextIOWrapper, props: Dict, log: bool = None) -> None:
    """Write a given dictionary to provided file descriptor.

    Args:
        fp: file pointer to write to
        props: config properties to be written
        log: additionally print to screen
    """
    for k in props.keys():
        v = props[k]
        line = f"{k}={v.strip()}"
        fp.write(line + "\n")
        if log:
            logging.info(line)


def print_properties(props: Dict) -> None:
    """Print a given dictionary to screen."""
    for k in props.keys():
        v = props[k]
        print(f"{k}={v}")


def parse_options(options_string: Optional[str]) -> Dict:
    """Parse options from given string into a dictionary

    Input string would be of the format "-DpropA=A -DpropB=B -DpropC=C"

    Args:
        options_string: options string to parse
    """
    options: Dict[str, str] = dict()

    if not options_string:
        return options

    # cleanup quotes
    line = options_string.strip().replace("'", "").replace('"', "")
    for arg in line.split("-D")[1:]:
        kv = arg.split("=")
        options[kv[0].strip()] = kv[1].strip()

    return options


def construct_options_string(options: Dict) -> str:
    """Construct options string from a given dictionary of options

    Output string would be of the format "-Dk1=v1 -Dk2=v2 -Dk3=v3"

    Args:
        options: options to form the string
    """
    result = ""
    for k in options:
        v = options[k]
        result += f" -D{k}={v}"

    return result


def merge_dictionaries(dictionaries_to_merge: List[Dict]) -> Dict:
    """Merge a given list of dictionaries, properties in subsequent ones override the properties in prior ones in the dictionary list."""
    result = dict()
    for override in dictionaries_to_merge:
        result.update(override)
    return result


def merge_options(dictionaries_to_merge: List[Dict]) -> Dict:
    """Merge a given list of options, options in subsequent ones override the options in prior ones in the list.

    Args:
        dictionaries_to_merge: options to merge
    """
    result: Dict[str, str] = dict()
    for override in dictionaries_to_merge:
        options_override = get_properties_with_options(override)
        for k in options_override:
            options = parse_options(result.get(k))
            options_override = parse_options(options_override.get(k))
            result[k] = construct_options_string(
                merge_dictionaries([options, options_override])
            )
    return result


def merge_configurations(dictionaries_to_merge: List[Dict]) -> Dict:
    """Merge a given list of properties including java type options, properties in subsequent ones override the properties in prior ones in the list.

    Args:
        dictionaries_to_merge: options to merge
    """
    result = merge_dictionaries(dictionaries_to_merge)
    options = merge_options(dictionaries_to_merge)
    return merge_dictionaries([result, options])


def get_static_defaults_conf_file() -> str:
    """Return static config properties file packaged with the client snap."""
    SPARK_STATIC_DEFAULTS_FILE = f"{os.environ.get('SNAP')}/conf/spark-defaults.conf"
    return SPARK_STATIC_DEFAULTS_FILE


def get_dynamic_defaults_conf_file() -> str:
    """Return dynamic config properties file generated during client setup."""
    SPARK_DYNAMIC_DEFAULTS_FILE = (
        f"{os.environ.get('SNAP_USER_DATA')}/spark-defaults.conf"
    )
    return SPARK_DYNAMIC_DEFAULTS_FILE


def get_env_defaults_conf_file() -> Optional[str]:
    """Return env var provided by user to point to the config properties file with conf overrides."""
    SPARK_ENV_DEFAULTS_FILE = os.environ.get("SNAP_SPARK_ENV_CONF")
    return SPARK_ENV_DEFAULTS_FILE


def get_snap_temp_dir() -> str:
    """Return /tmp directory as seen by the snap, for user's reference."""
    return "/tmp/snap.spark-client"


def parse_conf_overrides(conf_args: List) -> Dict:
    """Parse --conf overrides passed to spark-submit

    Args:
        conf_args: list of all --conf 'k1=v1' type args passed to spark-submit. Note v1 expression itself could be containing '='
    """
    conf_overrides = dict()
    if conf_args:
        for c in conf_args:
            try:
                kv = c.split("=")
                k = kv[0].strip()
                if is_property_with_options(k):
                    kv2 = c.split("=", 1)
                    v = kv2[1].strip()
                else:
                    v = kv[1].strip()
                conf_overrides[k] = os.path.expandvars(v)
            except IndexError:
                logging.error(
                    "Configuration related arguments parsing error. Please check input arguments and try again."
                )
                sys.exit(constants.EXIT_CODE_BAD_CONF_ARG)
    return conf_overrides


def reconstruct_submit_args(args: List, conf: Dict) -> List:
    """Add back possibly overridden config properties to list of other spark-submit arguments

    Args:
        args: regular args passed to spark-submit
        conf: dictionary of all additional config (possible after overrides) to be passed to spark-submit.
    """
    submit_args = args
    conf_arg = ""
    for k in conf.keys():
        conf_arg += f" --conf {k}={conf[k].strip()}"
    submit_args = [conf_arg] + submit_args
    return submit_args


def get_kube_config() -> str:
    """Return default kubeconfig to use if not explicitly provided."""
    USER_HOME_DIR = pwd.getpwuid(os.getuid())[constants.USER_HOME_DIR_ENT_IDX]
    DEFAULT_KUBECONFIG = f"{USER_HOME_DIR}/.kube/config"
    kubeconfig = os.environ.get("KUBECONFIG") or DEFAULT_KUBECONFIG
    return kubeconfig


def get_kubectl_cmd() -> str:
    """Return the kubectl binary location within the snap, used to build k8s commands."""
    kubectl_cmd = "{}/kubectl".format(os.environ["SNAP"])
    return kubectl_cmd


def autodetect_kubernetes_master(conf: Dict) -> str:
    """Return a kubernetes master for use with spark-submit in case not provided.

    Args:
        config: dictionary of all config available to spark-submit.
    """
    kubeconfig = get_kube_config()
    namespace = conf.get("spark.kubernetes.namespace")
    context = conf.get("spark.kubernetes.context")
    primary_sa = retrieve_primary_service_account_details(
        namespace, kubeconfig, context
    )
    primary_namespace = primary_sa.get("spark.kubernetes.namespace") or "default"
    kubectl_cmd = build_kubectl_cmd(kubeconfig, primary_namespace, context)
    master_cmd = f"{kubectl_cmd} config view --minify -o jsonpath=\"{{.clusters[0]['cluster.server']}}\""
    default_master = execute_kubectl_cmd(master_cmd, constants.EXIT_CODE_BAD_KUBECONFIG)
    return f"k8s://{default_master}"


def UmaskNamedTemporaryFile(*args, **kargs):
    """Return a temporary file descriptor readable by all users."""
    fdesc = NamedTemporaryFile(*args, **kargs)
    umask = os.umask(0o666)
    os.umask(umask)
    os.chmod(fdesc.name, 0o666 & ~umask)
    return fdesc


def build_kubectl_cmd(
    kube_config: Optional[str], namespace: Optional[str], k8s_context: Optional[str]
) -> str:
    """Return a kubectl based command prefix to be used to construct various commands to run.

    Args:
        kube_config: config to be used for kubernetes
        namespace: namespace for which kubectl command will run
        k8s_context: kubernetes context of choice
    """
    kubeconfig = kube_config or get_kube_config()
    kubectl_cmd = get_kubectl_cmd()
    cmd = f"{kubectl_cmd} --kubeconfig {kubeconfig}"
    if namespace:
        cmd += f" --namespace {namespace}"
    if k8s_context:
        cmd += f" --context {k8s_context}"
    return cmd


def build_secret_name(username: str) -> str:
    """Return the secret name associated with a service account associated with the provided username.

    Args:
        username: username to indicate the service account for which secret name has to be returned
    """
    return f"spark-client-sa-conf-{username or 'spark'}"


def execute_kubectl_cmd(
    cmd: str, exit_code_on_error: int, log_on_error: bool = True
) -> Optional[str]:
    """Execute provided kubectl command

    Args:
        cmd: Command to execute
        exit_code_on_error: On error, sys.exit() called with this code.
        log_on_error: boolean can be turned off for silent behavior i.e. no logging on error
    """
    logging.debug(cmd)
    # kubeconfig = get_kube_config()
    result = None
    try:
        out = subprocess.check_output(cmd, shell=True)
        result = out.decode("utf-8") if out else None
    except subprocess.CalledProcessError as e:
        if log_on_error:
            logging.error(e.output)
        sys.exit(exit_code_on_error)

    return result


def setup_kubernetes_secret(
    username: str,
    namespace: str,
    kubeconfig: str,
    k8s_context: str,
    properties_file: str,
    conf: List[str],
) -> None:
    """Store/set up properties against a service account (as secrets)

    Args:
        username: username corresponding to the service account for which config properties are to be stored
        name_space: namespace of the provided username.
        kube_config: config for kubectl command execution pointing to the right k8s cluster
        k8s_context: context of user's choice from within the provided kubeconfig
        properties_file: file to pick up config properties from
        conf: list of additional config properties to add/override ones in properties file provided
    """
    kubectl_cmd = build_kubectl_cmd(kubeconfig, namespace, k8s_context)
    secret_name = build_secret_name(username)
    props_from_file = read_property_file(properties_file)
    props_from_conf = parse_conf_overrides(conf)
    props = merge_configurations([props_from_file, props_from_conf])
    with UmaskNamedTemporaryFile(
        mode="w", prefix="spark-dynamic-conf-k8s-", suffix=".conf"
    ) as t:
        logging.debug(
            f"Spark dynamic props available for reference at {get_snap_temp_dir()}{t.name}\n"
        )
        write_property_file(t.file, props)
        t.flush()
        cmd = f"{kubectl_cmd} create secret generic {secret_name} --from-env-file={t.name}"
        logging.debug(cmd)
        execute_kubectl_cmd(cmd, constants.EXIT_CODE_PUT_SECRET_ENV_FILE_FAILED)


def retrieve_kubernetes_secret(
    username: Optional[str],
    namespace: Optional[str],
    kubeconfig: Optional[str],
    k8s_context: Optional[str],
    keys: Optional[List[str]],
) -> Dict:
    """Retrieve the decoded config properties stored against a service account (as secrets)

    Args:
        username: username corresponding to the service account for which config properties are to be retrieved
        namespace: namespace of the provided username.
        kubeconfig: config for kubectl command execution pointing to the right k8s cluster
        k8s_context: context of user's choice from within the provided kubeconfig
        keys: list of specific keys for which this operation is requested. If not available, all config properties retrieved
    """
    if not username:
        return dict()

    kubectl_cmd = build_kubectl_cmd(kubeconfig, namespace, k8s_context)
    secret_name = build_secret_name(username)
    result = dict()

    if keys is None:
        cmd = f"{kubectl_cmd} get secret {secret_name} -o yaml"
        out_yaml_str = execute_kubectl_cmd(cmd, constants.EXIT_CODE_GET_SECRET_FAILED)
        if out_yaml_str is None:
            raise ValueError("could not get the secret")
        secret = yaml.safe_load(out_yaml_str)
        keys = secret["data"].keys() if secret.get("data") else []

    for k in keys:
        k1 = k.replace(".", "\\.")
        cmd = f"{kubectl_cmd} get secret {secret_name} -o jsonpath='{{.data.{k1}}}' | base64 --decode"
        result[k] = execute_kubectl_cmd(cmd, constants.EXIT_CODE_GET_SECRET_FAILED)

    return result


def delete_kubernetes_secret(
    username: str, namespace: str, kubeconfig: str, k8s_context: str
) -> None:
    """Delete the config properties stored against a service account (as secrets)

    Args:
        username: username corresponding to the service account for which config properties are to be deleted
        name_space: namespace of the provided username.
        kube_config: config for kubectl command execution pointing to the right k8s cluster
        k8s_context: context of user's choice from within the provided kubeconfig
    """
    kubectl_cmd = build_kubectl_cmd(kubeconfig, namespace, k8s_context)
    secret_name = build_secret_name(username)
    cmd = f"{kubectl_cmd} delete secret {secret_name}"
    execute_kubectl_cmd(cmd, constants.EXIT_CODE_DEL_SECRET_FAILED, log_on_error=False)


def get_management_label(label: bool = True) -> str:
    """Return uber spark-client management label

    Args:
        label: bool to be turned off to retrieve the label fragment for unlabel command
    """
    return (
        "app.kubernetes.io/managed-by=spark-client"
        if label
        else "app.kubernetes.io/managed-by"
    )


def get_primary_label(label: bool = True) -> str:
    """Return label used to mark the primary service account.

    Args:
        label: bool to be turned off to retrieve the label fragment for unlabel command
    """
    return (
        "app.kubernetes.io/spark-client-primary=1"
        if label
        else "app.kubernetes.io/spark-client-primary"
    )


def retrieve_primary_service_account_details(
    namespace: Optional[str], kubeconfig: Optional[str], k8s_context: Optional[str]
) -> Dict:
    """Retrieve primary service account details.

    Args:
        namespace: namespace to point to the service account
        kubeconfig: kubernetes config for kubectl command
        k8s_context: kubernetes context to be used
    """
    kubectl_cmd = build_kubectl_cmd(kubeconfig, namespace, k8s_context)
    label = get_primary_label()
    cmd = f"{kubectl_cmd}  get serviceaccount -l {label} -A -o yaml"
    out_yaml_str = execute_kubectl_cmd(
        cmd, constants.EXIT_CODE_GET_PRIMARY_RESOURCES_FAILED
    )
    if out_yaml_str is None:
        raise ValueError("could not get the secret")
    out = yaml.safe_load(out_yaml_str)
    result = dict()
    if len(out["items"]) > 0:
        result["spark.kubernetes.authenticate.driver.serviceAccountName"] = out[
            "items"
        ][0]["metadata"]["name"]
        result["spark.kubernetes.namespace"] = out["items"][0]["metadata"]["namespace"]
    return result


def is_primary_sa_defined(namespace: str, kubeconfig: str, k8s_context: str) -> bool:
    """Check if a primary service account has been defined.

    Args:
        user_name: username to point to the service account
        kubeconfig: kubernetes config for kubectl command
        k8s_context: kubernetes context to be used
    """
    conf = retrieve_primary_service_account_details(namespace, kubeconfig, k8s_context)
    return len(conf.keys()) > 0


def get_dynamic_defaults(user_name: str, name_space: str) -> Dict:
    """Get setup scripts generated config values overridden with config properties kept in the service account.

    Args:
        user_name: username to point to the service account and it's secret config properties
        name_space: namespace of the username provided
    """
    kubeconfig = get_kube_config()
    setup_dynamic_defaults = retrieve_primary_service_account_details(
        None, kubeconfig, None
    )
    username = user_name or setup_dynamic_defaults.get(
        "spark.kubernetes.authenticate.driver.serviceAccountName"
    )
    namespace = name_space or setup_dynamic_defaults.get("spark.kubernetes.namespace")
    logging.debug(f"Dynamic defaults conf: username={username}")
    logging.debug(f"Dynamic defaults conf: namespace={namespace}")
    setup_dynamic_defaults_conf = retrieve_kubernetes_secret(
        username, namespace, kubeconfig, None, None
    )
    return merge_configurations([setup_dynamic_defaults, setup_dynamic_defaults_conf])


def print_help_for_missing_or_inaccessible_kubeconfig_file(kubeconfig: str) -> None:
    """Print error message for the user indicating expected kubeconfig is missing or inaccessible.

    Args:
        kubeconfig: config for kubectl command execution pointing to the right k8s cluster
    """
    print(
        "\nERROR: Missing kubeconfig file {}. Or default kubeconfig file {}/.kube/config not found.".format(
            kubeconfig, pwd.getpwuid(os.getuid())[5]
        )
    )
    print("\n")
    print(
        "Looks like either kubernetes is not set up properly or default kubeconfig file is not accessible!"
    )
    print("Please take the following remedial actions.")
    print(
        "	1. Please set up kubernetes and make sure kubeconfig file is available, accessible and correct."
    )
    print("	2. sudo snap connect spark-client:dot-kube-config")


def print_help_for_bad_kubeconfig_file(kubeconfig: str) -> None:
    """Print error message for the user indicating kubeconfig provided might be corrupted.

    Args:
        kubeconfig: config for kubectl command execution pointing to the right k8s cluster
    """
    print(
        "\nERROR: Invalid or incomplete kubeconfig file {}. One or more of the following entries might be missing or invalid.\n".format(
            kubeconfig
        )
    )
    print("	- current-context")
    print("	- context.name")
    print("	- context.namespace")
    print("	- context.cluster")
    print("	- cluster.name")
    print("	- cluster.server")
    print(" - cluster.certificate-authority-data")
    print("Please take the following remedial actions.")
    print(
        "	1. Please set up kubernetes and make sure kubeconfig file is available, accessible and correct."
    )
    print("	2. sudo snap connect spark-client:dot-kube-config")


def select_context_id(kube_cfg: Dict) -> int:
    """Interact with user to select a context from the kube config provided.

    Args:
        kube_cfg: config for kubectl command execution pointing to the right k8s cluster
    """
    NO_CONTEXT = -1
    SINGLE_CONTEXT = 0
    context_names = [n["name"] for n in kube_cfg["contexts"]]

    selected_context_id = NO_CONTEXT
    if len(context_names) == 1:
        return SINGLE_CONTEXT

    context_list_ux = "\n".join(
        ["{}. {}".format(context_names.index(a), a) for a in context_names]
    )
    while selected_context_id == NO_CONTEXT:
        print(context_list_ux)
        print("\nPlease select a kubernetes context by index:")

        try:
            selected_context_id = int(input())
        except ValueError:
            print("Invalid context index selection, please try again....")
            selected_context_id = NO_CONTEXT
            continue

        if selected_context_id not in range(len(context_names)):
            print("Invalid context index selection, please try again....")
            selected_context_id = NO_CONTEXT
            continue

    return selected_context_id


def get_defaults_from_kubeconfig(kube_config: str, context: str = None) -> Dict:
    """Get config defaults from kubernetes config and context.

    Args:
        kube_config: config for kubectl command execution pointing to the right k8s cluster
        k8s_context: context of user's choice from within the provided kubeconfig
    """
    USER_HOME_DIR = pwd.getpwuid(os.getuid())[constants.USER_HOME_DIR_ENT_IDX]
    DEFAULT_KUBECONFIG = f"{USER_HOME_DIR}/.kube/config"
    kubeconfig = kube_config or DEFAULT_KUBECONFIG
    try:
        with open(kubeconfig) as f:
            kube_cfg = yaml.safe_load(f)
            context_names = [n["name"] for n in kube_cfg["contexts"]]
            certs = [
                n["cluster"]["certificate-authority-data"] for n in kube_cfg["clusters"]
            ]
            current_context = context or kube_cfg["current-context"]
    except IOError:
        print_help_for_missing_or_inaccessible_kubeconfig_file(kubeconfig)
        sys.exit(-1)
    except KeyError:
        print_help_for_bad_kubeconfig_file(kubeconfig)
        sys.exit(-2)

    try:
        context_id = context_names.index(current_context)
    except ValueError:
        print(
            f"WARNING: Current context in provided kubeconfig file {kubeconfig} is invalid!"
        )
        print("\nProceeding with explicit context selection....")
        context_id = select_context_id(kube_cfg)

    defaults = {}
    defaults["context"] = context_names[context_id]
    defaults["namespace"] = "default"
    defaults["cert"] = certs[context_id]
    defaults["config"] = kubeconfig
    defaults["user"] = "spark"

    return defaults


def set_up_user(
    username: str,
    name_space: str,
    kube_config: str,
    k8s_context: str,
    defaults: Dict,
    mark_primary: bool,
) -> None:
    """Set up all resources related to a service account.

    Args:
        username: username corresponding to the service account to be set up.
        name_space: namespace of the provided username.
        kube_config: config for kubectl command execution pointing to the right k8s cluster
        k8s_context: context of user's choice from within the provided kubeconfig
        defaults: config to fallback on in case any parameters not supplied
        mark_primary: boolean to indicate if this service account needs to be marked primary
    """
    namespace = name_space or defaults["namespace"]
    kubeconfig = kube_config or defaults["config"]
    context_name = k8s_context or defaults["context"]
    kubectl_cmd = build_kubectl_cmd(kubeconfig, namespace, context_name)

    rolebindingname = username + "-role"
    roleaccess = "view"
    label = get_management_label()

    os.system(f"{kubectl_cmd} create serviceaccount {username}")
    os.system(
        f"{kubectl_cmd} create rolebinding {rolebindingname} --role={roleaccess} --serviceaccount={namespace}:{username}"
    )

    primary_label_to_remove = get_primary_label(label=False)
    primary_label_full = get_primary_label()

    primary = retrieve_primary_service_account_details(
        namespace, kubeconfig, context_name
    )
    is_primary_defined = len(primary.keys()) > 0

    logging.debug(f"is_primary_defined={is_primary_defined}")
    logging.debug(f"mark_primary={mark_primary}")

    if is_primary_defined and mark_primary:
        sa_to_unlabel = primary[
            "spark.kubernetes.authenticate.driver.serviceAccountName"
        ]
        namespace_of_sa_to_unlabel = primary["spark.kubernetes.namespace"]
        rolebindingname_to_unlabel = sa_to_unlabel + "-role"
        kubectl_cmd_unlabel = build_kubectl_cmd(
            kubeconfig, namespace_of_sa_to_unlabel, context_name
        )

        os.system(
            f"{kubectl_cmd_unlabel} label serviceaccount --namespace={namespace_of_sa_to_unlabel} {sa_to_unlabel} {primary_label_to_remove}-"
        )
        os.system(
            f"{kubectl_cmd_unlabel} label rolebinding --namespace={namespace_of_sa_to_unlabel} {rolebindingname_to_unlabel} {primary_label_to_remove}-"
        )

        os.system(
            f"{kubectl_cmd} label serviceaccount {username} {label} {primary_label_full}"
        )
        os.system(
            f"{kubectl_cmd} label rolebinding {rolebindingname} {label} {primary_label_full}"
        )
    elif is_primary_defined and not mark_primary:
        os.system(f"{kubectl_cmd} label serviceaccount {username} {label}")
        os.system(f"{kubectl_cmd} label rolebinding {rolebindingname} {label}")
    elif not is_primary_defined:
        os.system(
            f"{kubectl_cmd} label serviceaccount {username} {label} {primary_label_full}"
        )
        os.system(
            f"{kubectl_cmd} label rolebinding {rolebindingname} {label} {primary_label_full}"
        )
    else:
        logging.warning("Labeling logic issue.....")


def cleanup_user(
    username: str, namespace: str, kubeconfig: str, k8s_context: str
) -> None:
    """Clean up all resources related to a service account.

    Args:
        username: username corresponding to the service account to be cleaned up.
        namespace: namespace of the provided username.
        kubeconfig: config for kubectl command execution pointing to the right k8s cluster
        k8s_context: context of user's choice from within the provided kubeconfig
    """
    kubectl_cmd = build_kubectl_cmd(kubeconfig, namespace, k8s_context)
    rolebindingname = username + "-role"

    os.system(f"{kubectl_cmd} delete serviceaccount {username}")
    os.system(f"{kubectl_cmd} delete rolebinding {rolebindingname}")
    delete_kubernetes_secret(username, namespace, kubeconfig, k8s_context)


def mkdir(path: PathLike) -> None:
    """
    Create a dir, using a formulation consistent between 2.x and 3.x python versions.
    :param path: path to create
    :raises OSError: whenever OSError is raised by makedirs and it's not because the directory exists
    """
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def create_dir_if_not_exists(directory: PathLike) -> PathLike:
    """
    Create a directory if it does not exist.
    :param directory: path
    :return: directory, str
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory


def get_scala_shell_history_file() -> str:
    """Return the location of .scala_history file for spark-shell"""
    USER_HOME_DIR = pwd.getpwuid(os.getuid())[constants.USER_HOME_DIR_ENT_IDX]
    SCALA_HIST_FILE_DIR = os.environ.get("SNAP_USER_DATA", USER_HOME_DIR)
    return f"{SCALA_HIST_FILE_DIR}/.scala_history"
