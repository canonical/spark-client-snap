### Spark Monitoring with Canonical Observability Stack


The Charmed Spark solution comes with the [spark-metrics](https://github.com/banzaicloud/spark-metrics) exporter embedded in the [Charmed Spark OCI image](https://github.com/canonical/charmed-spark-rock), used as base for driver and executors pods .
This exporter is designed to push metrics to the [prometheus pushgateway](https://github.com/prometheus/pushgateway), that is integrated with the [Canonical Observability Stack](https://charmhub.io/topics/canonical-observability-stack). 


In order to enable the observability on Charmed Spark two steps are necessary:

1. Setup the COS (Canonical Observability Stack) bundle with juju
2. Configure the Spark service account

As a first step, start by deploying cos-lite bundle in a Kubernetes environment with Juju.

```shell
juju add-model cos
juju switch cos
juju deploy cos-lite --trust
```

Some extra charms are needed to integrate the Charmed Spark with the COS bundle. This includes the `prometheus-pushgateway-k8s` charm and the `cos-configuration-k8s grafana` that is used to configure the Grafana dashboard. We provide a basic dashboard [here](https://github.com/canonical/charmed-spark-rock/blob/dashboard/dashboards/prod/grafana/spark_dashboard.json).


```shell
juju deploy prometheus-pushgateway-k8s --channel edge

# deploy cos configuration charm to import the grafana dashboard
juju deploy cos-configuration-k8s \
  --config git_repo=https://github.com/canonical/charmed-spark-rock \
  --config git_branch=dashboard \
  --config git_depth=1 \
  --config grafana_dashboards_path=dashboards/prod/grafana/

# integrate cos-configration charm to import grafana dashboard
juju integrate cos-configuration-k8s grafana
juju integrate prometheus-pushgateway-k8s prometheus
```

This allows us to configure a custom scraping interval that prometheus will used to retrieve the exposed metrics.


Get address of the prometheus pushgateway.

```shell
export PROMETHEUS_GATEWAY=$(juju status --format=yaml | yq ".applications.prometheus-pushgateway-k8s.address") 
export PROMETHEUS_PORT=9091
```

The service account configurations needed for integrating Spark with the COS bundle is in the S3 bucket with name `confs/spark-monitoring.conf`. This configuration can be added to the existing `spark` service account with the following command:

```bash
spark-client.service-account-registry add-config \
  --username spark --namespace spark \
  --properties-file ./confs/spark-monitoring.conf
```

Now, let's submit a sample job to Spark using `spark-client.spark-submit`.

```bash
spark-client.spark-submit \
  --username spark --namespace spark \
  --deploy-mode cluster \
  s3a://$S3_BUCKET/scripts/stock_country_report.py \
    --input  s3a://$S3_BUCKET/data/data.csv.gz \
    --output s3a://$S3_BUCKET/data/output_report_microk8s
```

Use `juju status` to find the IP address of the `grafana` app. The Graphana Web UI can then be viewed in a web browser at port 3000 of that IP address. 

Use `admin` as username and fetch the password to use to login to Grafana dashboard by using the following action:

```shell
juju run grafana/leader get-admin-password
```

Once authenticated and in the landing page, navigate to "Dashboards" where you'll see a list of dashboards inside "General". Open the dashboard named "Spark dashboard". Here you can view several metrics related to the execution of Spark job.