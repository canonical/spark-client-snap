### Spark Job Submission To Kubernetes Cluster
The spark-client snaps ships with the Apache Spark's spark-submit utility for Kubernetes distribution.

To submit Spark jobs to a Kubernetes cluster using the spark-submit utility, we would need the following.

* The ***Kubernetes Master*** or ***Control Plane URL***. 
  * Please use ```kubectl cluster-info``` to figure out the control plan URL
  * Make sure to add ```k8s://``` prefix to the URL for use for Spark job submission
* The ***Spark Container Image*** to be used for job execution.
  * This is the OCI or Docker image for Spark which the spark-submit utility will use to launch both driver and executor pods once the job is submitted to the Kubernetes cluster
* The ***Kubernetes Service Account*** which, if not already in place, we can create using the setup utility bundled with the spark-client snap.
  * While creating and using the service account, the ***namespace*** of the account matters. Please follow the setup instructions to set it up properly.
* The ***CA certificate*** which we can extract using the setup utility bundled with the snap. You will need the file with CA cert contents later.
* The ***OAuth Token*** which can be generated using the setup utility. Provide it as a file to the spark-submit command.
* The ***S3 credentials and Endpoint*** need to be provided in case the data (and/or code) is placed in S3

Please follow the setup instructions to create the Kubernetes service account, fetch the CA certificate into a file and generate 
the OAuth token before proceeding further.

#### Validating Setup with an Example Spark Job

Once you have the above details handy, please execute the following commands to test the validity of your setup.
Here we are launching the Pi example bundled with Apache Spark.

```bash
K8S_MASTER_URL=k8s://https://<your K8s API server URL>
APP_NAME='spark-pi'
CA_CRT_FILE='</path/to/your/K8s API/CA Cert>'
OAUTH_TOKEN_FILE='</path/to/your/K8s API/Oauth Token>'
NUM_INSTANCES=5
SPARK_K8S_CONTAINER_IMAGE_TAG=<your spark container image>
PULL_POLICY=Always
NAMESPACE=<namespace for your spark K8s service account>
K8S_SERVICE_ACCOUNT_FOR_SPARK=<your spark K8s service account>
SPARK_EXAMPLES_JAR_NAME='spark-examples_2.12-3.4.0-SNAPSHOT.jar'
EVENT_LOG_ENABLED=false
        
spark-client.spark-submit \
--master $K8S_MASTER_URL \
--deploy-mode cluster \
--name $APP_NAME \
--conf spark.kubernetes.authenticate.submission.caCertFile=$CA_CRT_FILE \
--conf spark.kubernetes.authenticate.submission.oauthTokenFile=$OAUTH_TOKEN_FILE \
--conf spark.executor.instances=$NUM_INSTANCES \
--conf spark.kubernetes.container.image=$SPARK_K8S_CONTAINER_IMAGE_TAG \
--conf spark.kubernetes.container.image.pullPolicy=$PULL_POLICY \
--conf spark.kubernetes.namespace=$NAMESPACE \
--conf spark.kubernetes.authenticate.driver.serviceAccountName=K8S_SERVICE_ACCOUNT_FOR_SPARK \
--conf spark.eventLog.enabled=$EVENT_LOG_ENABLED \
--class org.apache.spark.examples.SparkPi \
local:///opt/spark/examples/jars/$SPARK_EXAMPLES_JAR_NAME 100
```

#### Adding Big Data to the mix

Once the setup is validated, it's time to test out with a real big data workload. Here we assume that 
* the input data is placed in S3
* the code i.e. python script is also placed in S3 and reads from the provided input location.
* the destination directory for output is also in S3

To launch the Spark job in this scenario, make sure the S3 access related information is available to you. Then execute the following commands.

```bash
K8S_MASTER_URL=k8s://https://<your K8s API server URL>
APP_NAME='my-pyspark-app'
CA_CRT_FILE='</path/to/your/K8s API/CA Cert>'
OAUTH_TOKEN_FILE='</path/to/your/K8s API/Oauth Token>'
NUM_INSTANCES=5
SPARK_K8S_CONTAINER_IMAGE_TAG=<your spark container image>
PULL_POLICY=Always
NAMESPACE=<namespace for your spark K8s service account>
K8S_SERVICE_ACCOUNT_FOR_SPARK=<your spark K8s service account>
EVENT_LOG_ENABLED=false

S3_ACCESS_KEY=<your s3 access key>
S3_SECRET_KEY=<your s3 secret key>
S3A_CREDENTIALS_PROVIDER_CLASS=org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider
S3A_ENDPOINT=<your s3 endpoint>
S3A_SSL_ENABLED=false
EVENT_LOG_ENABLED=false
S3_PATH_FOR_CODE_PY_FILE=</path/to/your/python_script_in_S3.py>

spark-client.spark-submit --master $K8S_MASTER_URL \
--deploy-mode cluster --name $APP_NAME \
--conf spark.kubernetes.authenticate.submission.caCertFile=$CA_CRT_FILE \
--conf spark.kubernetes.authenticate.submission.oauthTokenFile=$OAUTH_TOKEN_FILE \
--conf spark.executor.instances=$NUM_INSTANCES \
--conf spark.kubernetes.container.image=$SPARK_K8S_CONTAINER_IMAGE_TAG \
--conf spark.kubernetes.container.image.pullPolicy=$PULL_POLICY \
--conf spark.kubernetes.namespace=$NAMESPACE \
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