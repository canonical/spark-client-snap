# Enable Monitoring

The Charmed Spark solution comes with the [spark-metrics](https://github.com/banzaicloud/spark-metrics) exporter.
This exporter is designed to push metrics to the [prometheus pushgateway](https://github.com/prometheus/pushgateway), that is integrated with the [Canonical Observability Stack](https://charmhub.io/topics/canonical-observability-stack). 


To enable monitor with Charmed Spark just follow this guide.


As a prerequisite, you need to have Juju 3 installed with a MicroK8s controller bootstrapped. This can be done following this [tutorial](https://charmhub.io/topics/canonical-observability-stack/tutorials/install-microk8s).


As a first step, start by deploying cos-lite bundle in a Kubernetes environment with Juju.

```shell
juju add-model cos
juju switch cos
juju deploy cos-lite --trust

```
You can monitor the status of the deployment with the following command: 

```shell
watch --color juju status --color --relations
```

When everything is ready the output of previous command should be something similar:
```shell
Model  Controller       Cloud/Region        Version  SLA          Timestamp
cos    test-controller  microk8s/localhost  3.1.6    unsupported  13:52:00Z

App                         Version  Status   Scale  Charm                         Channel  Rev  Address         Exposed  Message
alertmanager                0.25.0   active       1  alertmanager-k8s              stable    77  10.152.183.25   no       
catalogue                            active       1  catalogue-k8s                 stable    19  10.152.183.250  no       
grafana                     9.2.1    active       1  grafana-k8s                   stable    82  10.152.183.88   no       
loki                        2.7.4    active       1  loki-k8s                      stable    91  10.152.183.26   no       
prometheus                  2.43.0   active       1  prometheus-k8s                stable   129  10.152.183.191  no       
traefik                     2.9.6    active       1  traefik-k8s                   stable   129  10.152.183.101  no       

Unit                           Workload  Agent  Address      Ports  Message
alertmanager/0*                active    idle   10.1.24.94          
catalogue/0*                   active    idle   10.1.24.78          
grafana/0*                     active    idle   10.1.24.96          
loki/0*                        active    idle   10.1.24.97          
prometheus/0*                  active    idle   10.1.24.91          
traefik/0*                     active    idle   10.1.24.93 

Integration provider                          Requirer                                         Interface                  Type     Message
alertmanager:alerting                         loki:alertmanager                                alertmanager_dispatch      regular  
alertmanager:alerting                         prometheus:alertmanager                          alertmanager_dispatch      regular  
alertmanager:grafana-dashboard                grafana:grafana-dashboard                        grafana_dashboard          regular  
alertmanager:grafana-source                   grafana:grafana-source                           grafana_datasource         regular  
alertmanager:replicas                         alertmanager:replicas                            alertmanager_replica       peer     
alertmanager:self-metrics-endpoint            prometheus:metrics-endpoint                      prometheus_scrape          regular  
catalogue:catalogue                           alertmanager:catalogue                           catalogue                  regular  
catalogue:catalogue                           grafana:catalogue                                catalogue                  regular  
catalogue:catalogue                           prometheus:catalogue                             catalogue                  regular  
grafana:grafana                               grafana:grafana                                  grafana_peers              peer     
grafana:metrics-endpoint                      prometheus:metrics-endpoint                      prometheus_scrape          regular  
loki:grafana-dashboard                        grafana:grafana-dashboard                        grafana_dashboard          regular  
loki:grafana-source                           grafana:grafana-source                           grafana_datasource         regular  
loki:metrics-endpoint                         prometheus:metrics-endpoint                      prometheus_scrape          regular  
prometheus:grafana-dashboard                  grafana:grafana-dashboard                        grafana_dashboard          regular  
prometheus:grafana-source                     grafana:grafana-source                           grafana_datasource         regular  
prometheus:prometheus-peers                   prometheus:prometheus-peers                      prometheus_peers           peer     
traefik:ingress                               alertmanager:ingress                             ingress                    regular  
traefik:ingress                               catalogue:ingress                                ingress                    regular  
traefik:ingress-per-unit                      loki:ingress                                     ingress_per_unit           regular  
traefik:ingress-per-unit                      prometheus:ingress                               ingress_per_unit           regular  
traefik:metrics-endpoint                      prometheus:metrics-endpoint                      prometheus_scrape          regular  
traefik:traefik-route                         grafana:ingress                                  traefik_route              regular  

```

After the correct deployment of the Observability bundle, some other extra applications need to be deployed to enable the monitoring of the Charmed Spark solution.

The first component is the Prometheus Pushgateway:
```shell
juju deploy prometheus-pushgateway-k8s --channel edge

```

followed by the followed by the `cos-configuration-k8s` and `prometheus-scrape-config-k8s`:
```shell
# deploy cos configuration charm to import the grafana dashboard
juju deploy cos-configuration-k8s \
  --config git_repo=https://github.com/canonical/charmed-spark-rock \
  --config git_branch=dashboard \
  --config git_depth=1 \
  --config grafana_dashboards_path=dashboards/prod/grafana/
# relate cos-configration charm to import grafana dashboard
juju relate cos-configuration-k8s grafana

# deploy the prometheus-scrape-config-k8s to configure a more fine grained scraping interval 
juju deploy prometheus-scrape-config-k8s scrape-interval-config --config scrape_interval=10s
juju relate scrape-interval-config prometheus-pushgateway-k8s
juju relate scrape-interval-config:metrics-endpoint prometheus:metrics-endpoint

```

After all these steps, the status of your deployment should look similar to the following:

```shell
Model  Controller       Cloud/Region        Version  SLA          Timestamp
cos    test-controller  microk8s/localhost  3.1.6    unsupported  13:55:00Z

App                         Version  Status   Scale  Charm                         Channel  Rev  Address         Exposed  Message
alertmanager                0.25.0   active       1  alertmanager-k8s              stable    77  10.152.183.25   no       
catalogue                            active       1  catalogue-k8s                 stable    19  10.152.183.250  no       
cos-configuration-k8s       3.5.0    active       1  cos-configuration-k8s         stable    15  10.152.183.200  no       
grafana                     9.2.1    active       1  grafana-k8s                   stable    82  10.152.183.88   no       
loki                        2.7.4    active       1  loki-k8s                      stable    91  10.152.183.26   no       
prometheus                  2.43.0   active       1  prometheus-k8s                stable   129  10.152.183.191  no       
prometheus-pushgateway-k8s  1.6.1    active       1  prometheus-pushgateway-k8s    edge       5  10.152.183.216  no       
scrape-interval-config      n/a      active       1  prometheus-scrape-config-k8s  stable    39  10.152.183.186  no       
traefik                     2.9.6    active       1  traefik-k8s                   stable   129  10.152.183.101  no       

Unit                           Workload  Agent  Address      Ports  Message
alertmanager/0*                active    idle   10.1.24.94          
catalogue/0*                   active    idle   10.1.24.78          
cos-configuration-k8s/0*       active    idle   10.1.24.99          
grafana/0*                     active    idle   10.1.24.96          
loki/0*                        active    idle   10.1.24.97          
prometheus-pushgateway-k8s/0*  active    idle   10.1.24.95          
prometheus/0*                  active    idle   10.1.24.91          
scrape-interval-config/0*      active    idle   10.1.24.105         
traefik/0*                     active    idle   10.1.24.93

Integration provider                          Requirer                                         Interface                  Type     Message
alertmanager:alerting                         loki:alertmanager                                alertmanager_dispatch      regular  
alertmanager:alerting                         prometheus:alertmanager                          alertmanager_dispatch      regular  
alertmanager:grafana-dashboard                grafana:grafana-dashboard                        grafana_dashboard          regular  
alertmanager:grafana-source                   grafana:grafana-source                           grafana_datasource         regular  
alertmanager:replicas                         alertmanager:replicas                            alertmanager_replica       peer     
alertmanager:self-metrics-endpoint            prometheus:metrics-endpoint                      prometheus_scrape          regular  
catalogue:catalogue                           alertmanager:catalogue                           catalogue                  regular  
catalogue:catalogue                           grafana:catalogue                                catalogue                  regular  
catalogue:catalogue                           prometheus:catalogue                             catalogue                  regular  
cos-configuration-k8s:grafana-dashboards      grafana:grafana-dashboard                        grafana_dashboard          regular  
cos-configuration-k8s:replicas                cos-configuration-k8s:replicas                   cos_configuration_replica  peer     
grafana:grafana                               grafana:grafana                                  grafana_peers              peer     
grafana:metrics-endpoint                      prometheus:metrics-endpoint                      prometheus_scrape          regular  
loki:grafana-dashboard                        grafana:grafana-dashboard                        grafana_dashboard          regular  
loki:grafana-source                           grafana:grafana-source                           grafana_datasource         regular  
loki:metrics-endpoint                         prometheus:metrics-endpoint                      prometheus_scrape          regular  
prometheus-pushgateway-k8s:metrics-endpoint   scrape-interval-config:configurable-scrape-jobs  prometheus_scrape          regular  
prometheus-pushgateway-k8s:pushgateway-peers  prometheus-pushgateway-k8s:pushgateway-peers     pushgateway_peers          peer     
prometheus:grafana-dashboard                  grafana:grafana-dashboard                        grafana_dashboard          regular  
prometheus:grafana-source                     grafana:grafana-source                           grafana_datasource         regular  
prometheus:prometheus-peers                   prometheus:prometheus-peers                      prometheus_peers           peer     
scrape-interval-config:metrics-endpoint       prometheus:metrics-endpoint                      prometheus_scrape          regular  
traefik:ingress                               alertmanager:ingress                             ingress                    regular  
traefik:ingress                               catalogue:ingress                                ingress                    regular  
traefik:ingress-per-unit                      loki:ingress                                     ingress_per_unit           regular  
traefik:ingress-per-unit                      prometheus:ingress                               ingress_per_unit           regular  
traefik:metrics-endpoint                      prometheus:metrics-endpoint                      prometheus_scrape          regular  
traefik:traefik-route                         grafana:ingress                                  traefik_route              regular  


```


In order to send metrics to the Prometheus Pushgateway we need to get the address of the Prometheus PushGateway: 

```shell
export PROMETHEUS_GATEWAY=$(juju status --format=yaml | yq ".applications.prometheus-pushgateway-k8s.address") 
export PROMETHEUS_PORT=9091
```

To enable the push of metrics you only need to add the following lines as configuration to a `spark-client` configuration file (e.g., `spark-defaults.conf`): 

```shell
spark.metrics.conf.driver.sink.prometheus.pushgateway-address=$PROMETHEUS_GATEWAY:$PROMETHEUS_PORT
spark.metrics.conf.driver.sink.prometheus.class=org.apache.spark.banzaicloud.metrics.sink.PrometheusSink
spark.metrics.conf.driver.sink.prometheus.enable-dropwizard-collector=true
spark.metrics.conf.driver.sink.prometheus.period=5
spark.metrics.conf.driver.sink.prometheus.metrics-name-capture-regex=([a-z0-9]*_[a-z0-9]*_[a-z0-9]*_)(.+)
spark.metrics.conf.driver.sink.prometheus.metrics-name-replacement=\$2
spark.metrics.conf.executor.sink.prometheus.pushgateway-address=$PROMETHEUS_GATEWAY:$PROMETHEUS_PORT
spark.metrics.conf.executor.sink.prometheus.class=org.apache.spark.banzaicloud.metrics.sink.PrometheusSink
spark.metrics.conf.executor.sink.prometheus.enable-dropwizard-collector=true
spark.metrics.conf.executor.sink.prometheus.period=5
spark.metrics.conf.executor.sink.prometheus.metrics-name-capture-regex=([a-z0-9]*_[a-z0-9]*_[a-z0-9]*_)(.+)
spark.metrics.conf.executor.sink.prometheus.metrics-name-replacement=\$2
```

or as alternative you can directly add each option as configuration option to `spark-client.spark-submit`: 

```shell
spark-client.spark-submit --deploy-mode cluster --name <APP_NAME> \
--conf spark.executor.instances=<NUM_INSTANCES> \
--conf spark.kubernetes.namespace=<NAMESPACE> \
--conf spark.kubernetes.authenticate.driver.serviceAccountName=<K8S_SERVICE_ACCOUNT_FOR_SPARK> \
--conf park.metrics.conf.driver.sink.prometheus.pushgateway-address=$PROMETHEUS_GATEWAY:$PROMETHEUS_PORT \
--conf spark.metrics.conf.driver.sink.prometheus.class=org.apache.spark.banzaicloud.metrics.sink.PrometheusSink \
--conf spark.metrics.conf.driver.sink.prometheus.enable-dropwizard-collector=true \
--conf spark.metrics.conf.driver.sink.prometheus.period=5 \
--conf spark.metrics.conf.driver.sink.prometheus.metrics-name-capture-regex=([a-z0-9]*_[a-z0-9]*_[a-z0-9]*_)(.+) \
--conf spark.metrics.conf.driver.sink.prometheus.metrics-name-replacement=\$2 \
--conf spark.metrics.conf.executor.sink.prometheus.pushgateway-address=$PROMETHEUS_GATEWAY:$PROMETHEUS_PORT \
--conf spark.metrics.conf.executor.sink.prometheus.class=org.apache.spark.banzaicloud.metrics.sink.PrometheusSink \
--conf spark.metrics.conf.executor.sink.prometheus.enable-dropwizard-collector=true \
--conf spark.metrics.conf.executor.sink.prometheus.period=5 \
--conf spark.metrics.conf.executor.sink.prometheus.metrics-name-capture-regex=([a-z0-9]*_[a-z0-9]*_[a-z0-9]*_)(.+) \
--conf spark.metrics.conf.executor.sink.prometheus.metrics-name-replacement=\$2 \
<PATH_FOR_CODE_PY_FILE>

```

Eventually, you will need to retrive the credentials for logging into the Grafana dashboard, by using the following action:
``` shell
juju run grafana/leader get-admin-password
```

After the login, Grafana will show a new dashboard: `Spark Dashboard` where the metrics are displayed.
