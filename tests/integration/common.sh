#!/bin/bash

# Derive Spark component versions used by integration tests.
# Allows overrides via environment variables while defaulting
# to the version recorded in the repository SPARK_VERSION file.

SPARK_VERSION_FILE=${SPARK_VERSION_FILE:-"./SPARK_VERSION"}

if [ ! -f "${SPARK_VERSION_FILE}" ]; then
  echo "ERROR: Spark version file not found at ${SPARK_VERSION_FILE}." >&2
  exit 1
fi

SPARK_VERSION_CONTENT=$(tr -d ' \n' < "${SPARK_VERSION_FILE}")
SPARK_RELEASE_VERSION=${SPARK_VERSION_CONTENT%%-*}
SPARK_MAJOR_MINOR=$(echo "${SPARK_RELEASE_VERSION}" | cut -d'.' -f1-2)

DEFAULT_SPARK_IMAGE="ghcr.io/canonical/charmed-spark:${SPARK_MAJOR_MINOR}-22.04_edge"
DEFAULT_SPARK_EXAMPLES_JAR_NAME="spark-examples_2.12-${SPARK_RELEASE_VERSION}.jar"

export INTEGRATION_SPARK_VERSION="${SPARK_VERSION_CONTENT}"
export INTEGRATION_SPARK_RELEASE_VERSION="${SPARK_RELEASE_VERSION}"
export INTEGRATION_SPARK_MAJOR_MINOR_VERSION="${SPARK_MAJOR_MINOR}"
export INTEGRATION_SPARK_IMAGE="${SPARK_IMAGE:-${DEFAULT_SPARK_IMAGE}}"
export INTEGRATION_SPARK_EXAMPLES_JAR_NAME="${SPARK_EXAMPLES_JAR_NAME:-${DEFAULT_SPARK_EXAMPLES_JAR_NAME}}"
