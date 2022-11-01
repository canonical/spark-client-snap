#!/usr/bin/env python3

import os
import pwd
import logging
import argparse
import utils

USER_HOME_DIR_ENT_IDX = 5
EXIT_CODE_BAD_KUBECONFIG = -100
EXIT_CODE_BAD_CONF_ARG = -200

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("--master", default=None, type=str, help='Kubernetes control plane uri.')
    parser.add_argument("--deploy-mode", default="client", type=str, help='Deployment mode for job submission. Default is \'client\'.')
    parser.add_argument("--properties-file", default=None, type=str, help='Spark default configuration properties file.')
    args, extra_args = parser.parse_known_args()

    os.environ["HOME"] = pwd.getpwuid(os.getuid())[USER_HOME_DIR_ENT_IDX]
    if os.environ.get('SPARK_HOME') is None or os.environ.get('SPARK_HOME') == '':
        os.environ['SPARK_HOME'] = os.environ['SNAP']

    STATIC_DEFAULTS_CONF_FILE = utils.get_static_defaults_conf_file()
    DYNAMIC_DEFAULTS_CONF_FILE = utils.get_dynamic_defaults_conf_file()
    ENV_DEFAULTS_CONF_FILE = utils.get_env_defaults_conf_file()

    snap_static_defaults = utils.read_property_file(STATIC_DEFAULTS_CONF_FILE)
    setup_dynamic_defaults = utils.read_property_file(DYNAMIC_DEFAULTS_CONF_FILE) if os.path.isfile(DYNAMIC_DEFAULTS_CONF_FILE) else dict()
    env_defaults = utils.read_property_file(ENV_DEFAULTS_CONF_FILE) if os.path.isfile(ENV_DEFAULTS_CONF_FILE) else dict()
    props_file_arg_defaults = utils.read_property_file(args.properties_file) if args.properties_file else dict()

    with utils.UmaskNamedTemporaryFile(mode = 'w', prefix='spark-conf-', suffix='.conf') as t:
        defaults = utils.merge_configurations([snap_static_defaults, setup_dynamic_defaults, env_defaults, props_file_arg_defaults])
        logging.debug(f'Spark props available for reference at {utils.get_snap_temp_dir()}{t.name}\n')
        utils.write_property_file(t.file, defaults, log=True)
        t.flush()
        submit_args = [f'--master {args.master or utils.autodetect_kubernetes_master(defaults)}',
                       f'--deploy-mode {args.deploy_mode}',
                       f'--properties-file {t.name}'] + extra_args

        SPARK_HOME = os.environ['SPARK_HOME']
        SPARK_SUBMIT_ARGS = ' '.join(submit_args)
        submit_cmd = f'{SPARK_HOME}/bin/spark-submit {SPARK_SUBMIT_ARGS}'
        logging.debug(submit_cmd)
        os.system(submit_cmd)