#!/usr/bin/env python3

import argparse
import logging
import os
import pwd

import constants
import utils

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--log-level", default="ERROR", type=str, help="Level for logging."
    )
    parser.add_argument(
        "--username", default=None, type=str, help="Username of service account to use."
    )
    parser.add_argument(
        "--namespace", default=None, type=str, help="Namespace of service account."
    )
    parser.add_argument("--master", default=None, type=str, help="Control plane uri.")
    parser.add_argument(
        "--properties-file",
        default=None,
        type=str,
        help="Spark default configuration properties file.",
    )
    args, extra_args = parser.parse_known_args()

    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(message)s", level=args.log_level
    )

    os.environ["HOME"] = str(pwd.getpwuid(os.getuid())[constants.USER_HOME_DIR_ENT_IDX])
    if os.environ.get("SPARK_HOME") is None or os.environ.get("SPARK_HOME") == "":
        os.environ["SPARK_HOME"] = os.environ["SNAP"]

    STATIC_DEFAULTS_CONF_FILE = utils.get_static_defaults_conf_file()
    ENV_DEFAULTS_CONF_FILE = utils.get_env_defaults_conf_file()

    snap_static_defaults = utils.read_property_file(STATIC_DEFAULTS_CONF_FILE)
    setup_dynamic_defaults = utils.get_dynamic_defaults(args.username, args.namespace)
    env_defaults = utils.read_property_file(ENV_DEFAULTS_CONF_FILE)
    props_file_arg_defaults = utils.read_property_file(args.properties_file)

    with utils.UmaskNamedTemporaryFile(
        mode="w", prefix="spark-conf-", suffix=".conf"
    ) as t:
        defaults = utils.merge_configurations(
            [
                snap_static_defaults,
                setup_dynamic_defaults,
                env_defaults,
                props_file_arg_defaults,
            ]
        )
        logging.debug(
            f"Spark props available for reference at {utils.get_snap_temp_dir()}{t.name}\n"
        )
        utils.write_property_file(t.file, defaults, log=True)
        t.flush()

        pyspark_args = [
            f"--master {args.master or utils.autodetect_kubernetes_master(defaults)}",
            f"--properties-file {t.name}",
        ] + extra_args

        SPARK_HOME = os.environ["SPARK_HOME"]
        PYSPARK_ARGS = " ".join(pyspark_args)
        pyspark_cmd = f"{SPARK_HOME}/bin/pyspark {PYSPARK_ARGS}"
        logging.info(pyspark_cmd)
        os.system(pyspark_cmd)
