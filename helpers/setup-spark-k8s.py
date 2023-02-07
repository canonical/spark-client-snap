#!/usr/bin/env python3

import argparse
import logging

import utils

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Spark Client Setup')
    base_parser = argparse.ArgumentParser()
    base_parser.add_argument(
        "--log-level", default="ERROR", type=str, help="Level for logging."
    )
    base_parser.add_argument(
        "--kubeconfig", default=None, help="Kubernetes configuration file"
    )
    base_parser.add_argument(
        "--context",
        default=None,
        help="Context name to use within the provided kubernetes configuration file",
    )
    base_parser.add_argument(
        "--namespace",
        default="default",
        help="Namespace for the service account. Default is 'default'.",
    )
    base_parser.add_argument(
        "--username",
        default="spark",
        help="Service account username. Default is 'spark'.",
    )

    subparsers = parser.add_subparsers(dest="action")
    subparsers.required = True

    #  subparser for service-account
    parser_account = subparsers.add_parser("service-account", parents=[base_parser])
    parser_account.add_argument(
        "--primary",
        action="store_true",
        help="Boolean to mark the service account as primary.",
    )
    parser_account.add_argument(
        "--properties-file",
        default=None,
        help="File with all configuration properties assignments.",
    )
    parser_account.add_argument(
        "--conf",
        action="append",
        type=str,
        help="Config properties to be added to the service account.",
    )

    #  subparser for service-account-cleanup
    parser_account_cleanup = subparsers.add_parser("service-account-cleanup", parents=[base_parser])

    #  subparser for sa-conf-create
    parser_conf_create = subparsers.add_parser("sa-conf-create", parents=[base_parser])
    parser_conf_create.add_argument(
        "--properties-file",
        default=None,
        help="File with all configuration properties assignments.",
    )
    parser_conf_create.add_argument(
        "--conf",
        action="append",
        type=str,
        help="Config properties to be added to the service account.",
    )

    #  subparser for sa-conf-get
    parser_conf_get = subparsers.add_parser("sa-conf-get", parents=[base_parser])
    parser_conf_get.add_argument(
        "--conf", action="append", type=str, help="Config property to retrieve."
    )

    #  subparser for sa-conf-del
    parser_conf_del = subparsers.add_parser("sa-conf-delete", parents=[base_parser])

    #  subparser for resources-primary-sa
    parser_conf_primary_resources = subparsers.add_parser("resources-primary-sa", parents=[base_parser])

    args = parser.parse_args()

    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(message)s", level=args.log_level
    )

    defaults = utils.get_defaults_from_kubeconfig(args.kubeconfig, args.context)

    if args.action == "service-account":
        utils.set_up_user(
            args.username,
            args.namespace,
            args.kubeconfig,
            args.context,
            defaults,
            args.primary,
        )
        utils.setup_kubernetes_secret(
            args.username,
            args.namespace,
            args.kubeconfig,
            args.context,
            args.properties_file,
            args.conf,
        )
    elif args.action == "service-account-cleanup":
        utils.cleanup_user(args.username, args.namespace, args.kubeconfig, args.context)
    elif args.action == "sa-conf-create":
        utils.delete_kubernetes_secret(
            args.username, args.namespace, args.kubeconfig, args.context
        )
        utils.setup_kubernetes_secret(
            args.username,
            args.namespace,
            args.kubeconfig,
            args.context,
            args.properties_file,
            args.conf,
        )
    elif args.action == "sa-conf-get":
        conf = utils.retrieve_kubernetes_secret(
            args.username, args.namespace, args.kubeconfig, args.context, args.conf
        )
        utils.print_properties(conf)
    elif args.action == "sa-conf-delete":
        utils.delete_kubernetes_secret(
            args.username, args.namespace, args.kubeconfig, args.context
        )
    elif args.action == "resources-primary-sa":
        conf = utils.retrieve_primary_service_account_details(
            args.namespace, args.kubeconfig, args.context
        )
        utils.print_properties(conf)
