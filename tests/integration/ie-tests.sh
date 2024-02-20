#!/bin/bash

readonly SPARK_IMAGE='ghcr.io/canonical/charmed-spark:3.4-22.04_edge'

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

validate_file_length() {
  # validate the length of the test file
  number_of_lines=$1
  l=$(wc -l ./tests/integration/resources/example.txt | cut -d' ' -f1)
  if [ "${number_of_lines}" != "$l" ]; then
      echo "ERROR: Number of lines is $number_of_lines, Expected Value: $l. Aborting with exit code 1."
      exit 1
  fi
}

get_s3_access_key(){
  # Prints out S3 Access Key by reading it from K8s secret
  kubectl get secret -n minio-operator microk8s-user-1 -o jsonpath='{.data.CONSOLE_ACCESS_KEY}' | base64 -d
}

get_s3_secret_key(){
  # Prints out S3 Secret Key by reading it from K8s secret
  kubectl get secret -n minio-operator microk8s-user-1 -o jsonpath='{.data.CONSOLE_SECRET_KEY}' | base64 -d
}

get_s3_endpoint(){
  # Prints out the endpoint S3 bucket is exposed on.
  kubectl get service minio -n minio-operator -o jsonpath='{.spec.clusterIP}'
}

create_s3_bucket(){
  # Creates a S3 bucket with the given name.
  BUCKET_NAME=$1
  aws s3 mb "s3://$BUCKET_NAME"
  echo "Created S3 bucket ${BUCKET_NAME}"
}

delete_s3_bucket(){
  # Deletes a S3 bucket with the given name.
  S3_ENDPOINT=$(get_s3_endpoint)
  BUCKET_NAME=$1
  aws s3 rb "s3://$BUCKET_NAME" --force
  echo "Deleted S3 bucket ${BUCKET_NAME}"
}

copy_file_to_s3_bucket(){
  # Copies a file from local to S3 bucket.
  # The bucket name and the path to file that is to be uploaded is to be provided as arguments
  BUCKET_NAME=$1
  FILE_PATH=$2

  # If file path is '/foo/bar/file.ext', the basename is 'file.ext'
  BASE_NAME=$(basename "$FILE_PATH")
  S3_ENDPOINT=$(get_s3_endpoint)

  # Copy the file to S3 bucket
  aws --endpoint-url "http://$S3_ENDPOINT" s3 cp $FILE_PATH s3://"$BUCKET_NAME"/"$BASE_NAME"
  echo "Copied file ${FILE_PATH} to S3 bucket ${BUCKET_NAME}"
}

list_s3_bucket(){
  # List files in a bucket.
  # The bucket name and the path to file that is to be uploaded is to be provided as arguments
  BUCKET_NAME=$1

  S3_ENDPOINT=$(get_s3_endpoint)

  # List files in the S3 bucket
  aws --endpoint-url "http://$S3_ENDPOINT" s3 ls s3://"$BUCKET_NAME/"
  echo "Listed files for bucket: ${BUCKET_NAME}"
}

run_example_job() {

  KUBE_CONFIG=/home/${USER}/.kube/config

  K8S_MASTER_URL=k8s://$(kubectl --kubeconfig=${KUBE_CONFIG} config view -o jsonpath="{.clusters[0]['cluster.server']}")
  SPARK_EXAMPLES_JAR_NAME='spark-examples_2.12-3.4.2.jar'

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
    --conf spark.kubernetes.container.image=$SPARK_IMAGE \
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
  echo -e "$(cat ./tests/integration/resources/test-spark-shell.scala | spark-client.spark-shell \
      --username=${USERNAME} \
      --conf spark.kubernetes.container.image=$SPARK_IMAGE \
      --namespace ${NAMESPACE})" \
      > spark-shell.out
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
  echo -e "$(cat ./tests/integration/resources/test-pyspark.py | spark-client.pyspark \
      --username=${USERNAME} \
      --conf spark.kubernetes.container.image=$SPARK_IMAGE \
      --namespace ${NAMESPACE} --conf spark.executor.instances=2)" \
      > pyspark.out
  cat pyspark.out
  pi=$(cat pyspark.out  | grep "^Pi is roughly" | rev | cut -d' ' -f1 | rev | cut -c 1-3)
  echo -e "Pyspark Pi Job Output: \n ${pi}"
  rm pyspark.out
  validate_pi_value $pi
}

