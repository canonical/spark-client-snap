## Working with Charmed Kubernetes

### Setup

After installing [Juju](https://juju.is/docs/olm/install-juju) and [Charmed Kubernetes](https://ubuntu.com/kubernetes/docs/install-manual) and [setting it up](https://ubuntu.com/kubernetes/docs/operations), let's discuss the steps to launch Spark jobs against the Charmed Kubernetes setup.

First thing is to set up the spark-client snap.

```shell
$ sudo snap install spark-client
```
Then we need to set up a service account for Spark job submission. Let's create a username ```spark``` in ```default``` namespace.

```shell
$ spark-client.service-account-registry create --username spark
```


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