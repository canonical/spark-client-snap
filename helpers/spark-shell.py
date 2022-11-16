#!/usr/bin/env python3

import argparse
import logging
import os
import pwd

import utils

USER_HOME_DIR_ENT_IDX = 5

if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO
    )

    parser = argparse.ArgumentParser()
    parser.add_argument("--master", default=None, type=str, help="Control plane uri.")
    parser.add_argument(
        "--properties-file",
        default=None,
        type=str,
        help="Spark default configuration properties file.",
    )
    args, extra_args = parser.parse_known_args()

    os.environ["HOME"] = str(pwd.getpwuid(os.getuid())[USER_HOME_DIR_ENT_IDX])
    if os.environ.get("SPARK_HOME") is None or os.environ.get("SPARK_HOME") == "":
        os.environ["SPARK_HOME"] = os.environ["SNAP"]

    STATIC_DEFAULTS_CONF_FILE = utils.get_static_defaults_conf_file()
    DYNAMIC_DEFAULTS_CONF_FILE = utils.get_dynamic_defaults_conf_file()
    ENV_DEFAULTS_CONF_FILE = utils.get_env_defaults_conf_file()
    SCALA_HISTORY_FILE = utils.get_scala_shell_history_file()

    snap_static_defaults = utils.read_property_file(STATIC_DEFAULTS_CONF_FILE)
    setup_dynamic_defaults = (
        utils.read_property_file(DYNAMIC_DEFAULTS_CONF_FILE)
        if os.path.isfile(DYNAMIC_DEFAULTS_CONF_FILE)
        else dict()
    )
    setup_dynamic_defaults[
        "spark.driver.extraJavaOptions"
    ] = f"-Dscala.shell.histfile={SCALA_HISTORY_FILE}"
    env_defaults = (
        utils.read_property_file(ENV_DEFAULTS_CONF_FILE)
        if ENV_DEFAULTS_CONF_FILE and os.path.isfile(ENV_DEFAULTS_CONF_FILE)
        else dict()
    )
    props_file_arg_defaults = (
        utils.read_property_file(args.properties_file)
        if args.properties_file
        else dict()
    )

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

        shell_args = [
            f"--master {args.master or utils.autodetect_kubernetes_master(defaults)}",
            f"--properties-file {t.name}",
        ] + extra_args

        SPARK_HOME = os.environ["SPARK_HOME"]
        SPARK_SHELL_ARGS = " ".join(shell_args)
        shell_cmd = f"{SPARK_HOME}/bin/spark-shell {SPARK_SHELL_ARGS}"
        logging.info(shell_cmd)
        os.system(shell_cmd)
