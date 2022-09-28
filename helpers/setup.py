import sys
import os
import yaml

kubectl_cmd='{}/kubectl'.format(os.environ['SNAP'])

def extract_ca_crt_from_kube_config(kubeconfig: str, cluster_name: str = None) -> None:
    with open(kubeconfig) as f:
        kube_cfg = yaml.safe_load(f)
        cluster_names = [n['name'] for n in kube_cfg['clusters']]
        certs = [n['cluster']['certificate-authority-data'] for n in kube_cfg['clusters']]

        if cluster_name:
            try:
                cluster_id = cluster_names.index(cluster_name)
            except ValueError:
                print('Invalid cluster selection, please try again....')
                sys.exit(-100)
        elif len(cluster_names) > 1:
            print ('\n'.join(["{}. {}".format(cluster_names.index(a), a) for a in cluster_names]))
            print('\nPlease select a cluster:')
            cluster_id = input()

            try:
               int(cluster_id)
            except ValueError:
                print('Invalid cluster selection, please try again....')
                sys.exit(-100)

            if int(cluster_id) not in range(len(cluster_names)):
                print('Invalid cluster selection, please try again....')
                sys.exit(-100)
        elif len(cluster_names) == 1:
            cluster_id = 0
        else:
            print('ERROR: No clusters found in kubeconfig file. Please provide a valid kubeconfig file!')
            sys.exit(-100)

        os.system('\n\necho {} | base64 --decode'.format(certs[int(cluster_id)]))


def setup_user(username: str, namespace: str, kubeconfig: str, cluster_name: str) -> None:
    clusterrolebindingname = username + '-role'
    clusterroleaccess='edit'
    os.system("{} create serviceaccount --kubeconfig={} --cluster={} {} --namespace={}".format(kubectl_cmd, kubeconfig, cluster_name, username, namespace))
    os.system("{} create clusterrolebinding --kubeconfig={} --cluster={} {} --clusterrole={}  --serviceaccount={}:{} --namespace={}".format(kubectl_cmd, kubeconfig, cluster_name, clusterrolebindingname, clusterroleaccess, namespace, username, namespace))
	

def dump_ca_crt(secretname: str, kubeconfig: str, cluster_name: str) -> None:
    os.system('{} get secret --kubeconfig={} --cluster={} {} -o jsonpath="{{.data.ca\.crt}}" | base64 --decode'.format(kubectl_cmd,  kubeconfig, cluster_name, secretname))


def dump_token(secretname: str, kubeconfig: str, cluster_name: str) -> None:
    os.system('{} get secret --kubeconfig={} --cluster={} {} -o jsonpath="{{.data.token}}" | base64 --decode'.format(kubectl_cmd,  kubeconfig, cluster_name, secretname))

if __name__ == "__main__":

    if len(sys.argv) == 1:
        print("Usage: setup-spark-k8s service-account | get-ca-cert | get-token --help", file=sys.stderr)
        sys.exit(-1)


    if sys.argv[1] == 'service-account':
        if len(sys.argv) == 2 or sys.argv[2] == '-h' or sys.argv[2] == '--help':
            print("Usage: setup-spark-k8s service-account --kubeconfig kubeconfig-file-name --cluster cluster-name-in-kubeconfig account-name [namespace]", file=sys.stderr)
            sys.exit(-1)

        if len(sys.argv) >= 7:
            if sys.argv[2] == '--kubeconfig' and sys.argv[4] == '--cluster':
                kubeconfig = sys.argv[3]
                cluster_name = sys.argv[5]
            elif sys.argv[2] == '--cluster' and sys.argv[4] == '--kubeconfig':
                cluster_name = sys.argv[3]
                kubeconfig = sys.argv[5]
            else:
                print("ERROR: Invalid Arguments.", file=sys.stderr)
                sys.exit(-2)

            username = sys.argv[6]
            namespace = sys.argv[7] if len(sys.argv) >= 8 else 'default'
        else:
            print("ERROR: Invalid Arguments.", file=sys.stderr)
            sys.exit(-2)

        setup_user(username, namespace, kubeconfig, cluster_name)

    elif sys.argv[1] == 'get-ca-cert':
        if len(sys.argv) == 3 and (sys.argv[2] == '-h' or sys.argv[2] == '--help'):
            print("Usage: setup-spark-k8s get-ca-cert --kubeconfig kubeconfig-file-name --cluster cluster-name-in-kubeconfig > ca.crt", file=sys.stderr)
            sys.exit(-1)

        if len(sys.argv) == 6:
            if sys.argv[2] == '--kubeconfig' and sys.argv[4] == '--cluster':
                kubeconfig = sys.argv[3]
                cluster_name = sys.argv[5]
            elif sys.argv[2] == '--cluster' and sys.argv[4] == '--kubeconfig':
                cluster_name = sys.argv[3]
                kubeconfig = sys.argv[5]
            else:
                print("ERROR: Invalid Arguments.", file=sys.stderr)
                sys.exit(-2)
        else:
            kubeconfig = sys.argv[2] if len(sys.argv) >=3 else '/home/{}/.kube/config'.format(os.getlogin())
            cluster_name = None

        try:
            extract_ca_crt_from_kube_config(kubeconfig, cluster_name)
        except IOError as e:
            print('\nERROR: Bad kubeconfig file. Or default kubeconfig file /home/{}/.kube/config not found.'.format(os.getlogin()))
            print('\n\n')
            print('Looks like kubectl is not setup. Please follow the instructions below to setup kubectl first!')
            print('	1. sudo snap install kubectl --classic')
            print('	2. sudo usermod -a -G microk8s $USER')
            print('	3. mkdir -p ~/.kube')
            print('	4. microk8s config > ~/.kube/config')
            print('	5. sudo chown -f -R $USER ~/.kube')

    elif sys.argv[1] == 'get-token':
        if len(sys.argv) == 2 or sys.argv[2] == '-h' or sys.argv[2] == '--help':
            print("Usage: setup-spark-k8s get-token --kubeconfig kubeconfig-file-name --cluster cluster-name-in-kubeconfig secretname > token\nsecretname is one of the output names of [kubectl get secrets]", file=sys.stderr)
            sys.exit(-1)

        if len(sys.argv) == 7:
            if sys.argv[2] == '--kubeconfig' and sys.argv[4] == '--cluster':
                kubeconfig = sys.argv[3]
                cluster_name = sys.argv[5]
            elif sys.argv[2] == '--cluster' and sys.argv[4] == '--kubeconfig':
                cluster_name = sys.argv[3]
                kubeconfig = sys.argv[5]
            else:
                print("ERROR: Invalid Arguments.", file=sys.stderr)
                sys.exit(-2)

            secretname = sys.argv[6]
        else:
            print("ERROR: Invalid Arguments.", file=sys.stderr)
            sys.exit(-2)
        dump_token(secretname, kubeconfig, cluster_name)

    else:
        print("ERROR: Invalid Arguments.", file=sys.stderr)
        sys.exit(-2)

