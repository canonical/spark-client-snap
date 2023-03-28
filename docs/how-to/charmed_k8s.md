## Launch Jobs on Charmed Kubernetes

### Setup

In order to setup a Charmed Kubernetes (if you don't already have one), 
you need to first install [Juju](https://juju.is/docs/olm/install-juju). 
After this, you can install a Charmed Kubernetes by following the install guide 
[here](https://ubuntu.com/kubernetes/docs/install-manual) and how to set it up [here](https://ubuntu.com/kubernetes/docs/operations).

Once the Charmed Kubernetes cluster is up and running, we can enable and run Spark jobs 
as outline in the following.

First thing is to set up the spark-client snap.

```shell
$ sudo snap install spark-client
```
Then we need to set up a service account for Spark job submission. 
Let's create a username ```spark``` in ```default``` namespace.

```shell
$ spark-client.service-account-registry create --username spark --namespace default
```

> **Note** For `spark-submit`, `spark-shell` and `pyspark` to work correctly, make sure DNS is enabled.

### Spark Job Submission To Kubernetes Cluster

Let's use the ```spark-submit``` utility in the snap to submit a ```Spark Pi``` job example.

```shell
$ spark-client.spark-submit --username spark --class org.apache.spark.examples.SparkPi local:///opt/spark/examples/jars/spark-examples_2.12-3.3.2.jar 100
```

### Spark Shell

To work with a Spark shell, run the following command.

```shell
$ spark-client.spark-shell --username spark
```
### PySpark Shell

To launch a pyspark shell, run the following command.

```shell
$ spark-client.pyspark --username spark
```

> **Note** Make sure the namespace provided to spark-submit is valid and the service account provided belongs to that namespace. To keep it simple, use the setup-spark-k8s script to create the account.
