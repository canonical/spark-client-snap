import sys
import os
import yaml

kubectl_cmd='kubectl'

def extract_ca_crt_from_kube_config(kubeconfig: str) -> None:    
    with open(kubeconfig) as f:
        kube_cfg = yaml.safe_load(f)
        cluster_names = [n['name'] for n in kube_cfg['clusters']]
        print ('\n'.join(["{}. {}".format(cluster_names.index(a), a) for a in cluster_names]))
        print('\nPlease select a cluster to dump the CA certificate:')
        cluster_id = input()

        try:
           int(cluster_id)
        except ValueError:
            print('Invalid cluster selection, please try again....')
            sys.exit(-100)
 
        if int(cluster_id) not in range(len(cluster_names)):
            print('Invalid cluster selection, please try again....')
            sys.exit(-100)
        
        print('CA certificate requested for cluster {}. Correct? [Y or N]'.format(cluster_names[int(cluster_id)]))

        consent = input()
        if consent != 'Y':
           print('ERROR: Apologies for the selection error. Please report the issue.')
           sys.exit(-101)

        certs = [n['cluster']['certificate-authority-data'] for n in kube_cfg['clusters']]
        os.system('\n\necho {} | base64 --decode'.format(certs[int(cluster_id)]))


def setup_user(username: str, namespace: str) -> None:
    clusterrolebindingname = username + '-role'
    clusterroleaccess='view'
    os.system("{} create serviceaccount {} --namespace={}".format(kubectl_cmd, username, namespace))
    os.system("{} create clusterrolebinding {} --clusterrole={}  --serviceaccount={}:{} --namespace={}".format(kubectl_cmd, clusterrolebindingname, clusterroleaccess, namespace, username, namespace))
	

def dump_ca_crt(secretname: str) -> None:
    os.system('{} get secret {} -o jsonpath="{{.data.ca\.crt}}" | base64 --decode'.format(kubectl_cmd, secretname))


def dump_token(secretname: str) -> None:
    os.system('{} get secret {} -o jsonpath="{{.data.token}}" | base64 --decode'.format(kubectl_cmd, secretname))

if __name__ == "__main__":

    if len(sys.argv) == 1:
        print("Usage: setup user|cert|token --help", file=sys.stderr)
        sys.exit(-1)


    if sys.argv[1] == 'user':
        if len(sys.argv) == 2 or sys.argv[2] == '-h' or sys.argv[2] == '--help':
            print("Usage: setup user username [namespace]", file=sys.stderr)
            sys.exit(-1)
        
        setup_user(username=sys.argv[2], namespace=sys.argv[3] if len(sys.argv) >= 4 else 'default')

    elif sys.argv[1] == 'cert':
        if len(sys.argv) == 3 and (sys.argv[2] == '-h' or sys.argv[2] == '--help'):
            print("Usage: setup cert [kubeconfig]", file=sys.stderr)
            sys.exit(-1)

        kubeconfig = sys.argv[2] if len(sys.argv) >=3 else '/home/{}/.kube/config'.format(os.getlogin())

        try:
            extract_ca_crt_from_kube_config(kubeconfig)
        except IOError as e:
            print('\nERROR: No kubeconfig file was provided. And default kubeconfig file /home/{}/.kube/config not found.'.format(os.getlogin()))
            print('\n\n')
            print('Looks like kubeconfig is not setup. Please follow the instructions below to setup kubeconfig first!')
            print('	1. sudo snap install microk8s --classic')
            print('	2. sudo usermod -a -G microk8s $USER')
            print('	3. mkdir -p ~/.kube')
            print('	4. microk8s config > ~/.kube/config')
            print('	5. sudo chown -f -R $USER ~/.kube')

    elif sys.argv[1] == 'token':
        if len(sys.argv) == 2 or sys.argv[2] == '-h' or sys.argv[2] == '--help':
            print("Usage: setup token secretname", file=sys.stderr)
            sys.exit(-1)

        dump_token(secretname=sys.argv[2])

    else:
        print("ERROR: Invalid Arguments.", file=sys.stderr)
        sys.exit(-2)

