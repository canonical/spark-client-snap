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

    SPARK_CONF_DEFAULTS_FILE = args.properties_file or utils.get_spark_defaults_conf_file()
    conf_defaults = utils.read_spark_defaults_file(SPARK_CONF_DEFAULTS_FILE)
    conf_overrides = utils.parse_conf_overrides(args.conf)
    conf = utils.override_conf_defaults(conf_defaults, conf_overrides)

    submit_args = [f'--master {args.master or utils.autodetect_kubernetes_master(conf)}',
                   f'--deploy-mode {args.deploy_mode}'] + utils.reconstruct_submit_args_with_conf_overrides(extra_args, conf)

    submit_cmd = '{}/bin/spark-submit'.format(os.environ['SPARK_HOME'])
    submit_cmd += ' ' + ' '.join(submit_args)

    logging.debug(submit_cmd)

    with tempfile.NamedTemporaryFile(mode = 'w', prefix='spark-conf-', suffix='.conf') as t:
        logging.info(f'Spark conf available for reference at /tmp/snap.spark-client{t.name}\n')
        for k in conf.keys():
            v = conf[k]
            t.write(f"{k}={v.strip()}\n")
        t.flush()
        os.system(submit_cmd)