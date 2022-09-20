# Description
The spark-client snap includes the scripts spark-submit, spark-shell, pyspark and other tools for managing Apache Spark jobs.

# Install
sudo snap install spark-client

# Usage

## Submit Spark Job
spark-client.spark-submit --master <K8S_MASTER_URL> --deploy-mode cluster --name <APP_NAME> --conf spark.kubernetes.authenticate.submission.caCertFile=<CA_CRT_FILE_PATH> --conf spark.kubernetes.authenticate.submission.oauthTokenFile=<TOKEN_FILE_PATH> --conf spark.executor.instances=<NUM_INSTANCES> --conf spark.kubernetes.container.image=<SPARK_K8S_CONTAINER_IMAGE_TAG> --conf spark.kubernetes.container.image.pullPolicy=Always --conf spark.kubernetes.authenticate.driver.serviceAccountName=<K8S_SERVICE_ACCOUNT_FOR_SPARK> --conf spark.hadoop.fs.s3a.access.key=<S3_ACCESS_KEY> --conf spark.hadoop.fs.s3a.secret.key=<S3_SECRET_KEY> --conf spark.hadoop.fs.s3a.aws.credentials.provider=<S3A_CREDENTIALS_PROVIDER_CLASS> --conf spark.hadoop.fs.s3a.endpoint=<S3A_ENDPOINT> --conf spark.hadoop.fs.s3a.connection.ssl.enabled=false  --conf spark.hadoop.fs.s3a.path.style.access=true --conf spark.eventLog.enabled=false <S3_PATH_FOR_CODE_PY_FILE>

## Interactive Spark Shell 
spark-client.spark-shell

## Interactive PySpark Shell
spark-client.pyspark

# Contributing

Please see the [Juju SDK docs](https://juju.is/docs/sdk) for guidelines on enhancements to this
snap following best practice guidelines, and for developer guidance.

