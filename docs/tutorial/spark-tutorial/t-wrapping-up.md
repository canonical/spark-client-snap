## Wrapping Up

### Cleanup

Let's clean up the resources we created during the tutorial.

First of all, let's delete the juju models that we created.

```bash
juju destroy-model -y spark-streaming --force --no-wait
juju destroy-model -y history-server --force --no-wait
juju destroy-model -y cos --force --no-wait
```

Now let's delete the K8s namespaces that were created. This will automatically clean up K8s resources within that namespace.
```bash
kubectl delete namespace cos
kubectl delete namespace history-server
kubectl delete namespace spark-streaming
kubectl delete namespace spark
```

Finally, the S3 bucket that was created can be removed using the AWS CLI as:

```bash
aws s3api delete-bucket --bucket spark-tutorial
```


### Further Reading

This tutorial covers running Charmed Spark locally using MicroK8s. Running Charmed Spark in MicroK8s locally is bounded by the amount of resources available locally. It is also possible to run Charmed Spark solution on AWS EKS. You can go through a nice demonstration of running Charmed Spark on top of AWS EkS at the [2023 Operator Day demo](https://github.com/deusebio/operator-day-2023-charmed-spark).
