## Manage Spark Service Accounts

The `spark-client` snap comes with a utility that helps administrators to manage service accounts. 

The setup utility supports the following actions.
* ***create*** - Create a new service account in Kubernetes for Spark job submission
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

As indicated above, the commands can take following optional parameters.
* ***log-level*** - Log level used by the logging module (default: `INFO`)
* ***kubeconfig*** - Kubernetes configuration file (default: ```$HOME/.kube/config```)
* ***context*** - For multi cluster Kubernetes deployments, the Kubernetes configuration file has multiple context entries. This parameter specifies which context to pick.
* ***namespace*** - Namespace for the service account (default: `default`)
* ***username*** - Username for the service accoun (default: `spark`)

> **Note** Don't forget to enable default kubeconfig access for the snap, otherwise it will complain not able to find kubeconfig file even after providing the valid default kubeconfig file

> **Note 2** The following utility functions assume that you have administrative permission on the namespaces (or on the kubernetes cluster) such that the corresponding resources (such as service accounts, secrets, roles and role-bindings) can be created and deleted. 

### Service Account Creation

For Spark job submission, a service account is needed in Kubernetes, belonging to a Kubernetes namespace. 

You might already have a functional Service Account, or you can use the `spark-client` snap to create  one in an existing Kubernetes namespace.

To get help regarding the usage of service account setup command within the snap, you can run the following command.

```bash
spark-client.service-account-registry create --help
```

The action takes following optional arguments
* ***primary*** - A flag to indicate whether the current service account should be made 'primary' (i.e. the default one for job submission)
* ***properties-file*** - File with all configuration properties to be associated with a service account.
* ***conf*** - Values to set or override esisting ones in specified `properties-file` parameter.

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
Service account is an abstraction for a set of Kubernetes resources needed to run a Spark job. The user can choose to associate configuration properties 
with service accounts that will serve as default for related job submissions across the cluster. A typical use of this feature would look like this.

```bash
spark-client.service-account-registry create --username demouser --namespace demonamespace  --properties-file /home/demouser/conf/spark-defaults.conf --conf spark.app.name=demo-spark-app --conf spark.executor.instances=3
```

The above command sets up a service account for user ```demonamespace:demouser``` for Spark job submission. Configuration properties are taken from the specified 
properties file, potentially overriden by configuration properties ```spark.app.name``` and ```spark.executor.instances```.

**_Note:_** The command described above does not create a kubernetes namespace but needs it to be there. It does however create the requested username in the specified and existing namespace. The kubernetes namespace could be created such as:
```
kubectl create namespace demonamespace
```

This service account - along with it's default configuration properties - now can be used for [Spark job submission](https://discourse.charmhub.io/t/spark-client-snap-tutorial-spark-submit/8953). 

If no specific account indicated on [job submission](https://discourse.charmhub.io/t/spark-client-snap-tutorial-spark-submit/8953), the account marked as ```primary``` is picked as default. An account can be marked as ```primary``` during creation.

***

 * Previous: [Set up the environment](https://discourse.charmhub.io/t/spark-client-snap-tutorial-setup-environment/8951)
 * Next: [Submit a Spark Job](https://discourse.charmhub.io/t/spark-client-snap-tutorial-spark-submit/8953)
 * [Charmed Spark Documentation](https://discourse.charmhub.io/t/charmed-spark-documentation/8963)