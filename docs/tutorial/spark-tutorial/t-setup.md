## Setup Environment for the Tutorial

This tutorial takes the demonstration on Charmed Spark by Paolo Sottovia at Ubuntu Summit 2023 as its reference. The video demonstration for this tutorial can be viewed on YouTube via (this link)[https://www.youtube.com/watch?v=nu1ll7VRqbI].

The resources that will be used during this tutorial are available at (this GitHub repository)[https://github.com/welpaolo/ubuntu-summit-2023]. Let's clone that repository onto our machine.

```bash
git clone https://github.com/welpaolo/ubuntu-summit-2023.git
cd ubuntu-summit-2023
```

Charmed Spark is developed to be run on top of a Kubernetes cluster. In this tutorial we use [MicroK8s](https://microk8s.io/), which is the simplest production-grade conformant K8s.

Before starting, it's always a good idea to update the packages in the system.

```bash
sudo apt update
sudp apt upgrade
```

MicroK8s can be installed via Snap as

```bash
sudo snap install microk8s -channel=1.28-strict/stable
```

Please note that we're installing the strictly confined version of the MicroK8s snap, because the non-confined one no longer works with Juju (starting from Juju 3.x onwards).

Let's configure MicroK8s for use in this tutorial:

```bash
# Set an alias 'kubectl' that can be used instead of microk8s.kubectl
sudo snap alias microk8s.kubectl kubectl

# Add the current user into 'microk8s' group
sudo usermod -a -G microk8s ${USER}

# Create and provide ownership of '~/.kube' directory to current user
mkdir -p ~/.kube
sudo chown -f -R ${USER} ~/.kube

# Put the group membership changes into effect
newgrp microk8s
```

Once done, the status of the MicroK8s can be verified with

```bash
microk8s status --wait-ready
```

Let's generate the Kubernetes configuration file using MicroK8s and write it to `~/.kube/config`

```bash
microk8s config | tee ~/.kube/config
```

In order to use Spark use S3 for object storage, we are going to use an S3 compliant object storage library `minio`, an add-on for which is shipped by default in `microk8s` installation. Let's install the addon and a few other addons.

```bash
sudo microk8s enable hostpath-storage dns rbac storage minio

sudo apt install jq
IPADDR=$(ip -4 -j route get 2.2.2.2 | jq -r '.[] | .prefsrc')
sudo microk8s enable metallb:$IPADDR-$IPADDR
```

Once you enable `minio` add-on, you will have a MinIO Kubernetes operator running in the K8s cluster. All the resources created for MinIO are created in the `minio-operator` namespace. You can verify these with the following commands:

```bash
kubectl get namespace minio-operator
kubectl get deployments -n minio-operator
kubectl get services -n minio-operator
kubectl get pods -n minio-operator
```

We'll use `juju` to deploy `kafka`, `zookeeper`, `prometheus`, Spark history server and a bunch of other applications later to use together with Spark. For that reason, let's install and configure `juju`:

```bash
sudo snap install juju --channel 3.1/stable

mkdir -p ~/.local/share
```

When Spark jobs are run on top of Kubernetes a set of Kubernetes, resources like service account, associated roles, role bindings and other configurations needs to be created and configured. Luckily, we have a `spark-client` snap as part of Charmed Spark solution to do all of that. Let's install the `spark-client` snap:

```bash
sudo snap install spark-client --channel 3.4/edge
```

Now we need to create a S3 bucket and upload the sample data and a few scripts we'll use later there. For us to be able to create the bucket, we need to authenticate to MinIO using an access key and the secret key. These can be obtained using the `microk8s-user-1` Kubernetes secret in the `minio-operator` namespace in Kubernetes cluster.

Export these into environment variables so that they can be used later in our tutorial.

```bash
export ACCESS_KEY=$(kubectl get secret -n minio-operator microk8s-user-1 -o jsonpath='{.data.CONSOLE_ACCESS_KEY}' | base64 -d)
export SECRET_KEY=$(kubectl get secret -n minio-operator microk8s-user-1 -o jsonpath='{.data.CONSOLE_SECRET_KEY}' | base64 -d)
export S3_ENDPOINT=$(kubectl get service minio -n minio-operator -o jsonpath='{.spec.clusterIP}')

MINIO_UI_IP=$(kubectl get service microk8s-console -n minio-operator -o jsonpath='{.spec.clusterIP}')
MINIO_UI_PORT=$(kubectl get service microk8s-console -n minio-operator -o jsonpath='{.spec.ports[0].port}')
export MINIO_UI_URL=$MINIO_UI_IP:$MINIO_UI_PORT

export S3_BUCKET="spark_tutorial"
```

These information can also be viewed on the console by running the `bin/check-minio.sh` script from the repository.

```bash
./bin/check-minio.sh
```

The repository also contains a Python script that creates a S3 bucket and copies some files we'll use later in the tutorial to the bucket. Run the `spark_bucket.py` script as:

```bash
python scripts/spark_bucket.py \
  --action create setup \
  --access-key $ACCESS_KEY \
  --secret-key $SECRET_KEY \
  --endpoint $S3_ENDPOINT \
  --bucket $S3_BUCKET
```

Once the script executes, the S3 bucket will be created successfully. Let's verify that using MinIO web UI as well. The IP and port in which MinIO web UI runs has already been exported to `MINIO_UI` earlier and can also be viewed by running the `./bin/check-minio.sh` script as demonstrated earlier.


Open a browser and enter the URL. In the login page, enter the access key as the username and secret key as the password. Once you're logged in, browse through the `spark_tutorial` bucket. There you can see the a few files and directories copied over to the bucket.

We will now create Kubernetes service accounts that will be used to run the Spark workloads. The creation of the service account can be done using the `spark-client` snap, which will create necessary roles, rolebindings and configurations along with the service account.

```bash
# Create namespace
kubectl create namespace spark

# Create service account
spark-client.service-account-registry create \
  --username spark --namespace spark \
  --properties-file ./confs/s3.conf
```

That's it. Now we're ready to submit jobs to Spark!