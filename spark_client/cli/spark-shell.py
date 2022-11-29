#!/usr/bin/env python3

import argparse
import logging

from typing import Optional

from spark_client.cli import defaults
from spark_client.exceptions import NoAccountFound
from spark_client.domain import ServiceAccount
from spark_client.services import K8sServiceAccountRegistry, SparkInterface, KubeInterface

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--log-level", default="ERROR", type=str, help="Level for logging."
    )
    parser.add_argument(
        "--master", default=None, type=str, help="Kubernetes control plane uri."
    )
    parser.add_argument(
        "--properties-file",
        default=None,
        type=str,
        help="Spark default configuration properties file.",
    )
    parser.add_argument(
        "--username",
        default=None,
        type=str,
        help="Service account name to use other than primary.",
    )
    parser.add_argument(
        "--namespace",
        default=None,
        type=str,
        help="Namespace of service account name to use other than primary.",
    )
    args, extra_args = parser.parse_known_args()

    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(message)s", level=args.log_level
    )

    kube_interface = KubeInterface(defaults.kube_config, kubectl_cmd=defaults.kubectl_cmd)

    if args.master is not None:
        contexts_for_api_server = [
            context["name"]
            for context in kube_interface.kube_config["contexts"]
            if context["context"]["cluster"] == args.master
        ]

        if len(contexts_for_api_server) == 0:
            raise NoAccountFound(args.master)
    else:
        contexts_for_api_server = kube_interface.available_contexts

    context = contexts_for_api_server[0]

    logging.info(f"Using K8s context: {context}")

    registry = K8sServiceAccountRegistry(kube_interface.with_context(context))

    service_account: Optional[ServiceAccount] = registry.get_primary() if args.username is None and args.namespace is None \
        else registry.get(f"{args.namespace or 'default'}:{args.username or 'spark'}")

    if service_account is None:
        raise ValueError("Service account provided does not exist.")

    SparkInterface(service_account=service_account, defaults=defaults).spark_shell(
        args.properties_file, extra_args
    )
