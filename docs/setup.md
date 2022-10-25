### Setup Apache Spark for your Kubernetes cluster
We are working with Kubernetes distribution for Spark. So, to be able to work with Kubernetes, we need to do some setup
for Spark jobs.

The spark-client snap comes with a setup utility which would be the starting point for the setup. You can
run the following command to understand it's usage.
```bash
spark-client.setup-spark-k8s --help
```

From the output you will notice that the setup utility supports the following actions.
* ***service-account*** - Action to set up the service account in Kubernetes for use during Spark job submission to Kubernetes

```bash
usage: setup-spark-k8s.py [-h] [--kubeconfig KUBECONFIG] [--context CONTEXT] {service-account} ...

positional arguments:
  {service-account}

optional arguments:
  -h, --help            show this help message and exit
  --kubeconfig KUBECONFIG
                        Kubernetes configuration file
  --context CONTEXT     Context name to use within the provided kubernetes configuration file
```

As you would have noticed, these commands can take following optional parameters.
* ***kubeconfig*** - Kubernetes configuration file. If not provided, ```$HOME/.kube/config``` is used by default
* ***context*** - For multi cluster Kubernetes deployments, Kubernetes configuration file will have multiple context entries. This parameter specifies which context name to pick from the configuration.

#### Enabling Default Kubernetes Config File Access

First of you will have to allow the snap to access default kubeconfig file ```$HOME/.kube/config``` in case you have it placed there.

```bash
sudo snap connect spark-client:dot-kubeconfig-access
```

The spark-client snap is a strictly confined snap. The above command grants the snap permission to read the afore-mentioned
kubeconfig file from default location.

#### Creating Service Account in Kubernetes
To submit Spark jobs to Kubernetes, we need a service account in Kubernetes. Service Account belongs to a Kubernetes namespace. 

You might already have a functional Service Account. Or you can use this spark-client snap to create a fresh one in a namespace of choice.

To get help regarding the usage of service account setup command within the snap, you can run the following command.

```bash
spark-client.setup-spark-k8s service-account --help
```

You will notice from the help output that the command takes an optional ```username``` as well as an optional ```namespace``` 
argument where the service account named username will be created in the namespace as specified. Default user is ```spark``` and namespace where user is created is ```default```.

```bash
usage: setup-spark-k8s.py service-account [-h] [--username USERNAME] [--namespace NAMESPACE]

optional arguments:
  -h, --help            show this help message and exit
  --username USERNAME   Service account username to be created in kubernetes. Default is spark
  --namespace NAMESPACE
                        Namespace for the service account to be created in kubernetes. Default is default namespace

```
