#!/usr/bin/env python3

import sys
import os
import yaml
import argparse
import pwd

kubectl_cmd='{}/kubectl'.format(os.environ['SNAP'])

def print_help_for_missing_or_inaccessible_kubeconfig_file():
    print('\nERROR: Bad kubeconfig file. Or default kubeconfig file {}/.kube/config not found.'.format(pwd.getpwuid(os.getuid())[5]))
    print('\n')
    print('Looks like either kubernetes is not setup properly or default kubeconfig file is not accessible!')
    print('Please take the following remedial actions.')
    print('	1. Please setup kubernetes and make sure kubeconfig file is available, accessible and correct.')
    print('	2. sudo snap connect spark-client:enable-kubeconfig-access')

def extract_default_context_from_kubeconfig(kubeconfig: str) -> str:
    with open(kubeconfig) as f:
        kube_cfg = yaml.safe_load(f)
        return kube_cfg['current-context']

def try_extract_default_context_from_kubeconfig(kubeconfig: str) -> str:
    try:
        context_name = extract_default_context_from_kubeconfig(kubeconfig)
    except IOError as e:
        print_help_for_missing_or_inaccessible_kubeconfig_file()
        sys.exit(-300)
    return context_name


def extract_default_namespace_from_kube_config(kubeconfig: str) -> None:
    default_namespace = 'default'
    with open(kubeconfig) as f:
        kube_cfg = yaml.safe_load(f)
        context_names = [n['name'] for n in kube_cfg['contexts']]
        try:
            namespaces = [n['context']['namespace'] for n in kube_cfg['contexts']]
        except KeyError:
            return default_namespace

        if len(context_names) > 1:
            try:
                context_id = context_names.index(kube_cfg['current-context'])
            except ValueError:
                return default_namespace
        elif len(context_names) == 1:
            context_id = 0
        else:
            return default_namespace

        return namespaces[int(context_id)]

def try_extract_default_namespace_from_kube_config(kubeconfig: str) -> str:
    try:
        namespace = extract_default_namespace_from_kube_config(kubeconfig)
    except IOError as e:
        return 'default'

    return namespace

def extract_ca_crt_from_kube_config(kubeconfig: str, context_name: str = None) -> None:
    with open(kubeconfig) as f:
        kube_cfg = yaml.safe_load(f)
        context_names = [n['name'] for n in kube_cfg['contexts']]
        cluster_names = [n['name'] for n in kube_cfg['clusters']]
        certs = [n['cluster']['certificate-authority-data'] for n in kube_cfg['clusters']]

        if context_name:
            try:
                context_id = context_names.index(context_name)
            except ValueError:
                print('Invalid context selection, please try again....')
                sys.exit(-100)
        elif len(context_names) > 1:
            print ('\n'.join(["{}. {}".format(context_names.index(a), a) for a in context_names]))
            print('\nPlease select a context id:')
            context_id = input()

            try:
               int(context_id)
            except ValueError:
                print('Invalid context selection, please try again....')
                sys.exit(-100)

            if int(context_id) not in range(len(context_names)):
                print('Invalid cluster selection, please try again....')
                sys.exit(-100)
        elif len(context_names) == 1:
            context_id = 0
        else:
            print('ERROR: No contexts found in kubeconfig file. Please provide a valid kubeconfig file!')
            sys.exit(-100)

        os.system(f'\n\necho {certs[int(context_id)]} | base64 --decode')


def setup_user(username: str, namespace: str, kubeconfig: str, context_name: str) -> None:
    #clusterrolebindingname = username + '-role'
    #clusterroleaccess='view'
    rolebindingname = username + '-role'
    roleaccess='view'
    os.system(f"{kubectl_cmd} create serviceaccount --kubeconfig={kubeconfig} --context={context_name} {username} --namespace={namespace}")
    #os.system(f"{kubectl_cmd} create clusterrolebinding --kubeconfig={kubeconfig} --context={context_name} {clusterrolebindingname} --clusterrole={clusterroleaccess}  --serviceaccount={namespace}:{username} --namespace={namespace}")
    os.system(f"{kubectl_cmd} create rolebinding --kubeconfig={kubeconfig} --context={context_name} {rolebindingname} --clusterrole={roleaccess}  --serviceaccount={namespace}:{username} --namespace={namespace}")

def generate_token(serviceaccountname: str, namespace: str, kubeconfig: str, context_name: str) -> None:
    os.system(f'{kubectl_cmd} create token {serviceaccountname} --namespace {namespace} --kubeconfig={kubeconfig} --context={context_name}')

if __name__ == "__main__":

    default_kubeconfig = '{}/.kube/config'.format(pwd.getpwuid(os.getuid())[5])
    default_namespace = try_extract_default_namespace_from_kube_config(default_kubeconfig)

    parser = argparse.ArgumentParser()
    parser.add_argument("--kubeconfig", default=None, help='Kubernetes configuration file')
    parser.add_argument("--context", default=None, help='Context name to use within the provided kubernetes configuration file')
    subparsers = parser.add_subparsers(dest='action')
    subparsers.required = True

    #  subparser for service-account
    parser_account = subparsers.add_parser('service-account')
    parser_account.add_argument('--username', default='spark', help='Service account username to be created in kubernetes. Default is spark')
    parser_account.add_argument('--namespace', default=default_namespace, help='Namespace for the service account to be created in kubernetes. Default is default namespace')

    #  subparser for CA certificate
    parser_certificate = subparsers.add_parser('get-ca-cert')

    #  subparser for OAuth token
    parser_token = subparsers.add_parser('get-token')
    parser_token.add_argument('--serviceaccount', default='spark', help='Service account name for which the Oauth token is to be fetched. Default is spark account.')
    parser_token.add_argument('--namespace', default=default_namespace, help='Namespace for the service account for which the Oauth token is to be fetched. Default is default namespace')

    args = parser.parse_args()

    if args.kubeconfig is not None:
        kubeconfig = args.kubeconfig
    else:
        kubeconfig = default_kubeconfig

    if args.context is not None:
        context_name = args.context
    else:
        context_name = try_extract_default_context_from_kubeconfig(kubeconfig)

    if args.action == 'service-account':
        username=args.username
        namespace = args.namespace
        # print ('kubeconfig={} context={} username={}, namespace={}'.format(kubeconfig, context_name, username, namespace))
        setup_user(username, namespace, kubeconfig, context_name)
    elif args.action == 'get-ca-cert':
        # print ('kubeconfig={} context={}'.format(kubeconfig, context_name))
        try:
            extract_ca_crt_from_kube_config(kubeconfig, context_name)
        except IOError as e:
            print_help_for_missing_or_inaccessible_kubeconfig_file()
            sys.exit(-400)
    elif args.action == 'get-token':
        serviceaccountname=args.serviceaccount
        namespace = args.namespace
        # print ('kubeconfig={} context={} serviceaccount={}, namespace={}'.format(kubeconfig, context_name, serviceaccountname, namespace))
        generate_token(serviceaccountname, namespace, kubeconfig, context_name)