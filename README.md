# Description
The spark-client snap includes the scripts spark-submit, spark-shell, pyspark and other tools for managing Apache Spark jobs.

# Install
sudo snap install spark-client

# Usage

## Submit Spark Job
Canonical's Charmed Data Platform solution for Apache Spark runs Spark jobs on your Kubernetes cluster. You can get started right away with [Microk8s](https://microk8s.io) - the mightiest tiny Kubernetes distro around! You can install MicroK8s on your Ubuntu laptop, workstation, or nodes in your workgroup or server cluster with just one command - `snap install microk8s --classic`. Learn more at [microk8s.io](https://microk8s.io)

To submit a Spark job to your Kubernetes cluster, run the following commands:

```bash
K8S_MASTER_URL=<your K8s API server URL>
APP_NAME=my_spark_app
CA_CRT_FILE_PATH=</path/to/your/K8s API/CA Cert>
NUM_INSTANCES=5
SPARK_K8S_CONTAINER_IMAGE_TAG=<your spark container image>
PULL_POLICY=Always
K8S_SERVICE_ACCOUNT_FOR_SPARK=<your spark K8s service account>
S3_ACCESS_KEY=<your s3 access key>
S3_SECRET_KEY=<your s3 secret key>
S3A_CREDENTIALS_PROVIDER_CLASS=org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider
S3A_ENDPOINT=<your s3 endpoint>
S3A_SSL_ENABLED=false
EVENT_LOG_ENABLED=false
S3_PATH_FOR_CODE_PY_FILE=</path/to/your/python_script.py>

spark-client.spark-submit --master $K8S_MASTER_URL \
 --deploy-mode cluster --name $APP_NAME \
 --conf spark.kubernetes.authenticate.submission.caCertFile=$CA_CRT_FILE_PATH \
 --conf spark.executor.instances=$NUM_INSTANCES \
 --conf spark.kubernetes.container.image=$SPARK_K8S_CONTAINER_IMAGE_TAG \
 --conf spark.kubernetes.container.image.pullPolicy=$PULL_POLICY \
 --conf spark.kubernetes.authenticate.driver.serviceAccountName=$K8S_SERVICE_ACCOUNT_FOR_SPARK \
 --conf spark.hadoop.fs.s3a.access.key=$S3_ACCESS_KEY \
 --conf spark.hadoop.fs.s3a.secret.key=$S3_SECRET_KEY \
 --conf spark.hadoop.fs.s3a.aws.credentials.provider=$S3A_CREDENTIALS_PROVIDER_CLASS \
 --conf spark.hadoop.fs.s3a.endpoint=$S3A_ENDPOINT \
 --conf spark.hadoop.fs.s3a.connection.ssl.enabled=$S3A_SSL_ENABLED \
 --conf spark.hadoop.fs.s3a.path.style.access=true \
 --conf spark.eventLog.enabled=$EVENT_LOG_ENABLED \
 $S3_PATH_FOR_CODE_PY_FILE
```

## Interactive Spark Shell 
spark-client.spark-shell

## Interactive PySpark Shell
spark-client.pyspark
