#!/usr/bin/env python3

import sys
import os
import pwd
import subprocess
from typing import List,Dict

USER_HOME_DIR_ENT_IDX = 5

def expand_arg(arg: str) -> str:
    if os.environ.get(arg):
        return os.environ[arg]
    else:
        return arg
def parse_config_args(args: List[str]) -> Dict:
    i = 0
    conf = dict()
    remaining_args = []

    while (i < len(args)):
        if (args[i] == '--master'):
            i += 1
            conf['spark.master'] = expand_arg(args[i])
        elif (args[i] == '--conf'):
            i += 1
            try:
                kv = args[i].split('=')
                conf[kv[0]] = expand_arg(kv[1])
            except IndexError as e:
                print('ERROR: Configuration related arguments parsing error. Please check input aarguments and try again.')
                sys.exit(-2)
        else:
            remaining_args.append(args[i])

        i += 1

    return conf

if __name__ == "__main__":
    os.environ["HOME"] = pwd.getpwuid(os.getuid())[USER_HOME_DIR_ENT_IDX]

    if os.environ.get('SPARK_HOME') is None:
        os.environ['SPARK_HOME'] = os.environ['SNAP']

    submit_args = sys.argv[1:]

    conf = parse_config_args(submit_args)

    if 'spark.master' not in conf.keys():
        DEFAULT_KUBECONFIG = '{}/.kube/config'.format(os.environ["HOME"])
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
           print(f'ERROR: Cannot determine default kubernetes control plane url. Probably bad or missing kubeconfig file {kubeconfig}')
           print(f'Please set the KUBECONFIG environment variable to point to the kubeconfig. Or fix the default kubeconfig {kubeconfig}')
           sys.exit(-1)

    submit_cmd = '{}/bin/spark-submit'.format(os.environ['SPARK_HOME'])

    submit_cmd += ' ' + ' '.join(submit_args)
    os.system(submit_cmd)