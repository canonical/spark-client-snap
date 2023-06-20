## Deploy the Spark History Server 

The Spark History server is a component in the Spark ecosystem that helps you monitor your spark jobs. In particualar, the History Server enables access to logs of completed/running Spark jobs for viewing and analysis.

Within the Charmed Spark solution, its deployment, configuration and operation is handled by [Juju](https://juju.is/). Therefore, a [Charmed operator](https://charmhub.io/spark-history-server-k8s) will be responsible for its management and operations on K8s.

### Requirements

Since Spark History server will be managed by Juju, make sure that:
* you have a Juju client (e.g. via a [SNAP](https://snapcraft.io/juju)) installed in your local machine  
* you are able to connect to a juju controller running on K8s.
* you have read-write permissions (therefore you have a access key and access secret) to a S3-compatible object storage (e.g. MinIO)

To see how to setup a Juju controller on K8s and the juju client, you can refer to existing tutorials and documentation, e.g. [here](https://juju.is/docs/olm/get-started-with-juju).

To see how to setup MinIO on top of MicroK8s, please refer to [here](https://microk8s.io/docs/addon-minio). If you have a MicroK8s MinIO plugin enabled, use the following commands to 
obtain the access key, the access secret and the MinIO endpoint:

* *access key*: `microk8s.kubectl get secret -n minio-operator microk8s-user-1 -o jsonpath='{.data.CONSOLE_ACCESS_KEY}' | base64 -d`
* *secret key*: `microk8s.kubectl get secret -n minio-operator microk8s-user-1 -o jsonpath='{.data.CONSOLE_SECRET_KEY}' | base64 -d`
* *MinIO endpoint*: `microk8s.kubectl get services -n minio-operator | grep minio | awk '{ print $3 }'`

### Preparation

#### Juju Namespace 

Before deploying the Spark History server, it is advisable to create a dedicated namespace for `Spark` components if you don't already have one:

```bash 
juju add-model spark
```

#### Setup S3 Bucket

Create a bucket named `history-server` and an path object `spark-events` for storing Spark logs in s3. This can be done in multiple ways depending on the S3 backend interface.
For instance, via Python API, you can install and use the `boto` library, as in the following:

*Install boto*

`pip install boto3`

*Create the S3 bucket*

```python
from botocore.client import Config
import boto3

config = Config(connect_timeout=60, retries={"max_attempts": 0})
session = boto3.session.Session(
    aws_access_key_id=<ACCESS_KEY>, aws_secret_access_key=<SECRET_KEY>
)
s3 = session.client("s3", endpoint_url=<S3_ENDPOINT>, config=config)

s3.create_bucket(Bucket="history-server")
s3.put_object(Bucket="history-server", Key=("spark-events/"))
```

### Deploy Spark History Server

* *Deploy the Spark History Server component*

```bash
juju deploy spark-history-server-k8s -n1 --channel 3.4/edge
```

* *Deploy and configure a [s3-integrator](https://charmhub.io/s3-integrator) charm*

```bash
juju deploy s3-integrator -n1 --channel edge
juju config s3-integrator bucket="history-server" path="spark-events" endpoint=<S3_ENDPOINT>
juju run s3-integrator/0 sync-s3-credentials access-key=<ACCESS_KEY> secret-key=<SECRET_KEY>
```

* *Relate s3-integrator and Spark History server*

```bash 
juju relate s3-integrator spark-history-server-k8s
```

Make sure that the s3-integrator and Spark History server services are active using `juju status`.

### Expose the Spark History server UI

The Spark History server exposes a UI accessible at ```http://<spark-history-server-ip>:18080```. 

If you are running MicroK8s, you can directly expose it to the local network by enabling DNS

```bash
microk8s enable dns
```

and retrieve the Spark History server POD IP using

```bash
kubectl get pod spark-history-server-0 -n spark --template '{{.status.podIP}}'
```
