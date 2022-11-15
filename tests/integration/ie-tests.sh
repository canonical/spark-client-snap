#!/bin/bash

test_example_job() {
  sudo snap connect spark-client:dot-kube-config

  spark-client.setup-spark-k8s service-account

  KUBE_CONFIG=/home/${USER}/.kube/config

  K8S_MASTER_URL=k8s://$(kubectl --kubeconfig=${KUBE_CONFIG} config view -o jsonpath="{.clusters[0]['cluster.server']}")
  SPARK_EXAMPLES_JAR_NAME='spark-examples_2.12-3.4.0-SNAPSHOT.jar'

  echo $K8S_MASTER_URL

  # run the sample pi job using spark-submit
  spark-client.spark-submit \
    --master $K8S_MASTER_URL \
    --deploy-mode cluster \
    --conf spark.kubernetes.driver.request.cores=100m \
    --conf spark.kubernetes.executor.request.cores=100m \
    --class org.apache.spark.examples.SparkPi \
    local:///opt/spark/examples/jars/$SPARK_EXAMPLES_JAR_NAME 100

  kubectl --kubeconfig=${KUBE_CONFIG} get pods
  DRIVER_JOB=$(kubectl --kubeconfig=${KUBE_CONFIG} get pods | grep driver | tail -n 1 | cut -d' ' -f1)
  echo -e "Inspecting logs for driver job: ${DRIVER_JOB}"
  kubectl --kubeconfig=${KUBE_CONFIG} logs ${DRIVER_JOB}

  EXECUTOR_JOB=$(kubectl --kubeconfig=${KUBE_CONFIG} get pods | grep exec | tail -n 1 | cut -d' ' -f1)
  echo -e "Inspecting state of executor job: ${EXECUTOR_JOB}"
  kubectl --kubeconfig=${KUBE_CONFIG} describe pod ${EXECUTOR_JOB}

  # Check job output
  pi=$(kubectl --kubeconfig=${KUBE_CONFIG} logs $(kubectl --kubeconfig=${KUBE_CONFIG} get pods | tail -n 1 | cut -d' ' -f1)  | grep 'Pi is roughly' | rev | cut -d' ' -f1 | rev | cut -c 1-4)
  echo -e "Spark Pi Job Output: \n ${pi}"
  if [ "${pi}" != "3.14" ]; then
      exit 1
  fi
}

test_example_job
