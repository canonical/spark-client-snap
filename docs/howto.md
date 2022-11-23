### How-To Guide

This section provides general commands on how to use the CLI interface for creating, managing and configuring spark applications.

#### Create Service Account

```bash
spark-client.setup-spark-k8s --username demouser --namespace demonamespace service-account --properties-file /home/demouser/conf/spark-overrides.conf  --conf spark.app.name=demo-spark-app-overrides
```

This creates a service account associated with configuration properties provided either via property file or explicit configuration arguments.

#### Create Service Account Configuration

```bash
spark-client.setup-spark-k8s --username demouser --namespace demonamespace sa-conf-create --properties-file /home/demouser/conf/spark-overrides.conf  --conf spark.app.name=demo-spark-app-overrides
```

If the account ```demouser``` already exists, this will drop the existing configuration associated with the account.

#### Inspect Specific Configurations For Service Account

```bash
spark-client.setup-spark-k8s --username demouser --namespace demonamespace sa-conf-get --conf spark.app.name --conf spark.kubernetes.namespace --conf spark.executor.instances
```

#### Inspect All Configuration For Service Account 

```bash
spark-client.setup-spark-k8s --username demouser --namespace demonamespace sa-conf-get
```

#### Delete Service Account Configuration

```bash
spark-client.setup-spark-k8s --username demouser --namespace demonamespace sa-conf-delete
```

#### Inspect Primary Service Account

```bash
spark-client.setup-spark-k8s resources-primary-sa
```

#### Cleanup a Service Account

```bash
spark-client.setup-spark-k8s --username demouser --namespace demonamespace service-account-cleanup
```
