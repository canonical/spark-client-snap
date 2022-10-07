#! /bin/bash

set -e

python3 ${OPS_ROOT}/spark-submit.py "$@"
