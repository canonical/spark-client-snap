#!/usr/bin/env python3

import sys
import os
import pwd
import subprocess
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
    parser.add_argument("--properties-file", default=None, type=str, help='Spark default configuration properties file.')
    parser.add_argument("--name", default="spark-app", type=str, help='Spark application\'s name.')
    parser.add_argument("--deploy-mode", default="client", type=str, help='Deployment mode for job submission. Default is \'client\'.')
    parser.add_argument("--class", default=None, type=str, help='Java class of the application to be launched.')
    parser.add_argument("--conf", action="append", type=str, help='Configuration properties to override the corresponding defaults.')
    parser.add_argument("extra_args", nargs="*")
    args = parser.parse_args()

    os.environ["HOME"] = pwd.getpwuid(os.getuid())[USER_HOME_DIR_ENT_IDX]
    if os.environ.get('SPARK_HOME') is None or os.environ.get('SPARK_HOME') == '':
        os.environ['SPARK_HOME'] = os.environ['SNAP']

    submit_args = sys.argv[1:]

    SPARK_CONF_DEFAULTS_FILE = utils.get_spark_defaults_conf_file()
    conf_defaults = utils.read_spark_defaults_file(SPARK_CONF_DEFAULTS_FILE)
    conf_overrides = dict()
    if args.conf:
        for c in args.conf:
            try:
                kv = c.split('=')
                k = kv[0]
                v = '='.join(kv[1:])
                conf_overrides[k] = os.environ.get(v, v)
            except IndexError as e:
                logging.error('Configuration related arguments parsing error. Please check input arguments and try again.')
                sys.exit(EXIT_CODE_BAD_CONF_ARG)

    conf = utils.override_conf_defaults(conf_defaults, conf_overrides)

    # TBD: Needs discussion
    # submit_args = utils.reconstruct_submit_args(args, conf)

    if not args.master:
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
           master_args = ['--master', 'k8s://' + default_master.decode("utf-8")]
           submit_args = master_args + submit_args
        except subprocess.CalledProcessError as e:
           logging.error(f'Cannot determine default kubernetes control plane url. Probably bad or missing kubeconfig file {kubeconfig}')
           logging.warning(f'Please set the KUBECONFIG environment variable to point to the kubeconfig. Or fix the default kubeconfig {kubeconfig}')
           logging.error(e.output)
           sys.exit(EXIT_CODE_BAD_KUBECONFIG)

    submit_cmd = '{}/bin/spark-submit'.format(os.environ['SPARK_HOME'])

    submit_cmd += ' ' + ' '.join(submit_args)
    os.system(submit_cmd)