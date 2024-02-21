# Wrapping Up

## Cleanup

Let's clean up the resources we created during the tutorial.

First of all, let's destroy the Juju controller we boostrapped for the tutorial.

```bash
juju destroy-controller --destroy-all-models --destroy-storage --force spark-tutorial
```

The `spark-streaming`, `history-server` and `cos` namespaces are automatically deleted when the corresponding models are destroyed. Let's also delete the `spark` K8s namespace. This will automatically clean up K8s resources within the namespace.

```bash
kubectl delete namespace cos
kubectl delete namespace history-server
kubectl delete namespace spark-streaming
kubectl delete namespace spark
```

Finally, the S3 bucket that was created can be removed using the AWS CLI as:

```bash
aws s3 rb  s3://spark-tutorial --force
```


## Going Further

Parts of this tutorial were originally covered in a talk of the Ubuntu Summit 2023, recording of which is available [here on YouTube](https://www.youtube.com/watch?v=nu1ll7VRqbI).

This tutorial covers running Charmed Spark locally using MicroK8s. Running Charmed Spark in MicroK8s locally is bounded by the amount of resources available locally. For a more robust deployment, it is also possible to run Charmed Spark solution on AWS EKS. You can go through a nice demonstration of running Charmed Spark on top of AWS EkS at the [2023 Operator Day demo](https://github.com/deusebio/operator-day-2023-charmed-spark).
