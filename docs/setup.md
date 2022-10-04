### Setup Apache Spark for your Kubernetes cluster
We are working with Kubernetes distribution for Spark. So, to be able to work with Kubernetes, we need to do some setup
for Spark jobs.

The spark-client snap comes with a multi-functional setup utility which would be the starting point for the setup. You can
run the following command to understand it's usage.
```bash
spark-client.setup-spark-k8s --help
```

From the output you will notice that the setup utility supports three kinds of actions.
* ***service-account*** - Action to setup the service account in Kubernetes for use during Spark job submission to Kubernetes
* ***get-ca-cert*** - Action to retrieve CA certificate from kubeconfig for use during Spark job submission to Kubernetes
* ***get-token*** - Action to retrieve OAuth token from Kubernetes Control plane for use during Spark job submission to Kubernetes

```bash
usage: setup-spark-k8s.py [-h] [--kubeconfig KUBECONFIG] [--cluster CLUSTER] {service-account,get-ca-cert,get-token} ...

positional arguments:
  {service-account,get-ca-cert,get-token}

optional arguments:
  -h, --help            show this help message and exit
  --kubeconfig KUBECONFIG
                        Kubernetes configuration file
  --cluster CLUSTER     Cluster name to use within the provided kubernetes configuration file
```

As you would have noticeed, all of these commands can take following optional parameters.
* ***kubeconfig*** - Kubernetes configuration file. If not provided, ```$HOME/.kube/config``` is used by default
* ***cluster*** - For multi cluster Kubernetes deployments, Kubernetes configuration file will have multiple cluster entries. This parameter specifies which cluster name to pick from the configuration.

#### Enabling Default Kubernetes Config File Access

First of you will have to allow the snap to access default kubeconfig file ```$HOME/.kube/config``` in case you have it placed there.

```bash
sudo snap connect spark-client:enable-kubeconfig-access
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

You will notice from the help output that the command takes a mandatory ```username``` as well as an optional ```namespace``` 
argument where the service account named username will be created. Default namespace where user is created is ```default```.

```bash
usage: setup-spark-k8s.py service-account [-h] [--namespace NAMESPACE] username

positional arguments:
  username              Service account username to be created in kubernetes.

optional arguments:
  -h, --help            show this help message and exit
  --namespace NAMESPACE
                        Namespace for the service account to be created in kubernetes. Default is default namespace
```

#### Retrieving CA Certificate
One of the requirements for Spark job submission to a Kubernetes cluster as we will see later is the CA certificate.

The spark-client snap ships with a utility to retrieve the Kubernetes CA certificate for Spark job submission purpose. 

To get help regarding the usage of CA certificate retrieval action within the snap setup command, you can run the following.

```bash
spark-client.setup-spark-k8s get-ca-cert --help
```

Notice that get-ca-cert action does not need any additional optional parameters, other than the optional kubeconfig and
cluster parameters passed to the setup-spark-k8s command. So, the following command should be enough with defaults.

```bash
spark-client.setup-spark-k8s get-ca-cert
```

Alternatively, assuming you have the kubeconfig file called ```/path/to/hello-kubeconfig```. And it has multiple
kubernetes clusters specified within it and you want to work with cluster named ```hello-cluster```. Following command should work.

```bash
spark-client.setup-spark-k8s --kubeconfig /path/to/hello-kubeconfig --cluster hello-cluster get-ca-cert
```
#### Generating OAuth Token for job submission
Spark job submission requires an Oauth Token to authenticate with Kubernetes Control Plane. The setup-spark-k8s command bundled
with the spark-client snap has a get-token action to help you with this token generation step.

Run the following command to know more about the get-token action of setup-spark-k8s command.

```bash
spark-client.setup-spark-k8s get-token --help
```

The action requires a mandatory ```serviceaccount``` and an optional ```namespace``` argument to which the serviceaccount
belongs. The default namespace assumed if not provided is ```default```.

```bash
usage: setup-spark-k8s.py get-token [-h] [--namespace NAMESPACE] serviceaccount

positional arguments:
  serviceaccount        Service account name for which the Oauth token is to be fetched.

optional arguments:
  -h, --help            show this help message and exit
  --namespace NAMESPACE
                        Namespace for the service account for which the Oauth token is to be fetched. Default is default namespace
```