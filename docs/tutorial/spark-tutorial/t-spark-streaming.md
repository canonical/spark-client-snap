## Streaming workloads with Charmed Spark

Spark comes with a built-in support for streaming workloads and Charmed Spark takes it even a step further by making it easy to integrate with streaming platforms like Kafka.

In this section, we are going to generate some streaming data in Kafka, and then process this stream of data in Spark. We are going to use `juju` to deploy a Kafka setup, where a Juju charm will generate events to Kafka, and a Spark job will consume these in real time to process it. We have already installed and configured `juju` in earlier sections.

First of all, let's start by creating a fresh `juju` model to be used as an experimental workspace.

```bash
juju add-model spark-streaming
```

When you add a Juju model, a Kubernetes namespace of the same name is created automatically. You can verify that by running `kubectl get namespaces` and there you should see a namespace named `spark-streaming`.

The service account `spark` we created in the earlier section is in `spark` namespace. Let's create a similar service account but now in the `spark-streaming` namespace. We can copy the existing config options from the old service account to the new service account.

```bash
# Get config from old service account and store in a file
spark-client.service-account-registry get-config \
  --username spark --namespace spark > properties.conf

# Create a new service account and load configurations from the file
spark-client.service-account-registry get-config \
  --username spark --namespace spark-streaming \
  --properties-file properties.conf
```

Now, let's create a minimal Kafka and Zookeeper setup. This can be done both easily and quickly using `zookeeper-k8s` and `kafka-k8s` charms. Single units of these charms running in our model should be enough.

```bash
# Deploy Zookeper
juju deploy zookeeper-k8s --series=jammy --channel=edge

# Deploy Kafka
juju deploy kafka-k8s --series=jammy --channel=edge
```

Once installed, you can shee the current status of the Juju model with the following command:
```bash
juju status --watch 1s
```

This command periodically refreshes status of Juju model and then present the data in the console. Once all the charms have been deployed (you may need to wait some time), the output should appear similar to the following:

```
Model            Controller      Cloud/Region        Version  SLA          Timestamp
spark-streaming  spark-tutorial  microk8s/localhost  3.1.7    unsupported  10:09:40Z

App            Version  Status   Scale  Charm          Channel  Rev  Address         Exposed  Message
kafka-k8s               waiting      1  kafka-k8s      3/edge    47  10.152.183.242  no       installing agent
zookeeper-k8s           active       1  zookeeper-k8s  3/edge    42  10.152.183.87   no       

Unit              Workload  Agent  Address      Ports  Message
kafka-k8s/0*      blocked   idle   10.1.29.184         missing required zookeeper relation
zookeeper-k8s/0*  active    idle   10.1.29.182         
```

The `kafka-k8s/0` unit is blocked because we have not integrated Kafka with Zookeeper yet. We can do that using:

```bash
juju integrate kafka-k8s zookeeper-k8s
```

After the integration, `juju status` should have an output similar to the following:

```
Model            Controller      Cloud/Region        Version  SLA          Timestamp
spark-streaming  spark-tutorial  microk8s/localhost  3.1.7    unsupported  10:13:55Z

App            Version  Status  Scale  Charm          Channel  Rev  Address         Exposed  Message
kafka-k8s               active      1  kafka-k8s      3/edge    47  10.152.183.242  no       
zookeeper-k8s           active      1  zookeeper-k8s  3/edge    42  10.152.183.87   no       

Unit              Workload  Agent  Address      Ports  Message
kafka-k8s/0*      active    idle   10.1.29.184         
zookeeper-k8s/0*  active    idle   10.1.29.182 
```

As you can see, both Kafka and Zookeeper charms are in "active" status.

For us to experiment with the streaming feature, we would want some sample streaming data to be generated in Kafka continuously in real time. For that, we can use the `kafka-test-app` charm as a producer of events. Let's deploy the charm, and integrate it with `kafka-k8s` so that it is able to write messages to Kafka.

```bash
juju deploy kafka-test-app --series=jammy --channel=edge --config role=producer --config topic_name=spark-streaming-store --config num_messages=1000

juju integrate kafka-test-app kafka-k8s
```

Once this integration is complete, `juju status` should appear something similar to:

```
Model            Controller      Cloud/Region        Version  SLA          Timestamp
spark-streaming  spark-tutorial  microk8s/localhost  3.1.7    unsupported  10:17:32Z

App             Version  Status  Scale  Charm           Channel  Rev  Address         Exposed  Message
kafka-k8s                active      1  kafka-k8s       3/edge    47  10.152.183.242  no       
kafka-test-app           active      1  kafka-test-app  edge       8  10.152.183.167  no       Topic spark-streaming-store enabled with process producer
zookeeper-k8s            active      1  zookeeper-k8s   3/edge    42  10.152.183.87   no       

Unit               Workload  Agent  Address      Ports  Message
kafka-k8s/0*       active    idle   10.1.29.184         
kafka-test-app/0*  active    idle   10.1.29.185         Topic spark-streaming-store enabled with process producer
zookeeper-k8s/0*   active    idle   10.1.29.182  
```