run_pyspark_s3() {
  echo "run_pyspark_s3 ${1} ${2}"

  NAMESPACE=$1
  USERNAME=$2

  ACCESS_KEY="$(get_s3_access_key)"
  SECRET_KEY="$(get_s3_secret_key)"
  S3_ENDPOINT="$(get_s3_endpoint)"

  aws configure set aws_access_key_id $ACCESS_KEY
  aws configure set aws_secret_access_key $SECRET_KEY
  aws configure set default.region "us-east-2"

  # First create S3 bucket named 'test'
  create_s3_bucket test

  # Copy 'example.txt' script to 'test' bucket
  copy_file_to_s3_bucket test ./tests/integration/resources/example.txt

  list_s3_bucket test

  echo -e "$(cat ./tests/integration/resources/test-pyspark-s3.py | spark-client.pyspark \
      --username=${USERNAME} \
      --conf spark.kubernetes.container.image=$SPARK_IMAGE \
      --conf spark.hadoop.fs.s3a.aws.credentials.provider=org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider \
      --conf spark.hadoop.fs.s3a.connection.ssl.enabled=false \
      --conf spark.hadoop.fs.s3a.path.style.access=true \
      --conf spark.hadoop.fs.s3a.endpoint=$S3_ENDPOINT \
      --conf spark.hadoop.fs.s3a.access.key=$ACCESS_KEY \
      --conf spark.hadoop.fs.s3a.secret.key=$SECRET_KEY \
      --namespace ${NAMESPACE} --conf spark.executor.instances=2)" \
      > pyspark.out
  cat pyspark.out
  l=$(cat pyspark.out  | grep "Number of lines" | rev | cut -d' ' -f1 | rev | cut -c 1-3)
  echo -e "Number of lines: \n ${l}"
  rm pyspark.out
  validate_file_length $l
}

run_spark_sql() {
  echo "run_spark_sql ${1} ${2}"

  NAMESPACE=$1
  USERNAME=$2

  ACCESS_KEY="$(get_s3_access_key)"
  SECRET_KEY="$(get_s3_secret_key)"
  S3_ENDPOINT="$(get_s3_endpoint)"

  # First create S3 bucket named 'test'
  create_s3_bucket test

  echo -e "$(cat ./tests/integration/resources/test-spark-sql.sql | spark-client.spark-sql \
      --username=${USERNAME} --namespace ${NAMESPACE} \
      --conf spark.kubernetes.container.image=$SPARK_IMAGE \
      --conf spark.hadoop.fs.s3a.aws.credentials.provider=org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider \
      --conf spark.hadoop.fs.s3a.connection.ssl.enabled=false \
      --conf spark.hadoop.fs.s3a.path.style.access=true \
      --conf spark.hadoop.fs.s3a.endpoint=$S3_ENDPOINT \
      --conf spark.hadoop.fs.s3a.access.key=$ACCESS_KEY \
      --conf spark.hadoop.fs.s3a.secret.key=$SECRET_KEY \
      --conf spark.sql.catalog.local.warehouse=s3a://spark/warehouse \
      --conf spark.sql.warehouse.dir=s3a://test/warehouse \
      --conf hive.metastore.warehouse.dir=s3a://test/hwarehouse \
      --conf spark.executor.instances=2)" > spark_sql.out 
  cat spark_sql.out
  l=$(cat spark_sql.out | grep "^Inserted Rows:" | rev | cut -d' ' -f1 | rev)
  echo -e "Number of rows inserted: ${l}"
  rm spark_sql.out
  delete_s3_bucket test
  if [ "$l" != "3" ]; then
      echo "ERROR: Number of rows inserted: $l, Expected: 3. Aborting with exit code 1."
      exit 1
  fi
}

test_pyspark() {
  run_pyspark tests spark
}

test_pyspark_s3() {
  run_pyspark_s3 tests spark
}

