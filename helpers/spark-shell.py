#!/usr/bin/env python3

import os
import pwd
import logging
import argparse
import utils

USER_HOME_DIR_ENT_IDX = 5

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("--deploy-mode", default="client", type=str, help='Deployment mode for spark shell. Default is \'client\'.')
    args, extra_args = parser.parse_known_args()

    os.environ["HOME"] = pwd.getpwuid(os.getuid())[USER_HOME_DIR_ENT_IDX]
    if os.environ.get('SPARK_HOME') is None or os.environ.get('SPARK_HOME') == '':
        os.environ['SPARK_HOME'] = os.environ['SNAP']

    SPARK_HOME = os.environ['SPARK_HOME']
    SPARK_SHELL_ARGS = ' '.join(extra_args)
    SCALA_HISTORY_FILE = utils.get_scala_shell_history_file()
    shell_cmd = f'{SPARK_HOME}/bin/spark-shell --deploy-mode client --conf spark.driver.extraJavaOptions=\'-Dscala.shell.histfile={SCALA_HISTORY_FILE}\' {SPARK_SHELL_ARGS}'
    logging.debug(shell_cmd)
    os.system(shell_cmd)