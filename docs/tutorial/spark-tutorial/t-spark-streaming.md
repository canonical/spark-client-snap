## Streaming workloads with Charmed Spark

Spark comes with a built-in support for streaming workloads and Charmed Spark takes it even a step further by making it easy to integrate with streaming platform like Kafka.

In this tutorial, we are going to use `juju` to deploy a Kafka setup, where a simple Juju charm will generate events to Kafka, and a Spark job we submit will consume these in real time to process it. We have already installed `juju` in previous sections.

First of all, let's start by creating a fresh `juju` model to be used as a workspace for this streaming tutorial.

```bash
juju add-model spark-streaming
```

Now, let's deploy Zookeeper and Kafka using the `zookeeper-k8s` and `kafka-k8s` charms. Single units of these charm should be enough.

```bash
juju deploy zookeeper-k8s --series=jammy --channel=edge
juju deploy kafka-k8s --series=jammy --channel=edge
```

The current status of the Juju model can be seen using the command:
```bash
juju status --watch 1s
```

Wait until the two charms are deployed and are in active and idle state. Now, for Kafka to be able to connect to Zookeeper, we need to integrate these two charms. Run the following command to integrate them.

```bash
juju integrate kafka-k8s zookeeper-k8s
```

For us to experiment with the streaming feature, we would want some sample streaming data to be generated continuously in real time. For that, we can use the `kafka-test-app` charm as a producer of events. Deploy the charm, and integrate it with `kafka-k8s` so that it is able to write messages to Kafka.

```bash
juju deploy kafka-test-app --series=jammy --channel=edge --config role=producer --config topic_name=spark-streaming-store --config num_messages=1000

juju integrate kafka-test-app kafka-k8s
```

Now the messages will be generated and written to Kafka. But in order to consume these messages, we need the credentials to establish the connection between Spark and Kafka. For the retreival of credentials, we are going to use the `data-integrator` charm. Deploy the charm and integrate it with `kafka-k8s` with the following commands:

```bash
juju deploy data-integrator --series=jammy --channel=edge --config extra-user-roles=consumer,admin --config topic-name=spark-streaming-store

juju integrate data-integrator kafka-k8s 
```

Once the charm is deployed and integrated, we can get the credentials to connect to Kafka by running the `get-credentials` action exposed by the `data-integrator` charm.

```bash
juju run-action data-integrator/0 get-credentials --wait 
```

You can view the credentials such as `username` and `password` in the output. These can be stored as variables using the following commands:

```bash
USERNAME=$(juju run data-integrator/0 get-credentials --format=json | yq .data-integrator/0.results.kafka.username)
PASSWORD=$(juju run data-integrator/0 get-credentials --format=json | yq .data-integrator/0.results.kafka.password)
```
<!-- 
Now, let's create a new Kubernetes service account for us to use for streaming example. As earlier, we will use `spark-client` snap to create the service account.

```bash
kubectl create namespace spark-streaming

spark-client.service-account-registry create \
  --username spark --namespace spark-streaming \
  --properties-file ./confs/s3.conf
``` -->

Now, we can submit a job that uses the Spark streaming APIs using `spark-client.spark-submit`. The Python script named `spark_streaming.py` is available in our local MinIO S3 bucket which we created in the earlier section. The script looks like the following:

```python
import argparse
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, col
from json import loads

spark = SparkSession.builder.getOrCreate()

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("--kafka-username", "-u",
                  help="The username to authenticate to Kafka",
                  required=True)
  parser.add_argument("--kafka-password", "-p",
                  help="The password to authenticate to Kafka",
                    required=True)

  args = parser.parse_args()
  username=args.kafka_username
  password=args.kafka_password
  lines = spark.readStream \
          .format("kafka") \
          .option("kafka.bootstrap.servers", "kafka-k8s-0.kafka-k8s-endpoints:9092") \
          .option("kafka.sasl.mechanism", "SCRAM-SHA-512") \
          .option("kafka.security.protocol", "SASL_PLAINTEXT") \
          .option("kafka.sasl.jaas.config", f'org.apache.kafka.common.security.scram.ScramLoginModule required username="{username}" password="{password}";') \
          .option("subscribe", "spark-streaming-store") \
          .option("includeHeaders", "true") \
          .load()

  get_origin = udf(lambda x: loads(x)["origin"])
  w_count = lines.withColumn("origin", get_origin(col("value"))).select("origin")\
          .groupBy("origin")\
          .count()
  query = w_count \
    .writeStream \
    .outputMode("complete") \
    .format("console") \
    .start()

  query.awaitTermination()

```

Let's submit this to the Spark cluster and run it:

```bash
spark-client.spark-submit \
  --username spark --namespace spark \
  --deploy-mode cluster \
  --conf spark.executor.instances=1 \
  --conf spark.jars.ivy=/tmp \
  --packages org.apache.spark:spark-streaming-kafka-0-10_2.12:3.4.1,org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1 \
  s3a://$S3_BUCKET/scripts/streaming_example.py \
    --kafka-username  $USERNAME \
    --kafka-password $PASSWORD
```

You can view the Driver and Executor pods getting spawned and running upon running `kubectl get pods -n spark-streaming` command in a new shell. Note the pod itentifier for the driver pod. We'll use it to view the pod logs.

Run the following command to view the driver pod logs:

```bash
kubectl logs <pod_identiferi> -n spark-streaming
```

If you repeatedly check the logs, you can see that new logs are appended every 10 seconds. In the logs, you can also view the word counts in the streaming data. The streaming data will be processed by Spark and written to pod logs continuously until the job is stopped.