test_spark_sql() {
  run_spark_sql tests spark
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

  OUTPUT=$(spark-client.service-account-registry list)

  EXISTS=$(echo -e "$OUTPUT" | grep "$NAMESPACE:$USERNAME" | wc -l)

  if [ "${EXISTS}" -ne "0" ]; then
      exit 2
  fi

  kubectl delete namespace ${NAMESPACE}

  if [ "${EXIT_CODE}" -ne "0" ]; then
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

  SLEEP_TIME=1
  for i in {1..5}
  do
    pod_status=$(kubectl get pod testpod | awk '{ print $3 }' | tail -n 1)
    echo $pod_status
    if [ "${pod_status}" == "Running" ]
    then
        echo "testpod is Running now!"
        break
    elif [ "${i}" -le "5" ]
    then
        echo "Waiting for the pod to come online..."
        sleep $SLEEP_TIME
    else
        echo "testpod did not come up. Test Failed!"
        exit 3
    fi
    SLEEP_TIME=$(expr $SLEEP_TIME \* 2);
  done

  MY_KUBE_CONFIG=$(cat /home/${USER}/.kube/config)

  kubectl exec testpod -- /bin/bash -c 'mkdir -p ~/.kube'
  kubectl exec testpod -- env KCONFIG="$MY_KUBE_CONFIG" /bin/bash -c 'echo "$KCONFIG" > ~/.kube/config'
  kubectl exec testpod -- /bin/bash -c 'cat ~/.kube/config'
}

teardown_test_pod() {
  kubectl delete pod testpod
}

run_example_job_in_pod() {
  SPARK_EXAMPLES_JAR_NAME='spark-examples_2.12-3.4.2.jar'

  PREVIOUS_JOB=$(kubectl get pods | grep driver | tail -n 1 | cut -d' ' -f1)

  NAMESPACE=$1
  USERNAME=$2


  kubectl exec testpod -- env UU="$USERNAME" NN="$NAMESPACE" JJ="$SPARK_EXAMPLES_JAR_NAME" IM="$SPARK_IMAGE" \
                  /bin/bash -c 'spark-client.spark-submit \
                  --username $UU --namespace $NN \
                  --conf spark.kubernetes.driver.request.cores=100m \
                  --conf spark.kubernetes.executor.request.cores=100m \
                  --conf spark.kubernetes.container.image=$IM \
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

  SPARK_SHELL_COMMANDS=$(cat ./tests/integration/resources/test-spark-shell.scala)

  # Check job output
  # Sample output
  # "Pi is roughly 3.13956232343"

  echo -e "$(kubectl exec testpod -- env UU="$USERNAME" NN="$NAMESPACE" CMDS="$SPARK_SHELL_COMMANDS" IM="$SPARK_IMAGE" /bin/bash -c 'echo "$CMDS" | spark-client.spark-shell --username $UU --namespace $NN --conf spark.kubernetes.container.image=$IM')" > spark-shell.out

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

  PYSPARK_COMMANDS=$(cat ./tests/integration/resources/test-pyspark.py)

  # Check job output
  # Sample output
  # "Pi is roughly 3.13956232343"

  echo -e "$(kubectl exec testpod -- env UU="$USERNAME" NN="$NAMESPACE" CMDS="$PYSPARK_COMMANDS" IM="$SPARK_IMAGE" /bin/bash -c 'echo "$CMDS" | spark-client.pyspark --username $UU --namespace $NN --conf spark.kubernetes.container.image=$IM')" > pyspark.out

  cat pyspark.out
  pi=$(cat pyspark.out  | grep "Pi is roughly" | tail -n 1 | rev | cut -d' ' -f1 | rev | cut -c 1-3)
  echo -e "Pyspark Pi Job Output: \n ${pi}"
  rm pyspark.out
  validate_pi_value $pi
}

