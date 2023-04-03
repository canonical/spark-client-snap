#!/bin/bash

setup_tests() {
  sudo snap connect spark-client:dot-kube-config
}

validate_pi_value() {
  pi=$1

  if [ "${pi}" != "3.1" ]; then
      echo "ERROR: Computed Value of pi is $pi, Expected Value: 3.1. Aborting with exit code 1."
      exit 1
  fi
}

run_example_job() {

  KUBE_CONFIG=/home/${USER}/.kube/config

  K8S_MASTER_URL=k8s://$(kubectl --kubeconfig=${KUBE_CONFIG} config view -o jsonpath="{.clusters[0]['cluster.server']}")
  SPARK_EXAMPLES_JAR_NAME='spark-examples_2.12-3.3.2.jar'

  echo $K8S_MASTER_URL

  PREVIOUS_JOB=$(kubectl --kubeconfig=${KUBE_CONFIG} get pods | grep driver | tail -n 1 | cut -d' ' -f1)

  NAMESPACE=$1
  USERNAME=$2

  # run the sample pi job using spark-submit
  spark-client.spark-submit \
    --username=${USERNAME} \
    --namespace=${NAMESPACE} \
    --log-level "DEBUG" \
    --deploy-mode cluster \
    --conf spark.kubernetes.driver.request.cores=100m \
    --conf spark.kubernetes.executor.request.cores=100m \
    --class org.apache.spark.examples.SparkPi \
    local:///opt/spark/examples/jars/$SPARK_EXAMPLES_JAR_NAME 100

  # kubectl --kubeconfig=${KUBE_CONFIG} get pods
  DRIVER_JOB=$(kubectl --kubeconfig=${KUBE_CONFIG} get pods -n ${NAMESPACE} | grep driver | tail -n 1 | cut -d' ' -f1)

  if [[ "${DRIVER_JOB}" == "${PREVIOUS_JOB}" ]]
  then
    echo "ERROR: Sample job has not run!"
    exit 1
  fi

  echo -e "Inspecting logs for driver job: ${DRIVER_JOB}"
  # kubectl --kubeconfig=${KUBE_CONFIG} logs ${DRIVER_JOB}

  EXECUTOR_JOB=$(kubectl --kubeconfig=${KUBE_CONFIG} get pods -n ${NAMESPACE} | grep exec | tail -n 1 | cut -d' ' -f1)
  echo -e "Inspecting state of executor job: ${EXECUTOR_JOB}"
  # kubectl --kubeconfig=${KUBE_CONFIG} describe pod ${EXECUTOR_JOB}

  # Check job output
  # Sample output
  # "Pi is roughly 3.13956232343"
  pi=$(kubectl --kubeconfig=${KUBE_CONFIG} logs $(kubectl --kubeconfig=${KUBE_CONFIG} get pods -n ${NAMESPACE} | grep driver | tail -n 1 | cut -d' ' -f1)  -n ${NAMESPACE} | grep 'Pi is roughly' | rev | cut -d' ' -f1 | rev | cut -c 1-3)
  echo -e "Spark Pi Job Output: \n ${pi}"

  validate_pi_value $pi

}

test_example_job() {
  run_example_job tests spark
}

run_spark_shell() {
  echo "run_spark_shell ${1} ${2}"

  NAMESPACE=$1
  USERNAME=$2

  # Check job output
  # Sample output
  # "Pi is roughly 3.13956232343"
  echo -e "$(cat ./tests/integration/resources/test-spark-shell.txt | spark-client.spark-shell --username=${USERNAME} --namespace ${NAMESPACE})" > spark-shell.out
  pi=$(cat spark-shell.out  | grep "^Pi is roughly" | rev | cut -d' ' -f1 | rev | cut -c 1-3)
  echo -e "Spark-shell Pi Job Output: \n ${pi}"
  rm spark-shell.out
  validate_pi_value $pi
}

test_spark_shell() {
  run_spark_shell tests spark
}

