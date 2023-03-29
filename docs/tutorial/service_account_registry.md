## Manage Spark Service Accounts

The spark-client snap comes with a setup utility which would be the starting point for the setup. You can
run the following command to understand it's usage.
```bash
spark-client.service-account-registry --help
```

From the output you will notice that the setup utility supports the following actions.
* ***create*** - Create a new service account in Kubernetes for use during Spark job submission
* ***delete*** - Delete a service account and associated resources from Kubernetes
* ***add-config*** - Add configuration entries associated with the specified service account in Kubernetes.
* ***remove-config*** - Remove configuration entries from the specified service account in Kubernetes.
* ***get-config*** - Fetch configuration entries associated with the specified service account from Kubernetes
* ***clear-config*** - Delete all configuration entries associated with the specified service account from Kubernetes
* ***get-primary*** - List resources related to 'primary' service account used implicitly for spark-submit
* ***list*** - List all service accounts available to be used with Spark

```bash
usage: service_account_registry.py [-h] {create,delete,add-config,remove-config,get-config,clear-config,get-primary,list} ...

Spark Client Setup

positional arguments:
  {create,delete,add-config,remove-config,get-config,clear-config,get-primary,list}

options:
  -h, --help            show this help message and exit
```

As you would have noticed, these commands can take following optional parameters.
* ***log-level*** - Log level used by the logging module. Default is 'INFO'.
* ***kubeconfig*** - Kubernetes configuration file. If not provided, ```$HOME/.kube/config``` is used by default
* ***context*** - For multi cluster Kubernetes deployments, Kubernetes configuration file will have multiple context entries. This parameter specifies which context name to pick from the configuration.
* ***namespace*** - Namespace for the service account to be used for the action. Default is 'default'.
* ***username*** - Username for the service account to be used for the action. Default is 'spark'.

> **Note** Don't forget to enable default kubeconfig access for the snap, otherwise it will complain not able to find kubeconfig file even after providing the valid default kubeconfig file

### Service Account Creation
To submit Spark jobs to Kubernetes, we need a service account in Kubernetes. Service Account belongs to a Kubernetes namespace. 

You might already have a functional Service Account. Or you can use this spark-client snap to create a fresh one in a namespace of choice.

To get help regarding the usage of service account setup command within the snap, you can run the following command.

```bash
spark-client.service-account-registry create --help
```

You will notice from the help output that the action takes following optional arguments
* ***primary*** - A marker to indicate the current service account should be made 'primary' for implicit spark-submit job submission purposes.
* ***properties-file*** - File with all configuration properties to be associated with a service account.
* ***conf*** - Values to add to and override the ones in specified properties-file param.

```bash
usage: service_account_registry.py create [-h] [--log-level {INFO,WARN,ERROR,DEBUG}] [--master MASTER] [--kubeconfig KUBECONFIG] [--context CONTEXT] [--properties-file PROPERTIES_FILE] [--conf CONF]
                                          [--username USERNAME] [--namespace NAMESPACE] [--primary]

options:
  -h, --help            show this help message and exit
  --log-level {INFO,WARN,ERROR,DEBUG}
                        Set the log level of the logging
  --master MASTER       Kubernetes control plane uri.
  --kubeconfig KUBECONFIG
                        Kubernetes configuration file
  --context CONTEXT     Kubernetes context to be used
  --properties-file PROPERTIES_FILE
                        Spark default configuration properties file.
  --conf CONF           Config properties to be added to the service account.
  --username USERNAME   Service account name to use other than primary.
  --namespace NAMESPACE
                        Namespace of service account name to use other than primary.
  --primary             Boolean to mark the service account as primary.
```
Service account is an abstraction for a set of associated kubernetes resources needed to run a Spark job. The user can choose to associate configuration properties 
with the service account that can serve as default while submitting jobs against that service account from any machine within the kubernetes cluster. A typical use 
of this feature would look like this.

```bash
spark-client.service-account-registry --username demouser --namespace demonamespace create --properties-file /home/demouser/conf/spark-defaults.conf --conf spark.app.name=demo-spark-app --conf spark.executor.instances=3
```

The above command sets up a service account for user ```demonamespace:demouser``` for Spark job submission using configuration properties coming from the specified 
properties file while overriding the configuration properties ```spark.app.name``` and ```spark.executor.instances```.

For [job submission](https://discourse.charmhub.io/t/spark-client-snap-tutorial-spark-submit/8953), this service account along with it's default configuration properties can be used to submit a Spark job. 

For example, assuming the properties file provided has configuration details to access data in S3, one could submit a job like
```bash
spark-client.submit  --username demouser --namespace demonamespace --deploy-mode cluster --conf spark.app.name=demo-spark-s3-app $S3_PATH_FOR_CODE_FILE
```
This would launch the spark job with configuration coming from the service account for user ```demonamespace:demouser``` but the app name would be ```demo-spark-s3-app```. 

**_Note:_** The command described above does not create a kubernetes namespace but needs it to be there. It does however create the requested username in the specified and existing namespace.

During [job submission](https://discourse.charmhub.io/t/spark-client-snap-tutorial-spark-submit/8953), if the account is not specified, the account currently marked as ```primary``` is implicitly picked. An account can be marked as ```primary``` during creation.