run_spark_sql_in_pod() {
  echo "run_spark_sql_in_pod ${1} ${2}"

  NAMESPACE=$1
  USERNAME=$2

  create_s3_bucket test

  SPARK_SQL_COMMANDS=$(cat ./tests/integration/resources/test-spark-sql.sql)

  echo -e "$(kubectl exec testpod -- \
    env \
      UU="$USERNAME" \
      NN="$NAMESPACE" \
      CMDS="$SPARK_SQL_COMMANDS" \
      IM="$SPARK_IMAGE" \
      ACCESS_KEY="$(get_s3_access_key)" \
      SECRET_KEY="$(get_s3_secret_key)" \
      S3_ENDPOINT="$(get_s3_endpoint)" \
    /bin/bash -c 'echo "$CMDS" | spark-client.spark-sql \
      --username $UU \
      --namespace $NN \
      --conf spark.kubernetes.container.image=$IM \
      --conf spark.hadoop.fs.s3a.aws.credentials.provider=org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider \
      --conf spark.hadoop.fs.s3a.connection.ssl.enabled=false \
      --conf spark.hadoop.fs.s3a.path.style.access=true \
      --conf spark.hadoop.fs.s3a.endpoint=$S3_ENDPOINT \
      --conf spark.hadoop.fs.s3a.access.key=$ACCESS_KEY \
      --conf spark.hadoop.fs.s3a.secret.key=$SECRET_KEY \
      --conf spark.sql.warehouse.dir=s3a://test/warehouse \
      --conf spark.driver.extraJavaOptions='-Dderby.system.home=/tmp/derby' \
    ')" > spark_sql.out
  cat spark_sql.out
  num_rows=$(cat spark_sql.out  | grep "^Inserted Rows:" | rev | cut -d' ' -f1 | rev )
  echo -e "Inserted Rows: ${num_rows}"
  rm spark_sql.out
  delete_s3_bucket test
  if [ "$num_rows" != "3" ]; then
      echo "ERROR: Number of rows inserted: $num_rows, Expected: 3. Aborting with exit code 1."
      exit 1
  fi
}


run_pyspark_s3_in_pod() {
  echo "run_pyspark_s3_in_pod ${1} ${2}"

  NAMESPACE=$1
  USERNAME=$2

  PYSPARK_COMMANDS=$(cat ./tests/integration/resources/test-pyspark-s3.py)

  # Check output of pyspark process with s3 

  echo -e "$(kubectl exec testpod -- \
    env \
      UU="$USERNAME" \
      NN="$NAMESPACE" \
      CMDS="$PYSPARK_COMMANDS" \
      IM="$SPARK_IMAGE" \
      ACCESS_KEY="$(get_s3_access_key)" \
      SECRET_KEY="$(get_s3_secret_key)" \
      S3_ENDPOINT="$(get_s3_endpoint)" \
    /bin/bash -c 'echo "$CMDS" | spark-client.pyspark \
      --username $UU \
      --namespace $NN \
      --conf spark.kubernetes.container.image=$IM \
      --conf spark.hadoop.fs.s3a.aws.credentials.provider=org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider \
      --conf spark.hadoop.fs.s3a.connection.ssl.enabled=false \
      --conf spark.hadoop.fs.s3a.path.style.access=true \
      --conf spark.hadoop.fs.s3a.endpoint=$S3_ENDPOINT \
      --conf spark.hadoop.fs.s3a.access.key=$ACCESS_KEY \
      --conf spark.hadoop.fs.s3a.secret.key=$SECRET_KEY 
    ')" > pyspark.out

  cat pyspark.out
  l=$(cat pyspark.out | grep "Number of lines" | tail -n 1 | rev | cut -d' ' -f1 | rev | cut -c 1-3)
  echo -e "Number of lines: \n ${l}"
  rm pyspark.out
  validate_file_length $l
}

test_pyspark_s3_in_pod() {
  run_pyspark_s3_in_pod tests spark
}


test_pyspark_in_pod() {
  run_pyspark_in_pod tests spark
}

test_spark_sql_in_pod() {
  run_spark_sql_in_pod tests spark
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

# (setup_user_admin_context && test_example_job && cleanup_user_success) || cleanup_user_failure

# (setup_user_admin_context && test_spark_shell && cleanup_user_success) || cleanup_user_failure

# (setup_user_admin_context && test_pyspark && cleanup_user_success) || cleanup_user_failure

(setup_user_admin_context && test_spark_sql && cleanup_user_success) || cleanup_user_failure

# (setup_user_admin_context && test_pyspark_s3 && cleanup_user_success) || cleanup_user_failure

# (setup_user_restricted_context && test_restricted_account && cleanup_user_success) || cleanup_user_failure

# setup_test_pod

# (setup_user_admin_context && test_example_job_in_pod && cleanup_user_success) || cleanup_user_failure_in_pod

# (setup_user_admin_context && test_spark_shell_in_pod && cleanup_user_success) || cleanup_user_failure_in_pod

# (setup_user_admin_context && test_pyspark_in_pod && cleanup_user_success) || cleanup_user_failure_in_pod

(setup_user_admin_context && test_spark_sql_in_pod && cleanup_user_success) || cleanup_user_failure_in_pod

# (setup_user_admin_context && test_pyspark_s3_in_pod && cleanup_user_success) || cleanup_user_failure_in_pod

# teardown_test_pod
