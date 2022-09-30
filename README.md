# Description
This repository hosts the source for ```spark-client``` snap. 
The ```spark-client``` snap includes the scripts spark-submit, spark-shell, pyspark and other tools for managing ```Apache Spark``` jobs for ```Kubernetes```.

# Installation and setup for Spark on Kubernetes
Install the spark client snap.

```bash
sudo snap install spark-client
```

Setup kubernetes service account for use with Spark client. Default namespace where user is created is ```default```.

```bash
spark-client.setup-spark-k8s service-account --kubeconfig kubeconfig-file-name --cluster cluster-name-in-kubeconfig account-name [namespace]
```

Enable access for default kubeconfig file ($HOME/.kube/config)

```bash
snap connect spark-client:enable-kubeconfig-access
```

Dump out the CA certificate on screen for use with Spark client. 


```bash
spark-client.setup-spark-k8s get-ca-cert --kubeconfig kubeconfig-file-name --cluster cluster-name-in-kubeconfig > ca.crt
```

Or navigate the set of clusters in the default kubeconfig interactively to select the certificate of interest. 
Default kubeconfig file is $HOME/.kube/config

```bash
spark-client.setup-spark-k8s get-ca-cert
```

Save the CA certificate output in a file to be used with Spark client's spark-submit command. Next, save the Outh Token for the service account to a file for use with Spark client. 

```bash
spark-client.setup-spark-k8s get-token --kubeconfig kubeconfig-file-name --cluster cluster-name-in-kubeconfig account-name [namespace] > token
```

# Usage

## Submit Spark Job
Canonical's Charmed Data Platform solution for Apache Spark runs Spark jobs on your Kubernetes cluster. 
You can get started right away with [Microk8s](https://microk8s.io) - the mightiest tiny Kubernetes distro around! 
You can install MicroK8s on your Ubuntu laptop, workstation, or nodes in your workgroup or server cluster with 
just one command - `snap install microk8s --classic`. Learn more at [microk8s.io](https://microk8s.io)

To submit a Spark job to your Kubernetes cluster, you would require:
- The ```Kubernetes Master or Control Plane URL```. Please use ```kubectl cluster-info``` to figure that out
- The ```Spark Container Image``` to be used for job execution. 
- The ```K8S Service Account``` created during the installation phase or use if you already have one.
  - Make sure you do provide the correct ```K8S namespace``` for the service account as well
- The ```CA certificate``` extracted during the installation phase. You will need the file name with CA cert contents.
- The ```S3 credentials and Endpoint``` need to be provided in case the data (and/or code) is placed in S3. 


Please execute the following commands to submit your Spark job in cluster mode to Kubernetes.

```bash
K8S_MASTER_URL=<your K8s API server URL>
APP_NAME=my_spark_app
CA_CRT_FILE_PATH=</path/to/your/K8s API/CA Cert>
OAUTH_TOKEN_FILE_PATH=</path/to/your/K8s API/Oauth Token>
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
 --conf spark.kubernetes.authenticate.submission.oauthTokenFile=$OAUTH_TOKEN_FILE_PATH \
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
If you intend to use spark-shell, please enable the scala history file write access.

```bash
snap connect spark-client:enable-scala-history
```

Let's quickly test out our spark-shell setup with official Pi example from the Spark distribution.

```bash
$ spark-client.spark-shell
....
....
Spark session available as 'spark'.
Welcome to
      ____              __
     / __/__  ___ _____/ /__
    _\ \/ _ \/ _ `/ __/  '_/
   /___/ .__/\_,_/_/ /_/\_\   version 3.3.0
      /_/
....
....
scala> import scala.math.random
scala> val slices = 1000
scala> val n = math.min(100000L * slices, Int.MaxValue).toInt
scala> val count = spark.sparkContext.parallelize(1 until n, slices).map { i => val x = random * 2 - 1; val y = random * 2 - 1;  if (x*x + y*y <= 1) 1 else 0;}.reduce(_ + _)
scala> println(s"Pi is roughly ${4.0 * count / (n - 1)}")
```

## Interactive PySpark Shell

Let's try out the same official Pi example using pyspark

```bash
$ spark-client.pyspark
....
....
Welcome to
      ____              __
     / __/__  ___ _____/ /__
    _\ \/ _ \/ _ `/ __/  '_/
   /__ / .__/\_,_/_/ /_/\_\   version 3.3.0
      /_/
....
....
>>> from random import random
>>> from operator import add
>>> partitions = 1000
>>> n = 100000 * partitions
>>> def f(_: int) -> float:
...     x = random() * 2 - 1
...     y = random() * 2 - 1
...     return 1 if x ** 2 + y ** 2 <= 1 else 0
...
>>> count = spark.sparkContext.parallelize(range(1, n + 1), partitions).map(f).reduce(add)
>>> print("Pi is roughly %f" % (4.0 * count / n))
```

# Common Gotchas!
- For spark-submit to work correctly, make sure DNS is enabled.
  - For example, if you are working with ```microk8s```, please run ```microk8s enable dns``` before submitting the spark job
- Double-check the K8S Master url, it has a prefix something like k8s://https://
- In case executor pods fail to schedule due to insufficient CPU resources, make [fractional](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#resource-units-in-kubernetes) CPU requests
- Don't forget to enable default kubeconfig access for the snap, otherwise it will complain not able to find kubeconfig file even after providing the valid default kubeconfig file
- Make sure the namespace provided to spark-submit is valid and the service account provided belongs to that namespace
- This a strictly confined snap, so avoid having the certificate and the token files in special locations like /tmp etc. Home directory would be best to keep such files.