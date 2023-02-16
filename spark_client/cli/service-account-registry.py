#!/usr/bin/env python3

import argparse
import json
import logging
from enum import Enum

from spark_client.cli import defaults
from spark_client.domain import PropertyFile, ServiceAccount
from spark_client.exceptions import NoAccountFound
from spark_client.services import (
    K8sServiceAccountRegistry,
    KubeInterface,
    parse_conf_overrides,
)
from spark_client.utils import (
    add_config_arguments,
    add_logging_arguments,
    base_spark_parser,
)


def build_service_account_from_args(args) -> ServiceAccount:
    return ServiceAccount(
        name=args.username,
        namespace=args.namespace,
        api_server=registry.kube_interface.api_server,
        primary=args.primary if hasattr(args, "primary") else False,
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
    parser = argparse.ArgumentParser(description="Spark Client Setup")

    base_parser = add_logging_arguments(
        base_spark_parser(argparse.ArgumentParser(add_help=False))
    )

    subparsers = parser.add_subparsers(dest="action")
    subparsers.required = True

    #  subparser for service-account
    parser_account = add_config_arguments(
        subparsers.add_parser(Actions.CREATE.value, parents=[base_parser])
    )
    parser_account.add_argument(
        "--primary",
        action="store_true",
        help="Boolean to mark the service account as primary.",
    )

    #  subparser for service-account-cleanup
    parser_account_cleanup = subparsers.add_parser(
        Actions.DELETE.value, parents=[base_parser]
    )

    #  subparser for sa-conf-create
    parser_conf_create = add_config_arguments(
        subparsers.add_parser(Actions.UPDATE_CONF.value, parents=[base_parser])
    )

    #  subparser for sa-conf-get
    parser_conf_get = subparsers.add_parser(
        Actions.GET_CONF.value, parents=[base_parser]
    )
    parser_conf_get.add_argument(
        "--conf", action="append", type=str, help="Config property to retrieve."
    )

    #  subparser for sa-conf-del
    parser_conf_del = subparsers.add_parser(
        Actions.DELETE_CONF.value, parents=[base_parser]
    )

    #  subparser for resources-primary-sa
    parser_conf_primary_resources = subparsers.add_parser(
        Actions.PRIMARY.value, parents=[base_parser]
    )

    #  subparser for list
    parser_conf_list = subparsers.add_parser(Actions.LIST.value, parents=[base_parser])

    args = parser.parse_args()

    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(message)s", level=args.log_level
    )

    kube_interface = KubeInterface(
        args.kubeconfig or defaults.kube_config, kubectl_cmd=defaults.kubectl_cmd
    )

    context = args.context or kube_interface.context_name

    logging.info(f"Using K8s context: {context}")

    registry = K8sServiceAccountRegistry(kube_interface.with_context(context))

    if args.action == Actions.CREATE:
        service_account = build_service_account_from_args(args)
        service_account.extra_confs = (
            PropertyFile.read(args.properties_file)
            if args.properties_file is not None
            else PropertyFile.empty()
        ) + parse_conf_overrides(args.conf)

        registry.create(service_account)

    elif args.action == Actions.DELETE:
        registry.delete(build_service_account_from_args(args).id)

    elif args.action == Actions.UPDATE_CONF:
        account_configuration = (
            PropertyFile.read(args.properties_file)
            if args.properties_file is not None
            else PropertyFile.empty()
        ) + parse_conf_overrides(args.conf)

        registry.set_configurations(
            build_service_account_from_args(args).id, account_configuration
        )

    elif args.action == Actions.GET_CONF:
        input_service_account = build_service_account_from_args(args)

        maybe_service_account = registry.get(input_service_account.id)

        if maybe_service_account is None:
            raise NoAccountFound(input_service_account.id)

        maybe_service_account.configurations.log(print)

    elif args.action == Actions.DELETE_CONF:
        registry.set_configurations(
            build_service_account_from_args(args).id, PropertyFile.empty()
        )

    elif args.action == Actions.PRIMARY:
        maybe_service_account = registry.get_primary()

        if maybe_service_account is None:
            raise NoAccountFound()

        maybe_service_account.configurations.log(print)

    elif args.action == Actions.LIST:
        for service_account in registry.all():
            print(
                str.expandtabs(
                    f"{service_account.id}\t{service_account.primary}\t{json.dumps(service_account.extra_confs.props)}"
                )
            )
