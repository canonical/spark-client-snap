#!/usr/bin/env python3

import os
import pwd
import logging
import argparse
import tempfile
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
    ENV_DEFAULTS_CONF_FILE = utils.get_env_defaults_conf_file()

    static_defaults = utils.read_property_file(STATIC_DEFAULTS_CONF_FILE)
    env_defaults = utils.read_property_file(ENV_DEFAULTS_CONF_FILE) if os.path.isfile(ENV_DEFAULTS_CONF_FILE) else dict()
    user_defaults = utils.read_property_file(args.properties_file) if args.properties_file else dict()

    with tempfile.NamedTemporaryFile(mode = 'w', prefix='spark-conf-', suffix='.conf') as t:
        defaults = utils.merge_configurations([static_defaults, env_defaults, user_defaults])

        final_properties_file = f'{utils.get_job_conf_tmp_dir()}{t.name}'
        utils.write_property_file(t.file, defaults, log=True)
        t.flush()

        submit_args = [f'--master {args.master or utils.autodetect_kubernetes_master(defaults)}',
                       f'--deploy-mode {args.deploy_mode}',
                       f'--properties-file {final_properties_file}'] + extra_args

        submit_cmd = '{}/bin/spark-submit'.format(os.environ['SPARK_HOME'])
        submit_cmd += ' ' + ' '.join(submit_args)

        logging.debug(submit_cmd)
        os.system(submit_cmd)