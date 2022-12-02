#!/usr/bin/env python3

import argparse
import logging
import re
from typing import Optional

from spark_client.cli import defaults
from spark_client.domain import ServiceAccount
from spark_client.services import (
    K8sServiceAccountRegistry,
    KubeInterface,
    SparkInterface,
)

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

    kube_interface = KubeInterface(
        defaults.kube_config, kubectl_cmd=defaults.kubectl_cmd
    )

    registry = K8sServiceAccountRegistry(
        kube_interface.select_by_master(re.compile("^k8s://").sub("", args.master))
        if args.master is not None
        else kube_interface
    )

    service_account: Optional[ServiceAccount] = (
        registry.get_primary()
        if args.username is None and args.namespace is None
        else registry.get(f"{args.namespace or 'default'}:{args.username or 'spark'}")
    )

    if service_account is None:
        raise ValueError("Service account provided does not exist.")

    SparkInterface(
        service_account=service_account,
        kube_interface=kube_interface,
        defaults=defaults,
    ).pyspark_shell(args.properties_file, extra_args)
