#!/bin/bash

# Copyright 2025 Canonical Ltd.

readonly SPARK_IMAGE='ghcr.io/canonical/charmed-spark:4.0-22.04_edge'
readonly SPARK_EXAMPLES_JAR_NAME='spark-examples_2.13-4.0.1.jar'

S3_BUCKET=test-snap-$(uuidgen)
SERVICE_ACCOUNT=spark
NAMESPACE=tests
KUBECONFIG=/home/${USER}/.kube/config

setup_tests() {
  sudo snap connect spark-client:dot-kube-config
}

validate_pi_value() {
  pi=$1

  if [ "${pi}" != "3.1" ]; then
      echo "ERROR: Computed Value of pi is $pi, Expected Value: 3.1. Aborting with exit code 1."
      return 1
  fi
  return 0
}

test_spark_submit_custom_certificate() {
  run_spark_submit_custom_certificate
}

run_spark_submit_custom_certificate(){
  
  KUBE_CONFIG=/home/${USER}/.kube/config

  # delete username if it exist
  spark-client.service-account-registry delete --username hello

  # Microceph credentials
  CA_CERT="/home/${USER}/certs/ca.crt"
  IP=$(ip route get 1.1.1.1 | awk '{print $7; exit}')
  S3_SERVER_URL="https://$IP"
  S3_ACCESS_KEY="foo"
  S3_SECRET_KEY="bar"
 

  # reconfigure the aws lib to work with local instance of microceph behind haproxy
  aws configure set aws_access_key_id $S3_ACCESS_KEY
  aws configure set aws_secret_access_key $S3_SECRET_KEY
  aws configure set default.region "us-east-1"

  # create folder
  aws --no-verify-ssl --endpoint-url "$S3_SERVER_URL" s3 mb "s3://dist-cache" 
  aws --no-verify-ssl --endpoint-url "$S3_SERVER_URL" s3 mb "s3://history-server"

  # create service account 
  spark-client.service-account-registry create --username hello \
    --conf spark.hadoop.fs.s3a.access.key=$S3_ACCESS_KEY \
    --conf spark.hadoop.fs.s3a.secret.key=$S3_SECRET_KEY \
    --conf spark.hadoop.fs.s3a.endpoint=$S3_SERVER_URL \
    --conf spark.hadoop.fs.s3a.impl=org.apache.hadoop.fs.s3a.S3AFileSystem \
    --conf spark.hadoop.fs.s3a.connection.ssl.enabled=true \
    --conf spark.hadoop.fs.s3a.path.style.access=true \
    --conf spark.eventLog.enabled=true \
    --conf spark.hadoop.fs.s3a.fast.upload=true \
    --conf spark.kubernetes.file.upload.path=s3a://dist-cache/ \
    --conf spark.eventLog.dir=s3a://history-server/ \
    --conf spark.history.fs.logDirectory=s3a://history-server/

  # list buckets 
  echo "Current buckets:"
  aws --no-verify-ssl --endpoint-url "$S3_SERVER_URL" s3 ls

  echo "Actual configs"
  spark-client.service-account-registry get-config --username hello

  echo "Generate truststore"
  # create certificate for running the Spark Job
  keytool -import -alias ceph-cert -file $CA_CERT -storetype JKS -keystore cacerts -storepass changeit -noprompt

  mv cacerts spark.truststore

  echo "Create secret for truststore"
  sudo microk8s.kubectl create secret generic spark-truststore --from-file spark.truststore

  # Import certificate
  # echo "Import certificate"
  spark-client.import-certificate ceph-cert $CA_CERT

  echo "Configure spark job with the new certificate"
  spark-client.service-account-registry add-config --username hello \
      --conf spark.executor.extraJavaOptions="-Djavax.net.ssl.trustStore=/spark-truststore/spark.truststore -Djavax.net.ssl.trustStorePassword=changeit" \
      --conf spark.driver.extraJavaOptions="-Djavax.net.ssl.trustStore=/spark-truststore/spark.truststore -Djavax.net.ssl.trustStorePassword=changeit" \
      --conf spark.kubernetes.executor.secrets.spark-truststore=/spark-truststore \
      --conf spark.kubernetes.driver.secrets.spark-truststore=/spark-truststore \
      --conf spark.kubernetes.container.image=${SPARK_IMAGE}
  
  echo "Print current config."
  spark-client.service-account-registry get-config --username hello

  echo "Run Spark job"
  spark-client.spark-submit \
    --username hello -v \
    --conf spark.hadoop.fs.s3a.connection.ssl.enabled=true \
    --conf spark.kubernetes.executor.request.cores=0.1 \
    --files="./tests/integration/resources/example.txt" \
    --class org.apache.spark.examples.SparkPi \
    local:///opt/spark/examples/jars/$SPARK_EXAMPLES_JAR_NAME 100

  DRIVER_JOB=$(kubectl --kubeconfig=${KUBE_CONFIG} get pods -n ${NAMESPACE} | grep driver | tail -n 1 | cut -d' ' -f1)

  if [[ "${DRIVER_JOB}" == "${PREVIOUS_JOB}" ]]
  then
    echo "ERROR: Sample job has not run!"
    exit 1
  fi

  # retrieve driver logs
  logs=$(kubectl --kubeconfig=${KUBE_CONFIG} logs $(kubectl --kubeconfig=${KUBE_CONFIG} get pods -n ${NAMESPACE} | grep driver | tail -n 1 | cut -d' ' -f1)  -n ${NAMESPACE})
  echo "logs: $logs"
  # Check job output
  # Sample output
  # "Pi is roughly 3.13956232343"
  pi=$(kubectl --kubeconfig=${KUBE_CONFIG} logs $(kubectl --kubeconfig=${KUBE_CONFIG} get pods -n ${NAMESPACE} | grep driver | tail -n 1 | cut -d' ' -f1)  -n ${NAMESPACE} | grep 'Pi is roughly' | rev | cut -d' ' -f1 | rev | cut -c 1-3)
  echo -e "Spark Pi Job Output: \n ${pi}"

  aws --no-verify-ssl --endpoint-url "$S3_SERVER_URL" s3 ls "s3://dist-cache" 
  validate_pi_value $pi

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
  setup_user $SERVICE_ACCOUNT $NAMESPACE
}

cleanup_user() {
  EXIT_CODE=$1
  USERNAME=$2
  NAMESPACE=$3

  spark-client.service-account-registry delete --username=${USERNAME} --namespace ${NAMESPACE}

  rm -rf metastore_db/ derby.log

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

echo -e "##################################"
echo -e "SETUP TEST"
echo -e "##################################"

setup_tests

echo -e "##################################"
echo -e "TEST SELF SIGNED CERTIFICATE"
echo -e "##################################"

(setup_user_admin_context && test_spark_submit_custom_certificate && cleanup_user_success) || cleanup_user_failure

echo -e "##################################"
echo -e "END OF THE TEST!"
echo -e "##################################"

