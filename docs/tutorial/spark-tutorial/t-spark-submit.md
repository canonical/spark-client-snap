The Charmed Spark solution offers several ways to interact with the Spark cluster. They are:
1. Using Spark Submit
2. Using Spark Shell

In this section, we'll run a sample job using `spark-submit` CLI command provided with `spark-client` snap. The sample Python program that we are going to run have already been uploaded to S3 in the earlier section. Also, the sample data file has also been uploaded to `data/data.csv.gz` in the same S3 bucket. Run the Python script with `spark-submit` as follows:

```bash
spark-client.spark-submit \
  --username spark --namespace spark \
  --deploy-mode cluster \
  s3a://$S3_BUCKET/scripts/stock_country_report.py \
    --input  s3a://$S3_BUCKET/data/data.csv.gz \
    --output s3a://$S3_BUCKET/data/output_report_microk8s
```

The variable `$S3_BUCKET` has been set in the earlier section to the MinIO bucket URL.

As the command gets executed, open a new shell and see newly created pods in the `spark` namespace:

```bash
kubectl get pods -n spark
```

You can see that a new driver pod and a couple of executor pods get spawned and they start processing the data. Once the job is completed, the driver as well as executor pods are transitioned to Completed state.

To see the result of the job that was executed before, first find the pod identifier of the driver pod, and then use `kubectl logs` to view logs for that pod.

```bash
kubectl get pods -n spark # Note the ID of the driver pod.

kubectl logs <pod_identier> -n spark
```

In the logs, you can see a line that begins with "The value of Pi is roughly ...". This value was computed in Spark.

In the next section, we will see how we can interact with Spark using interactive shell.