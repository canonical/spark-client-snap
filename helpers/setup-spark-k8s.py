import sys
import os
import yaml
import argparse

kubectl_cmd='{}/kubectl'.format(os.environ['SNAP'])

def print_help_for_missing_or_inaccessible_kubeconfig_file():
    print('\nERROR: Bad kubeconfig file. Or default kubeconfig file /home/{}/.kube/config not found.'.format(os.getlogin()))
    print('\n')
    print('Looks like either kubernetes is not setup properly or default kubeconfig file is not accessible!')
    print('Please take the following remedial actions.')
    print('	1. Please setup kubernetes and make sure kubeconfig file is available, accessible and correct.')
    print('	2. sudo snap connect spark-client:enable-kubeconfig-access')

def extract_default_cluster_from_kubeconfig(kubeconfig: str) -> str:
    with open(kubeconfig) as f:
        kube_cfg = yaml.safe_load(f)
        contexts = [n['name'] for n in kube_cfg['contexts']]
        clusters = [n['context']['cluster'] for n in kube_cfg['contexts']]
        try:
            context_id = contexts.index( kube_cfg['current-context'])
        except ValueError:
            print('Default context invalid or not set in kubeconfig file, please try again.')
            sys.exit(-200)
        return clusters[context_id]

def try_extract_default_cluster_from_kubeconfig(kubeconfig: str) -> str:
    try:
        cluster_name = extract_default_cluster_from_kubeconfig(kubeconfig)
    except IOError as e:
        print_help_for_missing_or_inaccessible_kubeconfig_file()
        sys.exit(-300)
    return cluster_name

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
    clusterroleaccess='view'
    os.system("{} create serviceaccount --kubeconfig={} --cluster={} {} --namespace={}".format(kubectl_cmd, kubeconfig, cluster_name, username, namespace))
    os.system("{} create clusterrolebinding --kubeconfig={} --cluster={} {} --clusterrole={}  --serviceaccount={}:{} --namespace={}".format(kubectl_cmd, kubeconfig, cluster_name, clusterrolebindingname, clusterroleaccess, namespace, username, namespace))
	

def dump_ca_crt(secretname: str, kubeconfig: str, cluster_name: str) -> None:
    os.system('{} get secret --kubeconfig={} --cluster={} {} -o jsonpath="{{.data.ca\.crt}}" | base64 --decode'.format(kubectl_cmd,  kubeconfig, cluster_name, secretname))


def generate_token(serviceaccountname: str, namespace: str, kubeconfig: str, cluster_name: str) -> None:
    token_expiry_duration='24h' # NOTE: The server may return a token with a longer or shorter lifetime.
    os.system('{} create token {} --namespace {} --duration {} --kubeconfig={} --cluster={}'.format(kubectl_cmd, serviceaccountname, namespace, token_expiry_duration, kubeconfig, cluster_name))

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--kubeconfig", default='no-kubeconfig-provided', help='Kubernetes configuration file')
    parser.add_argument("--cluster", default='no-cluster-provided', help='Cluster name to use within the provided kubernetes configuration file')
    subparsers = parser.add_subparsers(dest='action')
    subparsers.required = True

    #  subparser for service-account
    parser_account = subparsers.add_parser('service-account')
    parser_account.add_argument('username', help='Service account username to be created in kubernetes.')
    parser_account.add_argument('--namespace', default='default', help='Namespace for the service account to be created in kubernetes. Default is default namespace')

    #  subparser for CA certificate
    parser_certificate = subparsers.add_parser('get-ca-cert')

    #  subparser for OAuth token
    parser_token = subparsers.add_parser('get-token')
    parser_token.add_argument('serviceaccount', help='Service account name for which the Oauth token is to be fetched.')
    parser_token.add_argument('--namespace', default='default', help='Namespace for the service account for which the Oauth token is to be fetched. Default is default namespace')

    args = parser.parse_args()

    if args.kubeconfig != 'no-kubeconfig-provided':
        kubeconfig = args.kubeconfig
    else:
        kubeconfig = '/home/{}/.kube/config'.format(os.getlogin())

    if args.cluster != 'no-cluster-provided':
        cluster_name = args.cluster
    else:
        cluster_name = try_extract_default_cluster_from_kubeconfig(kubeconfig)

    if args.action == 'service-account':
        username=args.username
        namespace = args.namespace
        # print ('kubeconfig={} cluster={} username={}, namespace={}'.format(kubeconfig, cluster_name, username, namespace))
        setup_user(username, namespace, kubeconfig, cluster_name)
    elif args.action == 'get-ca-cert':
        # print ('kubeconfig={} cluster={}'.format(kubeconfig, cluster_name))
        try:
            extract_ca_crt_from_kube_config(kubeconfig, cluster_name)
        except IOError as e:
            print_help_for_missing_or_inaccessible_kubeconfig_file()
            sys.exit(-400)
    elif args.action == 'get-token':
        serviceaccountname=args.serviceaccount
        namespace = args.namespace
        # print ('kubeconfig={} cluster={} serviceaccount={}, namespace={}'.format(kubeconfig, cluster_name, serviceaccountname, namespace))
        generate_token(serviceaccountname, namespace, kubeconfig, cluster_name)