## Setup Kubernetes and Spark Client Snap

In order to be able to work with Kubernetes,  first we first to set up a Kubernetes cluster. In this tutorial we use [MicroK8s](https://microk8s.io/), 
which is the simplest production-grade conformant K8s.

### Setup MicroK8s

MicroK8s snap installation goes as simple as

```bash
sudo snap install microk8s --classic
```

It is also recommended to configure MicroK8s in a way, so that the correpsonding user has admin rights on  the cluster. 

```bash 
sudo snap alias microk8s.kubectl kubectl
sudo usermod -a -G microk8s ${USER}
mkdir -p ~/.kube
sudo chown -f -R ${USER} ~/.kube
```

In order to make these changes effective, it is best to open a new shell (or log in, log out) so the permissions would become effective. 

Make sure that the MicroK8s cluster is now up and running:

```bash
microk8s status --wait-ready
```

Note that this command will wait until the cluster is ready. Once this is indeed the case, it will 
print a summary of the services that are active. 

At this point we can export the Kubernetes config file: 

```bash 
microk8s config | tee ~/.kube/config
```

MicroK8s also allows to enable some K8s features used by the Spark Client Snap 
(DNS resolution of pods and RBAC):

```
microk8s.enable dns
microk8s.enable rbac
```

The MicroK8s cluster is now ready to be used. 

### Setup Spark Client Snap 

In order to install the spark-client snap, simply issue the following command:

```bash
sudo snap install spark-client --edge
```

This will install all the spark binaries along side with the `spark-client` utilities provided in 
the snap.

***

 * Previous: [Spark Client Snap Tutorial](https://discourse.charmhub.io/t/spark-client-snap-tutorial/8957)
 * Next: [Manage Spark service accounts](https://discourse.charmhub.io/t/spark-client-snap-tutorial-setup-environment/8952)