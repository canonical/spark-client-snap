#!/bin/bash

setup_tests() {
  sudo snap connect spark-client:dot-kube-config
}

test_example_job() {
  spark-client.service-account-registry create --username=ie-test

  KUBE_CONFIG=/home/${USER}/.kube/config

  K8S_MASTER_URL=k8s://$(kubectl --kubeconfig=${KUBE_CONFIG} config view -o jsonpath="{.clusters[0]['cluster.server']}")
  SPARK_EXAMPLES_JAR_NAME='spark-examples_2.12-3.3.1.jar'

  echo $K8S_MASTER_URL

  PREVIOUS_JOB=$(kubectl --kubeconfig=${KUBE_CONFIG} get pods | grep driver | tail -n 1 | cut -d' ' -f1)

  # run the sample pi job using spark-submit
  spark-client.spark-submit \
    --username=ie-test \
    --log-level "DEBUG" \
    --deploy-mode cluster \
    --conf spark.kubernetes.driver.request.cores=100m \
    --conf spark.kubernetes.executor.request.cores=100m \
    --class org.apache.spark.examples.SparkPi \
    local:///opt/spark/examples/jars/$SPARK_EXAMPLES_JAR_NAME 100

  # kubectl --kubeconfig=${KUBE_CONFIG} get pods
  DRIVER_JOB=$(kubectl --kubeconfig=${KUBE_CONFIG} get pods | grep driver | tail -n 1 | cut -d' ' -f1)

  if [[ "${DRIVER_JOB}" == "${PREVIOUS_JOB}" ]]
  then
    echo "ERROR: Sample job has not run!"
    exit 1
  fi

  echo -e "Inspecting logs for driver job: ${DRIVER_JOB}"
  # kubectl --kubeconfig=${KUBE_CONFIG} logs ${DRIVER_JOB}

  EXECUTOR_JOB=$(kubectl --kubeconfig=${KUBE_CONFIG} get pods | grep exec | tail -n 1 | cut -d' ' -f1)
  echo -e "Inspecting state of executor job: ${EXECUTOR_JOB}"
  # kubectl --kubeconfig=${KUBE_CONFIG} describe pod ${EXECUTOR_JOB}

  # Check job output
  pi=$(kubectl --kubeconfig=${KUBE_CONFIG} logs $(kubectl --kubeconfig=${KUBE_CONFIG} get pods | tail -n 1 | cut -d' ' -f1)  | grep 'Pi is roughly' | rev | cut -d' ' -f1 | rev | cut -c 1-3)
  echo -e "Spark Pi Job Output: \n ${pi}"

  spark-client.service-account-registry delete --username=ie-test

  account_deleted=$(spark-client.service-account-registry get-conf --username=ie-test 2>&1 | grep -c NoAccountFound)

  if [ "${pi}" != "3.1" ]; then
      exit 1
  fi

  if [ "${account_deleted}" == "0" ]; then
      exit 1
  fi

}

test_spark_shell() {
  spark-client.service-account-registry create --username=ie-test

  export DRIVER_IP=$(hostname -I | cut -d " " -f 1)

  echo "import scala.math.random" > test-spark-shell.scala
  echo "val slices = 10" >> test-spark-shell.scala
  echo "val n = math.min(100000L * slices, Int.MaxValue).toInt" >> test-spark-shell.scala
  echo "val count = spark.sparkContext.parallelize(1 until n, slices).map { i => val x = random * 2 - 1; val y = random * 2 - 1;  if (x*x + y*y <= 1) 1 else 0;}.reduce(_ + _)" >> test-spark-shell.scala
  echo "println(s\"Pi is roughly \${4.0 * count / (n - 1)}\")" >> test-spark-shell.scala
  echo "System.exit(0)" >> test-spark-shell.scala
  echo -e "$(cat test-spark-shell.scala | spark-client.spark-shell --username=ie-test --conf "spark.driver.host=${DRIVER_IP}")" > spark-shell.out
  pi=$(cat spark-shell.out  | grep "^Pi is roughly" | rev | cut -d' ' -f1 | rev | cut -c 1-3)
  echo -e "Spark-shell Pi Job Output: \n ${pi}"
  spark-client.service-account-registry delete --username=ie-test
  rm spark-shell.out test-spark-shell.scala
  if [ "${pi}" != "3.1" ]; then
      exit 1
  fi
}

test_pyspark() {
  spark-client.service-account-registry create --username=ie-test

  export DRIVER_IP=$(hostname -I | cut -d " " -f 1)

  echo "import sys" > test-pyspark.py
  echo "from random import random" >> test-pyspark.py
  echo "from operator import add" >> test-pyspark.py
  echo "from pyspark.context import SparkContext" >> test-pyspark.py
  echo "from pyspark.sql.session import SparkSession" >> test-pyspark.py
  echo "sc = SparkContext()" >> test-pyspark.py
  echo "spark = SparkSession(sc)" >> test-pyspark.py
  echo "for conf in spark.sparkContext.getConf().getAll(): print (conf)" >> test-pyspark.py
  echo "partitions = 10" >> test-pyspark.py
  echo "n = 1000000 * partitions" >> test-pyspark.py
  echo "def f(_: int) -> float:" >> test-pyspark.py
  echo "     x, y = random(), random()" >> test-pyspark.py
  echo "     return x * x + y * y < 1 " >> test-pyspark.py
  echo "count = spark.sparkContext.parallelize(range(n), partitions).filter(f).count()" >> test-pyspark.py
  echo "print (\"Pi is roughly %f\" % (4.0 * count / n))" >> test-pyspark.py
  echo -e "$(cat test-pyspark.py | spark-client.pyspark --username=ie-test --conf "spark.driver.host=${DRIVER_IP} --conf spark.executor.instances=2")" > pyspark.out
  cat pyspark.out
  pi=$(cat pyspark.out  | grep "^Pi is roughly" | rev | cut -d' ' -f1 | rev | cut -c 1-3)
  echo -e "Pyspark Pi Job Output: \n ${pi}"
  spark-client.service-account-registry delete --username=ie-test
  rm test-pyspark.py pyspark.out
  if [ "${pi}" != "3.1" ]; then
      exit 1
  fi
}

setup_tests

test_example_job

# test_spark_shell

# test_pyspark