Now the messages will be generated and written to Kafka periodically by `kafka-test-app`. However, in order to establish a connection and actually consume these messages from Kafka, Spark needs to authenticate with Kafka using the credentials. For the retreival of these credentials, we are going to use the `data-integrator` charm. Let's deploy `data-integrator` and integrate it with `kafka-k8s` with the following commands:

```bash
juju deploy data-integrator --series=jammy --channel=edge --config extra-user-roles=consumer,admin --config topic-name=spark-streaming-store

juju integrate data-integrator kafka-k8s 
```

Once this integration is complete, `juju status` should appear something similar to:

```
Model            Controller      Cloud/Region        Version  SLA          Timestamp
spark-streaming  spark-tutorial  microk8s/localhost  3.1.7    unsupported  10:22:14Z

App              Version  Status  Scale  Charm            Channel  Rev  Address         Exposed  Message
data-integrator           active      1  data-integrator  edge      15  10.152.183.18   no       
kafka-k8s                 active      1  kafka-k8s        3/edge    47  10.152.183.242  no       
kafka-test-app            active      1  kafka-test-app   edge       8  10.152.183.167  no       Topic spark-streaming-store enabled with process producer
zookeeper-k8s             active      1  zookeeper-k8s    3/edge    42  10.152.183.87   no       

Unit                Workload  Agent  Address      Ports  Message
data-integrator/0*  active    idle   10.1.29.186         
kafka-k8s/0*        active    idle   10.1.29.184         
kafka-test-app/0*   active    idle   10.1.29.185         Topic spark-streaming-store enabled with process producer
zookeeper-k8s/0*    active    idle   10.1.29.182 
```

Now that `data-integrator` is deployed and integrated with `kafka-k8s`, we can get the credentials to connect to Kafka by running the `get-credentials` action exposed by the `data-integrator` charm.

```bash
juju run-action data-integrator/0 get-credentials --wait 
```

The output generated by this command is similar to the following:

```
Running operation 1 with 1 task
  - task 2 on unit-data-integrator-0

Waiting for task 2...
kafka:
  consumer-group-prefix: relation-9-
  data: '{"extra-user-roles": "consumer,admin", "requested-secrets": "[\"username\",
    \"password\", \"tls\", \"tls-ca\", \"uris\"]", "topic": "spark-streaming-store"}'
  endpoints: kafka-k8s-0.kafka-k8s-endpoints:9092
  password: g6c5gjg48IjTFld664ipkz8Khqb5FOG0
  tls: disabled
  topic: spark-streaming-store
  username: relation-9
  zookeeper-uris: zookeeper-k8s-0.zookeeper-k8s-endpoints:2181/kafka-k8s
ok: "True"
```

As you can see, the endpoint, username and password to be used to authenticate with Kafka are displayed next to "endpoints", "username" and "password" respectively. It would be easier for us to store the username and password as variables so that they can be used later in the tutorial. For that, we can specify `--format=json` when running the `get-credentials` action, and then filtering out username and password using `yq`. Please note that we have already installed `yq` during the Setup section.

```bash
KAFKA_USERNAME=$(juju run data-integrator/0 get-credentials --format=json | yq .data-integrator/0.results.kafka.username)
KAFKA_PASSWORD=$(juju run data-integrator/0 get-credentials --format=json | yq .data-integrator/0.results.kafka.password)
KAFKA_ENDPOINT=$(juju run data-integrator/0 get-credentials --format=json | yq .data-integrator/0.results.kafka.endpoints)
```

For a moment, let's see the format of an event generated by `kafka-test-app`.

```json
{"timestamp": 1707128717.277745, "_id": "339e0f352b4843bfa0d512b796019a92", "origin": "kafka-test-app-0 (10.1.29.185)", "content": "Message #121"}
```

As we can see, the value of the "origin" key is the name and the IP address of the unit producing the events. We'll now write a Spark job in Python that counts the number of events grouped by the "origin" key in real time. 

First of all, we need to authenticate with Kafka and load the events from the `spark-streaming-store` topic . This can be done using `spark.readStream` function as:

```python
lines = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka-k8s-0.kafka-k8s-endpoints:9092") \
        .option("kafka.sasl.mechanism", "SCRAM-SHA-512") \
        .option("kafka.security.protocol", "SASL_PLAINTEXT") \
        .option("kafka.sasl.jaas.config", f'org.apache.kafka.common.security.scram.ScramLoginModule required username="relation-9" password="g6c5gjg48IjTFld664ipkz8Khqb5FOG0";') \
        .option("subscribe", "spark-streaming-store") \
        .option("includeHeaders", "true") \
        .load()
```

Now, let's create a user defined function that fetches the value of "origin" column from the event:

```python
from pyspark.sql.functions import udf
from json import loads

get_origin = udf(lambda x: loads(x)["origin"])
```

