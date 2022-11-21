#### How to create configuration for a Service Account after account creation

The configuration functionality mentioned in the previous section can be done after account creation as well. Useful for redefining the configuration associated with a existing service account.

```bash
spark-client.setup-spark-k8s --username demouser --namespace demonamespace sa-conf-create --properties-file /home/demouser/conf/spark-overrides.conf  --conf spark.app.name=demo-spark-app-overrides
```

The above command will **drop** the existing configuration associated with service account ```demonamespace:demouser``` and recreate it with properties in the new properties file and override the ```spark.app.name```.

All job submissions using this service-account will use the new default configuration going forward.


#### How to inspect configuration for a Service Account

For inspecting the current properties configured for a service account, the ```sa-conf-get``` utility comes handy.

```bash
spark-client.setup-spark-k8s --username demouser --namespace demonamespace sa-conf-get --conf spark.app.name --conf spark.kubernetes.namespace --conf spark.executor.instances
```

If you wish to not pick specific properties and see all of them for service account ```demonamespace:demouser```

```bash
spark-client.setup-spark-k8s --username demouser --namespace demonamespace sa-conf-get
```

#### How to delete configuration for a Service Account

For deleting all configuration associated with a service account,

```bash
spark-client.setup-spark-k8s --username demouser --namespace demonamespace sa-conf-delete
```

#### How to check Primary Service Account

While discussing service account creation, it was mentioned that a service account can be marked as the ```primary``` account to be used implicitly if no service account is specified during job submission.

There is always a single service account marked as ```primary```. The first service account created will automatically be considered the ```primary```.

To inspect which service account is marked as ```primary```, one would use the ```resources-primary-sa``` utility which would list the current ```primary``` service account.

```bash
spark-client.setup-spark-k8s resources-primary-sa
```

#### How to clean up a Service Account

To clean up all resources associated with a given service account,

```bash
spark-client.setup-spark-k8s --username demouser --namespace demonamespace service-account-cleanup
```
