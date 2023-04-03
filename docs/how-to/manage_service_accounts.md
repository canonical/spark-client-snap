## Manage Spark Client Accounts

This section provides general commands on how to use the CLI interface for creating, managing and configuring spark applications.

### Create Service Account

```bash
spark-client.service-account-registry --username demouser --namespace demonamespace create --primary --properties-file /home/demouser/conf/spark-overrides.conf  --conf spark.app.name=demo-spark-app-overrides
```

This creates a service account associated with configuration properties provided either via property file or explicit 
configuration arguments. The flags `--primary` specifies that the newly create account will be the primary account to 
be used. If another primary exists, the latter account primary flag will be set to `false`.

### List all service accounts

```bash
spark-client.service-account-registry list
```

This shows a list of the service accounts available, providing extra-information about whether it is a primary account
and its service account property flags.

### Add more entries to Service Account Configuration

```bash
spark-client.service-account-registry --username demouser --namespace demonamespace add-config --properties-file /home/demouser/conf/spark-overrides.conf  --conf spark.app.name=demo-spark-app-overrides
```

If the account ```demouser``` already exists, this will upsert into the existing configuration associated with the account.

### Remove entries from Service Account Configuration

```bash
spark-client.service-account-registry --username demouser --namespace demonamespace remove-config  --conf conf.key1.to.remove --conf conf.key2.to.remove
```

If the account ```demouser``` already exists, this will remove the specified keys from existing configuration associated with the account.

### Print configuration for a given Service Account 

```bash
spark-client.service-account-registry --username demouser --namespace demonamespace get-config
```

This command will print out to the screen the configuration for a given service account. 

### Delete Service Account Configuration

```bash
spark-client.service-account-registry --username demouser --namespace demonamespace clear-config
```

This command will delete the configurations associated to a given service account. 

### Inspect Primary Service Account

```bash
spark-client.service-account-registry get-primary
```

This command will allow the user to find out which one is the primary account, providing information 
about its configuration settings. 

### Cleanup a Service Account

```bash
spark-client.service-account-registry --username demouser --namespace demonamespace delete
```

This command will delete the service account together with the other resources created, e.g. 
secrets, role, role-bindings, etc. 