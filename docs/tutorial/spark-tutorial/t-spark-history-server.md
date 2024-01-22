### Monitoring

By default, Spark stores the logs of drivers and executors as pod logs in the local file system, which gets lost if the pods are deleted. Spark provides us with the feature to store these logs in S3 so that they can later be retrieved and visualized.

Monitoring of Spark cluster can be done in two ways,
1. Using Spark History server charm
2. Using Canonical Observability Stack (COS)

We'll cover monitoring with Spark history server in this section and cover monitoring using COS in the next section.

### Monitoring with Spark History Server

Spark History Server is is a user interface to monitor the metrics and performance of completed and running Spark applications. The Spark History Server is offered as a charm in the Charmed Spark solution, which can be deployed via Juju.

To enable monitoring via Spark History server, we must first create a service account and provide configuration for Spark jobs to store logs in a S3 bucket. Then we need to deploy Spark History server with Juju by configuring it to read from the same S3 bucket that the Spark writes logs to.

Since we already have an existing service account, let's add extra configurations related to monitoring and Spark History Server to the `spark` service account we created earlier.

```bash
spark-client.service-account-registry add-config \
  --username spark --namespace spark \
  --properties-file ./confs/spark-history-server.conf
```

Now, let's create a fresh model and deploy the Spark History Server charm:

```bash
juju add-model history-server

juju deploy spark-history-server-k8s -n1 --channel 3.4/stable
```

For Spark History Server to work, it needs to connect to a S3 bucket. This integration is provided by the `s3-integrator` charm. Let's deploy that charm and integrate it with `spark-history-server-k8s`.

```bash
juju deploy s3-integrator -n1 --channel edge
juju config s3-integrator bucket=$S3_BUCKET path="spark-events" endpoint=$S3_ENDPOINT

juju run s3-integrator/leader sync-s3-credentials \
  access-key=$ACCESS_KEY secret-key=$SECRET_KEY

juju integrate s3-integrator spark-history-server-k8s
```

Once the charms are deployed and integrated, run `juju status` and note the IP address of `spark-history-server-k8s/0` unit. The web UI of Spark History Server can be accessed at port 18080 on that IP address.

In the next section, we'll cover monitoring Spark jobs with Canonical Observability Stack (COS).