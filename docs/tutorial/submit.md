## Spark Job Submission To Kubernetes Cluster
The spark-client snaps ships with the Apache Spark's spark-submit utility for Kubernetes distribution.

To submit Spark jobs to a Kubernetes cluster using the spark-submit utility, please first follow the [setup](/docs/tutorial/service_account_registry.md/setup.md) instructions to create the Kubernetes service account.

### Validating Setup with an Example Spark Job

Once you have set up the service account successfully, please execute the following commands to test the validity of your setup.

Here we are launching the Pi example bundled with Apache Spark.

```bash
SPARK_EXAMPLES_JAR_NAME='spark-examples_2.12-3.4.0-SNAPSHOT.jar'
        
spark-client.spark-submit \
--deploy-mode cluster \
--class org.apache.spark.examples.SparkPi \
local:///opt/spark/examples/jars/$SPARK_EXAMPLES_JAR_NAME 100
```

### Adding Big Data to the mix

Once the setup is validated, it's time to test out with a real big data workload. Here we assume that 
* the input data is placed in S3
* the code i.e. python script is also placed in S3 and reads from the provided input location.
* the destination directory for output is also in S3

To launch the Spark job in this scenario, make sure the S3 access related information is available to you. Then execute the following commands.

```bash
APP_NAME='my-pyspark-app'
NUM_INSTANCES=5
NAMESPACE=<namespace for your spark K8s service account>
K8S_SERVICE_ACCOUNT_FOR_SPARK=<your spark K8s service account>

S3_ACCESS_KEY=<your s3 access key>
S3_SECRET_KEY=<your s3 secret key>
S3A_CREDENTIALS_PROVIDER_CLASS=org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider
S3A_ENDPOINT=<your s3 endpoint>
S3A_SSL_ENABLED=false
S3_PATH_FOR_CODE_PY_FILE=</path/to/your/python_script_in_S3.py>

spark-client.spark-submit --deploy-mode cluster --name $APP_NAME \
--conf spark.executor.instances=$NUM_INSTANCES \
--conf spark.kubernetes.namespace=$NAMESPACE \
--conf spark.kubernetes.authenticate.driver.serviceAccountName=$K8S_SERVICE_ACCOUNT_FOR_SPARK \
--conf spark.hadoop.fs.s3a.access.key=$S3_ACCESS_KEY \
--conf spark.hadoop.fs.s3a.secret.key=$S3_SECRET_KEY \
--conf spark.hadoop.fs.s3a.aws.credentials.provider=$S3A_CREDENTIALS_PROVIDER_CLASS \
--conf spark.hadoop.fs.s3a.endpoint=$S3A_ENDPOINT \
--conf spark.hadoop.fs.s3a.connection.ssl.enabled=$S3A_SSL_ENABLED \
--conf spark.hadoop.fs.s3a.path.style.access=true \
$S3_PATH_FOR_CODE_PY_FILE
```

These configuration parameters and others can be provided via a ```spark-defaults.conf``` config file placed as described here.
* Either setting ***SPARK_HOME*** and placing the config as ```$SPARK_HOME/conf/spark-defaults.conf```. Or
* Overriding ***SPARK_CONF_DIR*** and placing the config as ```$SPARK_CONF_DIR/spark-defaults.conf``` Or
* Overriding ***SPARK_CLIENT_ENV_CONF*** to point to the config file to use

For example, with a ```spark-defaults.conf``` similar to provided below for reference, we can make the submit command much simpler.

```
spark.master=k8s://https://<MY_K8S_CONTROL_PLANE_HOST_IP>:<MY_K8S_CONTROL_PLANE_PORT>
spark.kubernetes.context=<PREFERRED_K8S_CONTEXT>
spark.app.name=<SPARK_APP_NAME>
spark.executor.instances=<NUM_INSTANCES>
spark.kubernetes.container.image=<CONTAINER_IMAGE_PUBLIC_REF>
spark.kubernetes.container.image.pullPolicy=<PULL_POLICY>
spark.kubernetes.namespace=<NAMESPACE_OF_PREFERRED_SERVICEACCOUNT>
spark.kubernetes.authenticate.driver.serviceAccountName=<PREFERRED_SERVICEACCOUNT>
spark.eventLog.enabled=false
spark.hadoop.fs.s3a.access.key=<S3_ACCESS_KEY>
spark.hadoop.fs.s3a.secret.key=s<S3_SECRET_KEY>
spark.hadoop.fs.s3a.aws.credentials.provider=org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider
spark.hadoop.fs.s3a.endpoint=<S3_ENDPOINT_URI>
spark.hadoop.fs.s3a.connection.ssl.enabled=false
spark.hadoop.fs.s3a.path.style.access=true
```

With a valid configuration file placed appropriately, the submit command becomes quite simple.

```bash
spark-client.spark-submit --deploy-mode cluster $S3_PATH_FOR_CODE_PY_FILE
```
The configuration defaults can be overriden as well in the submit command with ```--conf``` arguments as illustrated previously.