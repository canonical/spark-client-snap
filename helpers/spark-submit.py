#!/usr/bin/env python3

import sys
import os
import pwd
import subprocess

if __name__ == "__main__":
    os.environ["HOME"] = pwd.getpwuid(os.getuid())[5]

    if os.environ.get('SPARK_HOME') is None:
        os.environ['SPARK_HOME'] = os.environ['SNAP']

    submit_args = sys.argv[1:]
    if '--master' not in sys.argv:
        default_kubeconfig = '{}/.kube/config'.format(os.environ["HOME"])
        default_kubectl_cmd = '{}/kubectl'.format(os.environ['SNAP'])
        default_master_kubectl_cmd = f"{default_kubectl_cmd} --kubeconfig {default_kubeconfig} config view -o jsonpath=\"{{.clusters[0]['cluster.server']}}\""
        try:
           default_master = subprocess.check_output(default_master_kubectl_cmd, shell=True)
           master_args = ['--master', 'k8s://' + default_master.decode("utf-8")]
           submit_args = master_args + submit_args
        except subprocess.CalledProcessError as e:
           print('ERROR: Cannot determine default kubernetes control plane url. Probably bad or missing kubeconfig file {}'.format(default_kubeconfig))
           sys.exit(-1)

    submit_cmd = '{}/bin/spark-submit'.format(os.environ['SPARK_HOME'])

    submit_cmd += ' ' + ' '.join(submit_args)
    os.system(submit_cmd)