run_pyspark() {
  echo "run_pyspark ${1} ${2}"

  NAMESPACE=$1
  USERNAME=$2

  # Check job output
  # Sample output
  # "Pi is roughly 3.13956232343"
  echo -e "$(cat ./tests/integration/resources/test-pyspark.txt | spark-client.pyspark --username=${USERNAME} --namespace ${NAMESPACE} --conf spark.executor.instances=2)" > pyspark.out
  cat pyspark.out
  pi=$(cat pyspark.out  | grep "^Pi is roughly" | rev | cut -d' ' -f1 | rev | cut -c 1-3)
  echo -e "Pyspark Pi Job Output: \n ${pi}"
  rm pyspark.out
  validate_pi_value $pi
}

test_pyspark() {
  run_pyspark tests spark
}

test_restricted_account() {

  kubectl config set-context spark-context --namespace=tests --cluster=prod --user=spark

  run_example_job tests spark
}

setup_user() {
  echo "setup_user() ${1} ${2} ${3}"

  USERNAME=$1
  NAMESPACE=$2

  kubectl create namespace ${NAMESPACE}

  if [ "$#" -gt 2 ]
  then
    CONTEXT=$3
    spark-client.service-account-registry create --context ${CONTEXT} --username ${USERNAME} --namespace ${NAMESPACE}
  else
    spark-client.service-account-registry create --username ${USERNAME} --namespace ${NAMESPACE}
  fi

}

setup_user_admin_context() {
  setup_user spark tests
}

setup_user_restricted_context() {
  setup_user spark tests microk8s
}

cleanup_user() {
  EXIT_CODE=$1
  USERNAME=$2
  NAMESPACE=$3

  spark-client.service-account-registry delete --username=${USERNAME} --namespace ${NAMESPACE}

  account_not_found_counter=$(spark-client.service-account-registry get-config --username=${USERNAME} --namespace ${NAMESPACE} 2>&1 | grep -c '404 Not Found')

  if [ "${account_not_found_counter}" == "0" ]; then
      exit 2
  fi

  kubectl delete namespace ${NAMESPACE}

  if [ "${EXIT_CODE}" != "0" ]; then
      exit 1
  fi
}

cleanup_user_success() {
  echo "cleanup_user_success()......"
  cleanup_user 0 spark tests
}

cleanup_user_failure() {
  echo "cleanup_user_failure()......"
  cleanup_user 1 spark tests
}

setup_test_pod() {
  kubectl apply -f ./tests/integration/resources/testpod.yaml

  for i in {1..5}
  do
    pod_status=$(kubectl get pod testpod | awk '{ print $3 }' | tail -n 1)
    if [ "${pod_status}" == "Running" ]
    then
        echo "testpod is Running now!"
        break
    elif [ "${i}" -le "5" ]
    then
        sleep 5
    else
        echo "testpod did not come up. Test Failed!"
        exit 3
    fi
  done

  MY_KUBE_CONFIG=$(cat /home/${USER}/.kube/config)

  kubectl exec testpod -- /bin/bash -c 'mkdir /home/spark/.kube'
  kubectl exec testpod -- env KCONFIG="$MY_KUBE_CONFIG" /bin/bash -c 'echo "$KCONFIG" > /home/spark/.kube/config'
  kubectl exec testpod -- /bin/bash -c 'cat /home/spark/.kube/config'
}

teardown_test_pod() {
  kubectl delete pod testpod
}

run_example_job_in_pod() {
  SPARK_EXAMPLES_JAR_NAME='spark-examples_2.12-3.3.2.jar'

  PREVIOUS_JOB=$(kubectl get pods | grep driver | tail -n 1 | cut -d' ' -f1)

  NAMESPACE=$1
  USERNAME=$2

  kubectl exec testpod -- env UU="$USERNAME" NN="$NAMESPACE" JJ="$SPARK_EXAMPLES_JAR_NAME" \
                  /bin/bash -c 'spark-client.spark-submit \
                  --username $UU --namespace $NN \
                  --conf spark.kubernetes.driver.request.cores=100m \
                  --conf spark.kubernetes.executor.request.cores=100m \
                  --class org.apache.spark.examples.SparkPi \
                  local:///opt/spark/examples/jars/$JJ 100'

  # kubectl --kubeconfig=${KUBE_CONFIG} get pods
  DRIVER_JOB=$(kubectl get pods -n ${NAMESPACE} | grep driver | tail -n 1 | cut -d' ' -f1)

  if [[ "${DRIVER_JOB}" == "${PREVIOUS_JOB}" ]]
  then
    echo "ERROR: Sample job has not run!"
    exit 1
  fi

  # Check job output
  # Sample output
  # "Pi is roughly 3.13956232343"
  pi=$(kubectl logs $(kubectl get pods -n ${NAMESPACE} | grep driver | tail -n 1 | cut -d' ' -f1)  -n ${NAMESPACE} | grep 'Pi is roughly' | rev | cut -d' ' -f1 | rev | cut -c 1-3)
  echo -e "Spark Pi Job Output: \n ${pi}"

  validate_pi_value $pi

}

