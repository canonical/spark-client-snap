## Wrapping Up

### Cleanup

Let's clean up the resources we created during the tutorial.

First of all, let's delete the pods in the `spark` namespace.

```bash
kubectl delete pod --field-selector=status.phase==Succeeded -n spark
kubectl delete pod --field-selector=status.phase==Failed -n spark
```

Now let's delete the Juju models that were created during the tutorial.

```bash
juju destroy-model -y spark-streaming --force --no-wait
juju destroy-model -y history-server --force --no-wait
juju destroy-model -y cos --force --no-wait
```

Finally, the S3 bucket that was created can be removed using the `spark_bucket.py` script that comes with the repository.

```python
python scripts/spark_bucket.py \
  --action delete \
  --access-key $AWS_ACCESS_KEY \
  --secret-key $AWS_SECRET_KEY \
  --endpoint $AWS_S3_ENDPOINT \
  --bucket $AWS_S3_BUCKET 
```

### Further Reading

The video demonstration of this tutorial during Ubuntu Summit 2023 can be found (here)[https://www.youtube.com/watch?v=nu1ll7VRqbI]. The files used in the demo can be found in this (repository)[https://github.com/welpaolo/ubuntu-summit-2023].

Running Charmed Spark in MicroK8s locally is bounded by the amount of resources available locally. It is also possible to run Charmed Spark solution on AWS EKS. There's a nice demonstration of running Charmed Spark on top of AWS EKS at the [2023 Operator Day](https://github.com/deusebio/operator-day-2023-charmed-spark).