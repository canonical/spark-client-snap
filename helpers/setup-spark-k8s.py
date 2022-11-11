#!/usr/bin/env python3

import argparse
import utils
import logging

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)


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
    parser_account.add_argument('--properties-file', default = None, help='File with all configuration properties assignments.')
    parser_account.add_argument('--conf', action='append', type=str, help='Config properties to be added to the service account.')

    #  subparser for service-account-cleanup
    parser_account = subparsers.add_parser('service-account-cleanup')

    #  subparser for sa-conf-create
    parser_account = subparsers.add_parser('sa-conf-create')
    parser_account.add_argument('--properties-file', default = None, help='File with all configuration properties assignments.')
    parser_account.add_argument('--conf', action='append', type=str, help='Config properties to be added to the service account.')

    #  subparser for sa-conf-get
    parser_account = subparsers.add_parser('sa-conf-get')
    parser_account.add_argument('--conf', action='append', type=str, help='Config property to retrieve.')

    #  subparser for sa-conf-del
    parser_account = subparsers.add_parser('sa-conf-delete')

    #  subparser for resources-primary-sa
    parser_account = subparsers.add_parser('resources-primary-sa')

    args = parser.parse_args()

    defaults = utils.get_defaults_from_kubeconfig(args.kubeconfig, args.context)
    
    if args.action == 'service-account':
        utils.set_up_user(args.username, args.namespace, args.kubeconfig, args.context, defaults, args.primary)
        utils.setup_kubernetes_secret(args.username, args.namespace, args.kubeconfig, args.context, args.properties_file, args.conf)
    elif args.action == 'service-account-cleanup':
        utils.cleanup_user(args.username, args.namespace, args.kubeconfig, args.context)
    elif args.action == 'sa-conf-create':
        utils.delete_kubernetes_secret(args.username, args.namespace, args.kubeconfig, args.context)
        utils.setup_kubernetes_secret(args.username, args.namespace, args.kubeconfig, args.context, args.properties_file, args.conf)
    elif args.action == 'sa-conf-get':
        conf = utils.retrieve_kubernetes_secret(args.username, args.namespace, args.kubeconfig, args.context, args.conf)
        utils.print_properties(conf)
    elif args.action == 'sa-conf-delete':
        utils.delete_kubernetes_secret(args.username, args.namespace, args.kubeconfig, args.context)
    elif args.action == 'resources-primary-sa':
        conf = utils.retrieve_primary_service_account_details(args.namespace, args.kubeconfig, args.context)
        utils.print_properties(conf)

