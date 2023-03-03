## Working with Charmed Kubernetes From within a pod

### Setup

Assuming you have juju and charmed kubernetes already setup, let's discuss the steps to launch Spark jobs from within a pod in charmed kubernetes.

First thing is to get the kubeconfig of the charmed kubernetes setup for use with the spark-client scripts within the pod that we will launch next.

```shell
$ juju scp kubernetes-control-plane/0:config ./KUBECONFIG_CONTENTS_FROM_CHARMED_KUBERNETES
```

Now we launch the pod using Canonical Data Plarform's OCI image for Apache Spark.

```shell
$ kubectl run -i --tty charmed-spark --image=docker.io/dataplatformoci/spark:3.3.2 --command -- /bin/bash
```

Within the pod, lets create the kubeconfig for use with spark-client. ```KUBECONFIG_CONTENTS_FROM_CHARMED_KUBERNETES``` will come from the first step executed outside the charmed kubernetes cluster pod. 

```shell
$ mkdir ~/.kube
$ cat > ~/.kube/config << EOF
KUBECONFIG_CONTENTS_FROM_CHARMED_KUBERNETES
EOF
```

Then we need to set up a service account for Spark job submission. Let's create a username ```spark``` in ```default``` namespace.

```shell
$ python3 -m spark_client.cli.service-account-registry create --username spark
```

### Spark Job Submission To Kubernetes Cluster

Let's use the ```spark-submit``` script packaged within the OCI image to submit a ```Spark Pi``` job example to charmed kubernetes.

```shell
$ python3 -m spark_client.cli.spark-submit --username spark --class org.apache.spark.examples.SparkPi local:///opt/spark/examples/jars/spark-examples_2.12-3.3.2.jar 100
```
Or
```shell
$ spark-client.spark-submit --username spark --class org.apache.spark.examples.SparkPi local:///opt/spark/examples/jars/spark-examples_2.12-3.3.2.jar 100
```

### Spark Shell

To work with a Spark shell, run the following command within the pod.

```shell
$ python3 -m spark_client.cli.spark-shell --username spark
```
Or
```shell
$ spark-client.spark-shell --username spark
```

### PySpark Shell

To launch a pyspark shell, run the following command within the pod.

```shell
$ python3 -m spark_client.cli.pyspark --username spark
```
Or
```shell
$ spark-client.pyspark --username spark
```
