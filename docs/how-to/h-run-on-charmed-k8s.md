## Launch Jobs on Charmed Kubernetes

### Setup

In order to setup a Charmed Kubernetes (assuming that you don't have a Kubernetes cluster yet), 
you need to install [Juju](https://juju.is/docs/olm/install-juju) first. 
Afterwards you can install Charmed Kubernetes by following the [Installation Guide](https://ubuntu.com/kubernetes/docs/install-manual) and then the [Setup Guide](https://ubuntu.com/kubernetes/docs/operations).

Once the Charmed Kubernetes cluster is up and running, you can enable and run Spark jobs 
like this.

First thing is to set up the `spark-client` snap.

```shell
$ sudo snap install spark-client
```
Then you need to set up a service account for Spark job submission. 
Let's create an account called ```spark``` in the ```default``` namespace.

```shell
$ spark-client.service-account-registry create --username spark --namespace default
```

> **Note** For `spark-submit`, `spark-shell` and `pyspark` to work correctly, make sure DNS is enabled.

### Spark Job Submission To Kubernetes Cluster

Let's use the ```spark-submit``` utility (that's part of the snap) to submit a ```Spark Pi``` job example.

```shell
$ spark-client.spark-submit --username spark --class org.apache.spark.examples.SparkPi local:///opt/spark/examples/jars/spark-examples_2.12-3.3.2.jar 100
```

### Spark Shell

To invoke a Spark shell, run the following command.

```shell
$ spark-client.spark-shell --username spark
```
### PySpark Shell

To launch a `pyspark` shell, run the following command.

```shell
$ spark-client.pyspark --username spark
```

> **Note** Make sure the namespace provided to spark-submit is valid and the service account provided belongs to that namespace. To keep it simple, use the setup-spark-k8s script to create the account.

***

* Previous: [Use the Spark Client Python API](/t/spark-client-snap-how-to-python-api/8958)
* Next: [Run on K8s pods](/t/spark-client-snap-how-to-run-on-k8s-in-a-pod/8961)