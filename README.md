## Introduction

Canonical's Charmed Data Platform solution for Apache Spark runs Spark jobs on your Kubernetes cluster. 
You can get started right away with [Microk8s](https://microk8s.io/) - the mightiest tiny Kubernetes distro around! 
You can install MicroK8s on your Ubuntu laptop, workstation, or nodes in your workgroup or server cluster with just one command - ```snap install microk8s --classic```. Learn more at [microk8s.io](https://microk8s.io/).

## Spark-client Snap
The ***spark-client*** snap includes the scripts to run jobs via [spark-submit](https://discourse.charmhub.io/t/spark-client-snap-tutorial-spark-submit/8953), 
or using [interactive shells](https://discourse.charmhub.io/t/spark-client-snap-tutorial-interactive-mode/8954), and other tools for 
managing ***Apache Spark*** jobs for ***Kubernetes***.

## Setup
The spark-client snap simplifies the setup to run Spark jobs against your Kubernetes cluster. 
To run the snap, make sure that your environment satisfies the requirements 
listed [here](https://discourse.charmhub.io/t/spark-client-snap-reference-requirements/8962) and 
then follow the instructions in the [setup](https://discourse.charmhub.io/t/spark-client-snap-tutorial-setup-environment/8952) 
section to get started.

Do check out the section on [config resolution](https://discourse.charmhub.io/t/spark-client-snap-explanation-hierarchical-configuration-handling/8956) 
to understand how [spark-submit](https://discourse.charmhub.io/t/spark-client-snap-tutorial-spark-submit/8953) actually 
resolves the configuration properties coming from a diverse set of available sources.

## Play!
Once the [setup](https://discourse.charmhub.io/t/spark-client-snap-tutorial-setup-environment/8951) is complete, 
create a Spark service account using the [CLI](https://discourse.charmhub.io/t/spark-client-snap-tutorial-setup-environment/8952) and follow the Spark 
job [submission guide](https://discourse.charmhub.io/t/spark-client-snap-tutorial-spark-submit/8953) to validate and start utilizing your 
Kubernetes cluster for big data workloads.

Don't forget to check out the interactive [shells](https://discourse.charmhub.io/t/spark-client-snap-tutorial-interactive-mode/8954) for Scala and Python. 
They can save you a lot of time and debugging effort for authoring Spark jobs in the Kubernetes environment.

Check out the [How-Tos](https://discourse.charmhub.io/t/spark-client-snap-how-to-manage-spark-accounts/8959) section for a list of useful 
commands that will make your life easy working with the Spark client. If Python is your thing, then you can 
also manage your service accounts via a Python [library](https://discourse.charmhub.io/t/spark-client-snap-how-to-python-api/8958)

If you already have a _**Charmed Kubernetes**_ setup, check out the sections for 
using _**spark-client**_ with [Charmed Kubernetes](https://discourse.charmhub.io/t/spark-client-snap-how-to-run-on-charmed-kubernetes/8960) as snap 
and [Charmed Kubernetes From Pod](https://discourse.charmhub.io/t/spark-client-snap-how-to-run-on-k8s-in-a-pod/8961) within the pod.

Further documentation can be found in [Discourse](https://discourse.charmhub.io/t/spark-client-snap-documentation/8963)

## Common Mistakes to Avoid
Spark on Kubernetes is a complex environment with many moving parts. Sometimes, small mistakes can
take a lot of time to debug and figure out.
Follow our list of [common mistakes](https://discourse.charmhub.io/t/spark-client-snap-tutorial-common-gotchas/8955) to avoid while setting up 
and playing with Spark on Kubernetes.

## Contributing
The spark-client snap is an initiative from Canonical to simplify and encourage the adoption of Apache Spark for Kubernetes environments.
We are excited to share this initiative with the community. Although the project is in it's 
nascent stages, we are always on
the lookout to collaborate with great engineers. If you think you have a great idea to delight 
the Spark community, follow and engage with us on [Github](https://github.com/canonical/spark-client-snap) 
and [Discourse](https://discourse.charmhub.io/tag/spark).

