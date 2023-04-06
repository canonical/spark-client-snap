## Setup Kubernetes and Spark Client Snap

We are working with Kubernetes distribution for Spark. So, to be able to work with Kubernetes, 
we first need to install a kubernetes cluster. In this tutorial we will [MicroK8s](https://microk8s.io/), 
which is the simplest production-grade conformant K8s. Lightweight and focused. 
Single command install on Linux, Windows and macOS.

### Setup MicroK8s

To install MicroK8s

```bash
sudo snap install microk8s --classic
```

It is also recommended to configure MicroK8s, so that the user has admin permission on 
the cluster. Use the following commands to configure the user to perform actions on the K8s cluster:

```bash 
sudo snap alias microk8s.kubectl kubectl
sudo usermod -a -G microk8s ${USER}
mkdir -p ~/.kube
sudo chown -f -R ${USER} ~/.kube
```

In order to make this changes effective, it is best to open a new shell such that the permissions
becomes effective. In the new terminal, make sure that the MicroK8s cluster is 
now up and running, using:

```bash
microk8s status --wait-ready
```

Note that this will wait until the cluster is ready and once this is indeed the case, it will 
print a summary of the services that are active. 

At this point we can export the kubeconfig file: 

```bash 
microk8s config | tee ~/.kube/config
```

MicroK8s also allows to enable some K8s features used by the Spark Client Snap 
(DNS resolution of pods and RBAC) by simply using 

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

This will install all the spark binaries along side with the spark-client utilities provided in 
the snap.