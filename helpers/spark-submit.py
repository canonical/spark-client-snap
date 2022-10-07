import sys
import os
from typing import List
import subprocess

def expand_arg(arg: str) -> str:
    if os.environ.get(arg):
        return os.environ[arg]
    else:
        return arg

def construct_submit_command(args: List[str]) -> str:
    i = 0
    conf = dict()
    remaining_args = []
    while (i < len(args)):
        if(args[i] == '--master'):
            i += 1
            conf['master'] = expand_arg(args[i])
        elif (args[i] == '--deploy-mode'):
            i += 1
            conf['deploy-mode'] = expand_arg(args[i])
        elif (args[i] == '--name'):
            i += 1
            conf['name'] = expand_arg(args[i])
        elif (args[i] == '--conf'):
            i += 1
            try:
                kv = args[i].split('=')
                conf[kv[0]] = expand_arg(kv[1])
            except IndexError as e:
                print('ERROR: Configuration arguments parsing error. Please check input and try again.')
                sys.exit(-1000)
        else:
            remaining_args.append(args[i])

        i += 1

    if ('master' not in conf.keys()):
        default_kubeconfig = '/home/{}/.kube/config'.format(os.environ['USER'])
        default_kubectl_cmd = '{}/kubectl'.format(os.environ['SNAP'])
        default_master_kubectl_cmd = "{} --kubeconfig {} config view -o jsonpath=\"{{.clusters[0]['cluster.server']}}\"".format(default_kubectl_cmd, default_kubeconfig)
        try:
           default_master = subprocess.check_output(default_master_kubectl_cmd, shell=True)
           conf['master'] = 'k8s://{}'.format(default_master.decode("utf-8"))
        except subprocess.CalledProcessError as e:
           print('ERROR: Cannot determine default kubernetes control plane url. Probably bad or missing kubeconfig file {}'.format(default_kubeconfig))
           sys.exit(-1100)

    if ('deploy-mode' not in conf.keys()):
        conf['deploy-mode'] = 'cluster'

    if ('name' not in conf.keys()):
        conf['name'] = 'canonical-spark-k8s-app'

    if ( ('spark.kubernetes.authenticate.submission.oauthTokenFile' not in conf.keys()) and
         ('spark.kubernetes.authenticate.submission.oauthToken' not in conf.keys()) ):
        conf['spark.kubernetes.authenticate.submission.oauthTokenFile'] = '/home/{}/canonical-spark-token'.format(os.environ['USER'])

    if ('spark.kubernetes.authenticate.submission.caCertFile' not in conf.keys()):
        conf['spark.kubernetes.authenticate.submission.caCertFile'] = '/home/{}/ca.crt'.format(os.environ['USER'])

    if ('spark.executor.instances' not in conf.keys()):
        conf['spark.executor.instances'] = 2

    if ('spark.kubernetes.container.image' not in conf.keys()):
        conf['spark.kubernetes.container.image'] = 'docker.io/averma32/sparkpy6:latest'

    if ('spark.kubernetes.container.image.pullPolicy' not in conf.keys()):
        conf['spark.kubernetes.container.image.pullPolicy'] = 'Always'

    if ('spark.kubernetes.namespace' not in conf.keys()):
        conf['spark.kubernetes.namespace'] = 'default'

    if ('spark.kubernetes.authenticate.driver.serviceAccountName' not in conf.keys()):
        conf['spark.kubernetes.authenticate.driver.serviceAccountName'] = 'spark'

    cmd = '{}/bin/spark-submit'.format(os.environ['SNAP'])

    cmd += ' --master {}'.format(conf['master'])
    del conf['master']

    cmd += ' --deploy-mode {}'.format(conf['deploy-mode'])
    del conf['deploy-mode']

    cmd += ' --name {}'.format(conf['name'])
    del conf['name']

    for k in sorted(conf.keys()):
       cmd += ' --conf {}={}'.format(k, conf[k])

    cmd += ' ' + ' '.join(remaining_args)

    return cmd

if __name__ == "__main__":
    submit_cmd = construct_submit_command(sys.argv[1:])
    print("======================================================")
    print(submit_cmd)
    print("======================================================")
    os.system(submit_cmd)