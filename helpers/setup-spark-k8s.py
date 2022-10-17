#!/usr/bin/env python3

import sys
import os
import yaml
import argparse
import pwd
from typing import Dict

KUBECTL_CMD= '{}/kubectl'.format(os.environ['SNAP'])
USER_HOME_DIR_ENT_IDX = 5

def print_help_for_missing_or_inaccessible_kubeconfig_file(kubeconfig: str):
    print('\nERROR: Missing kubeconfig file {}. Or default kubeconfig file {}/.kube/config not found.'.format(kubeconfig, pwd.getpwuid(os.getuid())[5]))
    print('\n')
    print('Looks like either kubernetes is not set up properly or default kubeconfig file is not accessible!')
    print('Please take the following remedial actions.')
    print('	1. Please set up kubernetes and make sure kubeconfig file is available, accessible and correct.')
    print('	2. sudo snap connect spark-client:enable-kubeconfig-access')

def print_help_for_bad_kubeconfig_file(kubeconfig: str):
    print('\nERROR: Invalid or incomplete kubeconfig file {}. One or more of the following entries might be missing or invalid.\n'.format(kubeconfig))
    print('	- current-context')
    print('	- context.name')
    print('	- context.namespace')
    print('	- context.cluster')
    print('	- cluster.name')
    print('	- cluster.server')
    print(' - cluster.certificate-authority-data')
    print('Please take the following remedial actions.')
    print('	1. Please set up kubernetes and make sure kubeconfig file is available, accessible and correct.')
    print('	2. sudo snap connect spark-client:enable-kubeconfig-access')

def select_context_id(kube_cfg: Dict) -> int:
    NO_CONTEXT = -1
    SINGLE_CONTEXT = 0
    context_names = [n['name'] for n in kube_cfg['contexts']]

    selected_context_id = NO_CONTEXT
    if len(context_names) == 1:
        return SINGLE_CONTEXT

    context_list_ux = '\n'.join(["{}. {}".format(context_names.index(a), a) for a in context_names])
    while selected_context_id == NO_CONTEXT:
        print (context_list_ux)
        print('\nPlease select a kubernetes context by index:')
        selected_context_id = input()

        try:
           int(selected_context_id)
        except ValueError:
            print('Invalid context index selection, please try again....')
            selected_context_id = NO_CONTEXT
            continue

        if int(selected_context_id) not in range(len(context_names)):
            print('Invalid context index selection, please try again....')
            selected_context_id = NO_CONTEXT
            continue

    return int(selected_context_id)

def get_defaults_from_kubeconfig(kubeconfig: str, context: str = None) -> Dict:
    try:
        with open(kubeconfig) as f:
            kube_cfg = yaml.safe_load(f)
            context_names = [n['name'] for n in kube_cfg['contexts']]
            # namespaces = [n['context']['namespace'] for n in kube_cfg['contexts']]
            certs = [n['cluster']['certificate-authority-data'] for n in kube_cfg['clusters']]
            current_context = context or kube_cfg['current-context']
    except IOError as ioe:
        print_help_for_missing_or_inaccessible_kubeconfig_file(kubeconfig)
        sys.exit(-1)
    except KeyError as ke:
        print_help_for_bad_kubeconfig_file(kubeconfig)
        sys.exit(-2)

    try:
        context_id = context_names.index(current_context)
    except ValueError:
        print(f'WARNING: Current context in provided kubeconfig file {kubeconfig} is invalid!')
        print(f'\nProceeding with explicit context selection....')
        context_id = select_context_id(kube_cfg)

    defaults = {}
    defaults['context'] = context_names[context_id]
    defaults['namespace'] = 'default' # namespaces[context_id]
    defaults['cert'] = certs[context_id]
    defaults['config'] = kubeconfig
    defaults['user'] = 'spark'

    return defaults

def set_up_user(username: str, name_space: str, defaults: Dict) -> None:
    namespace = name_space or defaults['namespace']
    kubeconfig = defaults['config']
    context_name = defaults['context']

    rolebindingname = username + '-role'
    roleaccess='view'
    os.system(f"{KUBECTL_CMD} create serviceaccount --kubeconfig={kubeconfig} --context={context_name} {username} --namespace={namespace}")
    os.system(f"{KUBECTL_CMD} create rolebinding --kubeconfig={kubeconfig} --context={context_name} {rolebindingname} --role={roleaccess}  --serviceaccount={namespace}:{username} --namespace={namespace}")

def print_cert(defaults: Dict) -> None:
    cert_encoded = defaults['cert']
    os.system(f'\n\necho {cert_encoded} | base64 --decode')

def generate_token(serviceaccountname: str, name_space: str, defaults: Dict) -> None:
    namespace = name_space or defaults['namespace']
    kubeconfig = defaults['config']
    context_name = defaults['context']
    os.system(f'{KUBECTL_CMD} create token {serviceaccountname} --namespace {namespace} --kubeconfig={kubeconfig} --context={context_name}')

if __name__ == "__main__":
    USER_HOME_DIR = pwd.getpwuid(os.getuid())[USER_HOME_DIR_ENT_IDX]
    DEFAULT_KUBECONFIG = f'{USER_HOME_DIR}/.kube/config'

    parser = argparse.ArgumentParser()
    parser.add_argument("--kubeconfig", default=None, help='Kubernetes configuration file')
    parser.add_argument("--context", default=None, help='Context name to use within the provided kubernetes configuration file')
    subparsers = parser.add_subparsers(dest='action')
    subparsers.required = True

    #  subparser for service-account
    parser_account = subparsers.add_parser('service-account')
    parser_account.add_argument('--username', default='spark', help='Service account username to be created in kubernetes. Default is spark')
    parser_account.add_argument('--namespace', default=None, help='Namespace for the service account to be created in kubernetes. Default is default namespace')

    #  subparser for CA certificate
    parser_certificate = subparsers.add_parser('get-ca-cert')

    #  subparser for OAuth token
    parser_token = subparsers.add_parser('get-token')
    parser_token.add_argument('--username', default='spark', help='Service account name for which the Oauth token is to be fetched. Default is spark account.')
    parser_token.add_argument('--namespace', default=None, help='Namespace for the service account for which the Oauth token is to be fetched. Default is default namespace')

    args = parser.parse_args()

    defaults = get_defaults_from_kubeconfig(args.kubeconfig or DEFAULT_KUBECONFIG, args.context)
    print(defaults)

    if args.action == 'service-account':
        username = args.username
        namespace = args.namespace or defaults['namespace']
        set_up_user(username, namespace, defaults)
    elif args.action == 'get-ca-cert':
        print_cert(defaults)
    elif args.action == 'get-token':
        username = args.username
        namespace = args.namespace or defaults['namespace']
        generate_token(username, namespace, defaults)