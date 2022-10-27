#!/usr/bin/env python3

import os
from typing import List, Dict
import re
import pwd
import argparse

USER_HOME_DIR_ENT_IDX = 5

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
    result = dict()
    for k in defaults.keys():
        result[k] = defaults[k]
    for k in overrides.keys():
        result[k] = overrides[k]
    return result

def get_spark_defaults_conf_file() -> None:
    SPARK_HOME = os.environ.get('SPARK_HOME', os.environ.get('SNAP'))
    SPARK_CONF_DIR = os.environ.get('SPARK_CONF_DIR', f"{SPARK_HOME}/conf")
    SPARK_CONF_DEFAULTS_FILE = os.environ.get('SNAP_SPARK_ENV_CONF', f"{SPARK_CONF_DIR}/spark-defaults.conf")
    return SPARK_CONF_DEFAULTS_FILE

# TBD:
# This needs to be discussed. Expressions like properties-file and deploy-mode and class cannot
# be easily referenced from within arg

def reconstruct_submit_args(args: argparse.Namespace, conf: Dict) -> str:
    submit_args = ''
    submit_args += " --master {}".format(args.master or conf.get('spark.master'))
    submit_args += " --properties-file {}".format(args.propertiesfilearg or get_spark_defaults_conf_file())
    submit_args += " --name {}".format(args.name or conf.get("spark.app.name"))
    submit_args += " --deploy-mode {}".format(args.deploymodearg or conf.get("spark.deploy.mode"))
    submit_args += " --class {}".format(args.classarg)
    submit_args += " --conf {}".format(' --conf '.join(conf.values()))
    submit_args += ' ' + " ".join(args.extra_args)
    return submit_args