Now let's count the number of events grouped by the value of "origin" key, which is returned by `get_origin` function we wrote above.

```python
count = lines.withColumn(
            "origin", 
            get_origin(col("value"))
          ).select("origin").groupBy("origin").count()
```

Finally, writing the result continuously to the console until the job is terminated can be done as:

```python
query = w_count.writeStream.outputMode("complete").format("console").start()

query.awaitTermination()
```

Putting all this up together and enabling username, password, endpoint and topic to be passed as command line arguments, we come up with the following program:

```python
import argparse
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, col
from json import loads

# Create a Spark Session
spark = SparkSession.builder.appName("SubmitExample").getOrCreate()

# Read username, password and endpoint from command line arguments.
parser = argparse.ArgumentParser()
parser.add_argument("--kafka-username", "-u",
                help="The username to authenticate to Kafka",
                required=True)
parser.add_argument("--kafka-password", "-p",
                help="The password to authenticate to Kafka",
                  required=True)
parser.add_argument("--kafka-endpoint", "-e",
                  help="The bootstrap server endpoint",
                    required=True)
parser.add_argument("--kafka-topic", "-t",
                  help="The Kafka topic to subscribe to",
                    required=True)
args = parser.parse_args()
username=args.kafka_username
password=args.kafka_password
endpoint=args.kafka_endpoint
topic=args.kafka_topic

# Authenticating with Kafka and reading the stream from the topic
lines = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", endpoint) \
        .option("kafka.sasl.mechanism", "SCRAM-SHA-512") \
        .option("kafka.security.protocol", "SASL_PLAINTEXT") \
        .option(
          "kafka.sasl.jaas.config", 
          f'org.apache.kafka.common.security.scram.ScramLoginModule required username="{username}" password="{password}";'
        ).option("subscribe", topic) \
        .option("includeHeaders", "true") \
        .load()

# User defined function that returns the origin of one particular event
get_origin = udf(lambda x: loads(x)["origin"])

# Group by origin of the event and count number of event for each origins
count = lines.withColumn(
            "origin", 
            get_origin(col("value"))
          ).select("origin").groupBy("origin").count()

# Start writing the result to console
query = count.writeStream.outputMode("complete").format("console").start()

# Keep doing this until the job is terminated
query.awaitTermination()
```

Save the Python code above in a file named `spark_streaming.py`. We are now going to copy this script to the S3 bucket as:

```bash
aws s3 cp spark_streaming.py s3://spark-tutorial/spark_streaming.py
```

*Please make sure to provide correct path to where you saved the Python code.*

Once the file is copied to S3 server, let's submit a new job to Spark cluster using `spark-submit`.

```bash
spark-client.spark-submit \
    --username spark --namespace spark-streaming \
    --deploy-mode cluster \
    s3a://spark-tutorial/spark_streaming.py \
        --kafka-endpoint $KAFKA_ENDPOINT \
        --kafka-username $KAFKA_USERNAME \
        --kafka-password $KAFKA_PASSWORD \
        --kafka-topic "spark-streaming-store"
```

The job submission should start a driver pod, which in turn will create executor pods. The executor pods will then transition to the "Running" state and the streaming data is processed continuously by the executor pods.

We can view the status of the pods with the following command:

```python
watch -n1 "kubectl get pods -n spark-streaming | grep 'spark-streaming-.*-driver' "
```

The results are that are written to the console in the program we wrote earlier are actually written to the pod logs. To fetch the pod logs, we first need to know the name of the driver pod. Let's find the name of the driver pod and then fetch pod logs as:


```bash
pod_name=$(kubectl get pods -n spark-streaming | grep "count-vowels-.*-driver" | tail -n 1 | cut -d' ' -f1)

kubectl logs -n spark-streaming -f $pod_name | grep "Batch: " -A 10 # filter out line starting with "Batch: " and next 10 lines after that line
```

The option `-f` will tail the pod logs until `Ctrl + C` keys are pressed. If you observe carefully, you can see that new logs are appended every ten seconds, including the results containing the number of events grouped by the origin similar to the following:


```
...
2024-02-05T16:04:05.189Z [entrypoint] -------------------------------------------
2024-02-05T16:04:05.189Z [entrypoint] Batch: 13
2024-02-05T16:04:05.189Z [entrypoint] -------------------------------------------
2024-02-05T16:04:05.228Z [entrypoint] +--------------------+-----+
2024-02-05T16:04:05.228Z [entrypoint] |              origin|count|
2024-02-05T16:04:05.228Z [entrypoint] +--------------------+-----+
2024-02-05T16:04:05.228Z [entrypoint] |kafka-test-app-0 ...|  272|
2024-02-05T16:04:05.228Z [entrypoint] +--------------------+-----+
2024-02-05T16:04:05.228Z [entrypoint] 
...
```

Bravo! We were successful in processing streaming data with Charmed Spark solution.

In the next section, we will learn to monitor the status of the job using Spark History Server.
