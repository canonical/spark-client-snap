## Working with Charmed Kubernetes From within a pod

### Setup

After installing [Juju](https://juju.is/docs/olm/install-juju) and [Charmed Kubernetes](https://ubuntu.com/kubernetes/docs/install-manual) and [setting it up](https://ubuntu.com/kubernetes/docs/operations), let's discuss the steps to launch Spark jobs from within a pod in Charmed Kubernetes.

First thing, we launch a pod using Canonical's Charmed Spark container image.

Create a pod manifest ```shell-demo.yaml``` for use with Charmed Kubernetes, something like this

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: shell-demo
  namespace: spark-test-ns
spec:
  containers:
  - name: spark-client
    image: ghcr.io/canonical/charmed-spark:3.3.2-22.04_edge
    command: ["/bin/pebble", "run", "--hold"]
  serviceAccountName: spark-user
  hostNetwork: true
  dnsPolicy: Default
```

The pod can be created with
```shell
kubectl apply -f shell-demo.yaml
```

after that, one logs in with

```shell
$ kubectl exec --stdin --tty shell-demo -n spark-test-ns -- /bin/bash 
```

Now from within the pod, lets create the kubeconfig for use with spark-client. ```KUBECONFIG_CONTENTS_FROM_CHARMED_KUBERNETES``` will come from the first step executed outside the Charmed Kubernetes cluster pod. 

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

Let's use the ```spark-submit``` script packaged within the Charmed Spark container image to submit a ```Spark Pi``` job example to Charmed Kubernetes.

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
