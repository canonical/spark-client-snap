#!/usr/bin/env python3

import os
import sys
from typing import List, Dict
import re
import pwd
import subprocess
import logging


USER_HOME_DIR_ENT_IDX = 5
EXIT_CODE_BAD_KUBECONFIG = -100
EXIT_CODE_BAD_CONF_ARG = -200

def generate_spark_default_conf() -> Dict:
    defaults = dict()
    defaults['spark.app.name'] = 'spark-app'
    defaults['spark.executor.instances'] = 2
    defaults['spark.kubernetes.container.image'] = 'docker.io/averma32/sparkpy6:latest'
    defaults['spark.kubernetes.container.image.pullPolicy'] = 'IfNotPresent'
    defaults['spark.kubernetes.namespace'] = 'default'
    defaults['spark.kubernetes.authenticate.driver.serviceAccountName'] = 'spark'
    defaults['spark.eventLog.enabled'] = 'false'
    USER_HOME_DIR = pwd.getpwuid(os.getuid())[USER_HOME_DIR_ENT_IDX]
    SCALA_HIST_FILE_DIR = os.environ.get('SNAP_USER_COMMON', USER_HOME_DIR)
    defaults['spark.driver.extraJavaOptions'] = f'-Dscala.shell.histfile={SCALA_HIST_FILE_DIR}/.scala_history'

    return defaults

def read_spark_defaults_file(spark_defaults_file_name: str) -> Dict :
    defaults = dict()
    with open(spark_defaults_file_name) as f:
        for line in f:
            kv = list(filter(None, re.split('=| ', line)))
            k = kv[0]
            v = '='.join(kv[1:])
            defaults[k] = os.environ.get(v, v)

    return defaults

def write_spark_defaults_file(spark_defaults_target_file_name: str, defaults: Dict) -> None:
    with open(spark_defaults_target_file_name, 'w') as f:
        for k in defaults.keys():
            f.write(f"{k}={defaults[k]}\n")

def override_conf_defaults(defaults: Dict, overrides: Dict) -> Dict:
    #result = defaults | overrides
    #return result
    defaults.update(overrides)
    return defaults

def get_spark_defaults_conf_file() -> None:
    SPARK_HOME = os.environ.get('SPARK_HOME', os.environ.get('SNAP'))
    SPARK_CONF_DIR = os.environ.get('SPARK_CONF_DIR', f"{SPARK_HOME}/conf")
    SPARK_CONF_DEFAULTS_FILE = os.environ.get('SNAP_SPARK_ENV_CONF', f"{SPARK_CONF_DIR}/spark-defaults.conf")
    return SPARK_CONF_DEFAULTS_FILE


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

def reconstruct_submit_args_with_conf_overrides(args: List, conf: Dict) -> List:
    submit_args = args
    conf_arg = ''
    for k in conf.keys():
        conf_arg += f' --conf {k}={conf[k].strip()}'
    submit_args = [conf_arg] + submit_args
    return submit_args

def autodetect_kubernetes_master(conf: Dict) -> str:
    USER_HOME_DIR = pwd.getpwuid(os.getuid())[USER_HOME_DIR_ENT_IDX]
    DEFAULT_KUBECONFIG = f'{USER_HOME_DIR}/.kube/config'
    kubeconfig = os.environ.get('KUBECONFIG') or DEFAULT_KUBECONFIG
    kubectl_cmd = '{}/kubectl'.format(os.environ['SNAP'])
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