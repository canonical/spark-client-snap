#!/usr/bin/env python3

import sys
import os
import yaml
import argparse
import pwd
from typing import Dict
import utils
import logging

KUBECTL_CMD= '{}/kubectl'.format(os.environ['SNAP'])
USER_HOME_DIR_ENT_IDX = 5

def print_help_for_missing_or_inaccessible_kubeconfig_file(kubeconfig: str):
    print('\nERROR: Missing kubeconfig file {}. Or default kubeconfig file {}/.kube/config not found.'.format(kubeconfig, pwd.getpwuid(os.getuid())[5]))
    print('\n')
    print('Looks like either kubernetes is not set up properly or default kubeconfig file is not accessible!')
    print('Please take the following remedial actions.')
    print('	1. Please set up kubernetes and make sure kubeconfig file is available, accessible and correct.')
    print('	2. sudo snap connect spark-client:dot-kube-config')

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
    print('	2. sudo snap connect spark-client:dot-kube-config')

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
    defaults['namespace'] = 'default'
    defaults['cert'] = certs[context_id]
    defaults['config'] = kubeconfig
    defaults['user'] = 'spark'

    return defaults

def set_up_user(username: str, name_space: str, defaults: Dict, mark_primary: bool) -> None:
    namespace = name_space or defaults['namespace']
    kubeconfig = defaults['config']
    context_name = defaults['context']

    rolebindingname = username + '-role'
    roleaccess='view'
    label = utils.get_management_label()

    os.system(f"{KUBECTL_CMD} create serviceaccount --kubeconfig={kubeconfig} --context={context_name} {username} --namespace={namespace}")
    os.system(f"{KUBECTL_CMD} create rolebinding --kubeconfig={kubeconfig} --context={context_name} {rolebindingname} --role={roleaccess}  --serviceaccount={namespace}:{username} --namespace={namespace}")

    primary_label_to_remove = utils.get_primary_label(label=False)
    primary_label_full = utils.get_primary_label()

    primary = utils.retrieve_primary_service_account_details()
    is_primary_defined = len(primary.keys()) > 0

    logging.debug(f"is_primary_defined={is_primary_defined}")
    logging.debug(f"mark_primary={mark_primary}")

    if is_primary_defined and mark_primary:
        sa_to_unlabel = primary['spark.kubernetes.authenticate.driver.serviceAccountName']
        namespace_of_sa_to_unlabel = primary['spark.kubernetes.namespace']
        rolebindingname_to_unlabel = sa_to_unlabel + '-role'

        os.system(f"{KUBECTL_CMD} label serviceaccount --kubeconfig={kubeconfig} --context={context_name} --namespace={namespace_of_sa_to_unlabel} {sa_to_unlabel} {primary_label_to_remove}-")
        os.system(f"{KUBECTL_CMD} label rolebinding --kubeconfig={kubeconfig} --context={context_name} --namespace={namespace_of_sa_to_unlabel} {rolebindingname_to_unlabel} {primary_label_to_remove}-")

        os.system(f"{KUBECTL_CMD} label serviceaccount --kubeconfig={kubeconfig} --context={context_name} {username} {label} {primary_label_full} --namespace={namespace}")
        os.system(f"{KUBECTL_CMD} label rolebinding --kubeconfig={kubeconfig} --context={context_name} {rolebindingname} {label} {primary_label_full} --namespace={namespace}")
    elif is_primary_defined and not mark_primary:
        os.system(f"{KUBECTL_CMD} label serviceaccount --kubeconfig={kubeconfig} --context={context_name} {username} {label} --namespace={namespace}")
        os.system(f"{KUBECTL_CMD} label rolebinding --kubeconfig={kubeconfig} --context={context_name} {rolebindingname} {label} --namespace={namespace}")
    elif not is_primary_defined:
        os.system(f"{KUBECTL_CMD} label serviceaccount --kubeconfig={kubeconfig} --context={context_name} {username} {label} {primary_label_full} --namespace={namespace}")
        os.system(f"{KUBECTL_CMD} label rolebinding --kubeconfig={kubeconfig} --context={context_name} {rolebindingname} {label} {primary_label_full} --namespace={namespace}")
    else:
        logging.warning("Labeling logic issue.....")


