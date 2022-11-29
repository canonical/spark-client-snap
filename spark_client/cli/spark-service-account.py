#!/usr/bin/env python3

import argparse
import logging
from enum import Enum
import json

from spark_client.cli import defaults
from spark_client.domain import ServiceAccount, PropertyFile
from spark_client.services import K8sServiceAccountRegistry, parse_conf_overrides, KubeInterface


def build_service_account_from_args(args) -> ServiceAccount:
    return ServiceAccount(
        name=args.username, namespace=args.namespace, api_server=registry.kube_interface.api_server,
        primary=args.primary if hasattr(args, "primary") else False
    )


class Actions(str, Enum):
    CREATE = "create"
    DELETE = "delete"
    UPDATE_CONF = "update-conf"
    GET_CONF = "get-conf"
    DELETE_CONF = "delete-conf"
    PRIMARY = "get-primary"
    LIST = "list"


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--log-level", default="ERROR", type=str, help="Level for logging."
    )
    parser.add_argument(
        "--kubeconfig", default=None, help="Kubernetes configuration file"
    )
    parser.add_argument(
        "--context",
        default=None,
        help="Context name to use within the provided kubernetes configuration file",
    )
    parser.add_argument(
        "--namespace",
        default="default",
        help="Namespace for the service account. Default is 'default'.",
    )
    parser.add_argument(
        "--username",
        default="spark",
        help="Service account username. Default is 'spark'.",
    )

    subparsers = parser.add_subparsers(dest="action")
    subparsers.required = True

    #  subparser for service-account
    parser_account = subparsers.add_parser(Actions.CREATE.value)
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
    parser_account = subparsers.add_parser(str(Actions.DELETE.value))

    #  subparser for sa-conf-create
    parser_account = subparsers.add_parser(str(Actions.UPDATE_CONF.value))
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

    #  subparser for sa-conf-get
    parser_account = subparsers.add_parser(str(Actions.GET_CONF.value))
    parser_account.add_argument(
        "--conf", action="append", type=str, help="Config property to retrieve."
    )

    #  subparser for sa-conf-del
    parser_account = subparsers.add_parser(Actions.DELETE_CONF.value)

    #  subparser for resources-primary-sa
    parser_account = subparsers.add_parser(Actions.PRIMARY.value)

    parser_account = subparsers.add_parser(Actions.LIST.value)

    args = parser.parse_args()

    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(message)s", level=args.log_level
    )

    kube_interface = KubeInterface(defaults.kube_config)

    context = args.context or kube_interface.context_name

    logging.info(f"Using K8s context: {context}")

    registry = K8sServiceAccountRegistry(kube_interface.with_context(context))

    if args.action == Actions.CREATE:

        service_account = build_service_account_from_args(args)
        service_account.extra_confs = \
            (PropertyFile.read(args.properties_file) if args.properties_file is not None else PropertyFile.empty()) + \
            parse_conf_overrides(args.conf)

        registry.create(service_account)

    elif args.action == Actions.DELETE:

        registry.delete(build_service_account_from_args(args).id)

    elif args.action == Actions.UPDATE_CONF:

        account_configuration = \
            (PropertyFile.read(args.properties_file) if args.properties_file is not None else PropertyFile.empty()) + \
            parse_conf_overrides(args.conf)

        registry.set_configurations(build_service_account_from_args(args).id, account_configuration)

    elif args.action == Actions.GET_CONF:

        registry.get(build_service_account_from_args(args).id).configurations.log(print)

    elif args.action == Actions.DELETE_CONF:

        registry.set_configurations(build_service_account_from_args(args).id, PropertyFile.empty())

    elif args.action == Actions.PRIMARY:

        registry.get_primary().configurations.log(print)

    elif args.action == Actions.LIST:

        for service_account in registry.all():
            print(f"{service_account.id}\t{service_account.primary}\t{json.dumps(service_account.extra_confs.props)}")