test_example_job_in_pod() {
  run_example_job_in_pod tests spark
}


run_spark_shell_in_pod() {
  echo "run_spark_shell_in_pod ${1} ${2}"

  NAMESPACE=$1
  USERNAME=$2

  SPARK_SHELL_COMMANDS=$(cat ./tests/integration/resources/test-spark-shell.txt)

  # Check job output
  # Sample output
  # "Pi is roughly 3.13956232343"

  echo -e "$(kubectl exec testpod -- env UU="$USERNAME" NN="$NAMESPACE" CMDS="$SPARK_SHELL_COMMANDS" /bin/bash -c 'echo "$CMDS" | spark-client.spark-shell --username $UU --namespace $NN')" > spark-shell.out

  pi=$(cat spark-shell.out  | grep "^Pi is roughly" | rev | cut -d' ' -f1 | rev | cut -c 1-3)
  echo -e "Spark-shell Pi Job Output: \n ${pi}"
  rm spark-shell.out
  validate_pi_value $pi
}

test_spark_shell_in_pod() {
  run_spark_shell_in_pod tests spark
}

run_pyspark_in_pod() {
  echo "run_pyspark_in_pod ${1} ${2}"

  NAMESPACE=$1
  USERNAME=$2

  PYSPARK_COMMANDS=$(cat ./tests/integration/resources/test-pyspark.txt)

  # Check job output
  # Sample output
  # "Pi is roughly 3.13956232343"

  echo -e "$(kubectl exec testpod -- env UU="$USERNAME" NN="$NAMESPACE" CMDS="$PYSPARK_COMMANDS" /bin/bash -c 'echo "$CMDS" | spark-client.pyspark --username $UU --namespace $NN')" > pyspark.out

  cat pyspark.out
  pi=$(cat pyspark.out  | grep "Pi is roughly" | tail -n 1 | rev | cut -d' ' -f1 | rev | cut -c 1-3)
  echo -e "Pyspark Pi Job Output: \n ${pi}"
  rm pyspark.out
  validate_pi_value $pi
}

test_pyspark_in_pod() {
  run_pyspark_in_pod tests spark
}

test_restricted_account_in_pod() {

  kubectl config set-context spark-context --namespace=tests --cluster=prod --user=spark

  run_example_job_in_pod tests spark
}

cleanup_user_failure_in_pod() {
  teardown_test_pod
  cleanup_user_failure
}

setup_tests

(setup_user_admin_context && test_example_job && cleanup_user_success) || cleanup_user_failure

(setup_user_admin_context && test_spark_shell && cleanup_user_success) || cleanup_user_failure

(setup_user_admin_context && test_pyspark && cleanup_user_success) || cleanup_user_failure

(setup_user_restricted_context && test_restricted_account && cleanup_user_success) || cleanup_user_failure

setup_test_pod

(setup_user_admin_context && test_example_job_in_pod && cleanup_user_success) || cleanup_user_failure_in_pod

(setup_user_admin_context && test_spark_shell_in_pod && cleanup_user_success) || cleanup_user_failure_in_pod

(setup_user_admin_context && test_pyspark_in_pod && cleanup_user_success) || cleanup_user_failure_in_pod

#(setup_user_restricted_context && test_restricted_account_in_pod && cleanup_user_success) || cleanup_user_failure_in_pod

teardown_test_pod