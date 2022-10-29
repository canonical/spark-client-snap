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
    parser.add_argument("--conf", action="append", type=str, help='Configuration properties to override the corresponding defaults.')
    args, extra_args = parser.parse_known_args()

    os.environ["HOME"] = pwd.getpwuid(os.getuid())[USER_HOME_DIR_ENT_IDX]
    if os.environ.get('SPARK_HOME') is None or os.environ.get('SPARK_HOME') == '':
        os.environ['SPARK_HOME'] = os.environ['SNAP']

    STATIC_DEFAULTS_CONF_FILE = utils.get_static_defaults_conf_file()
    DYNAMIC_DEFAULTS_CONF_FILE = utils.get_dynamic_defaults_conf_file()

    static_defaults = utils.read_property_file(STATIC_DEFAULTS_CONF_FILE)
    dynamic_defaults = utils.read_property_file(DYNAMIC_DEFAULTS_CONF_FILE) if os.path.isfile(DYNAMIC_DEFAULTS_CONF_FILE) else dict()
    user_defaults = utils.read_property_file(args.properties_file) if args.properties_file else dict()
    user_overrides = utils.parse_conf_overrides(args.conf) if args.conf else dict()

    conf = utils.merge_configurations([static_defaults, dynamic_defaults, user_defaults, user_overrides])

    submit_args = [f'--master {args.master or utils.autodetect_kubernetes_master(conf)}',
                   f'--deploy-mode {args.deploy_mode}'] + utils.reconstruct_submit_args(extra_args, conf)

    submit_cmd = '{}/bin/spark-submit'.format(os.environ['SPARK_HOME'])
    submit_cmd += ' ' + ' '.join(submit_args)

    logging.debug(submit_cmd)

    with tempfile.NamedTemporaryFile(mode = 'w', prefix='spark-conf-', suffix='.conf') as t:
        logging.info(f'Spark props available for reference at {utils.get_job_conf_tmp_dir()}{t.name}\n')
        utils.write_property_file(t.file, conf)
        t.flush()
        os.system(submit_cmd)