def cleanup_user(username: str, namespace: str, k8s_context: str) -> None:
    kubectl_cmd = utils.build_kubectl_cmd(namespace, k8s_context)
    rolebindingname = username + '-role'

    os.system(f"{kubectl_cmd} delete serviceaccount {username}")
    os.system(f"{kubectl_cmd} delete rolebinding {rolebindingname}")
    utils.delete_kubernetes_secret(username, namespace, k8s_context)

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)

    USER_HOME_DIR = pwd.getpwuid(os.getuid())[USER_HOME_DIR_ENT_IDX]
    DEFAULT_KUBECONFIG = f'{USER_HOME_DIR}/.kube/config'

    parser = argparse.ArgumentParser()
    parser.add_argument("--kubeconfig", default=None, help='Kubernetes configuration file')
    parser.add_argument("--context", default=None, help='Context name to use within the provided kubernetes configuration file')
    parser.add_argument('--namespace', default='default', help='Namespace for the service account. Default is \'default\'.')
    parser.add_argument('--username', default='spark', help='Service account username. Default is \'spark\'.')

    subparsers = parser.add_subparsers(dest='action')
    subparsers.required = True

    #  subparser for service-account
    parser_account = subparsers.add_parser('service-account')
    parser_account.add_argument('--primary', action='store_true', help='Boolean to mark the service account as primary.')
    parser_account.add_argument('--conf', action='append', type=str, help='Config properties to be added to the service account.')

    #  subparser for service-account-cleanup
    parser_account = subparsers.add_parser('service-account-cleanup')

    #  subparser for sa-conf-put
    parser_account = subparsers.add_parser('sa-conf-put')
    parser_account.add_argument('--properties-file', default = None, help='File with all configuration properties assignments.')

    #  subparser for sa-conf-get
    parser_account = subparsers.add_parser('sa-conf-get')
    parser_account.add_argument('--conf', action='append', type=str, help='Config property to retrieve.')

    #  subparser for sa-conf-del
    parser_account = subparsers.add_parser('sa-conf-del')

    # #  subparser for resources-sa
    # parser_account = subparsers.add_parser('resources-sa')

    #  subparser for resources-primary-sa
    parser_account = subparsers.add_parser('resources-primary-sa')

    args = parser.parse_args()

    defaults = get_defaults_from_kubeconfig(args.kubeconfig or DEFAULT_KUBECONFIG, args.context)
    
    if args.action == 'service-account':
        username = args.username
        namespace = args.namespace or defaults['namespace']
        set_up_user(username, namespace, defaults, args.primary)
        utils.setup_kubernetes_secret_literal(username, namespace, args.context, args.conf)
    elif args.action == 'service-account-cleanup':
        cleanup_user(args.username, args.namespace, args.context)
    elif args.action == 'sa-conf-put':
        utils.setup_kubernetes_secret_env_file(args.username, args.namespace or defaults['namespace'], args.context, args.properties_file)
    elif args.action == 'sa-conf-get':
        conf = utils.retrieve_kubernetes_secret(args.username, args.namespace, args.context, args.conf)
        utils.print_properties(conf)
    elif args.action == 'sa-conf-del':
        utils.delete_kubernetes_secret(args.username, args.namespace, args.context)
    # elif args.action == 'resources-sa':
    #     conf = utils.retrieve_k8s_resources_by_label(args.namespace, args.context)
    #     utils.print_properties(conf)
    elif args.action == 'resources-primary-sa':
        conf = utils.retrieve_primary_service_account_details()
        utils.print_properties(conf)

