## Introduction

Canonical's Charmed Data Platform solution for Apache Spark runs Spark jobs on your Kubernetes cluster. 
You can get started right away with [Microk8s](https://microk8s.io/) - the mightiest tiny Kubernetes distro around! 
You can install MicroK8s on your Ubuntu laptop, workstation, or nodes in your workgroup or server cluster with just one command - ```snap install microk8s --classic```. Learn more at [microk8s.io](https://microk8s.io/).

## Spark-client Snap
The ***spark-client*** snap includes the scripts [spark-submit](/docs/submit.md), [spark-shell](/docs/shell.md), [pyspark](/docs/pyspark.md) and other tools for managing ***Apache Spark*** jobs for ***Kubernetes***.

## Setup
The spark-client snap simplifies the setup to run Spark jobs against your Kubernetes cluster. Please follow the instructions in the [setup](/docs/setup.md) section to get started.

Do check out the section on [config resolution](/docs/config.md) to understand how [spark-submit](/docs/submit.md) actually resolves the configuration properties coming from a diverse set of available sources.

## Play!
Once the [setup](/docs/setup.md) is complete, please follow the Spark job [submission guide](/docs/submit.md) to validate and start utilizing your 
Kubernetes cluster for big data workloads.

Don't forget to check out the interactive shells for [Scala](/docs/shell.md) and [Python](/docs/pyspark.md). 
They can save you a lot of time and debugging effort for authoring Spark jobs in the Kubernetes environment.

Check out the [How-Tos](/docs/howto.md) section for a list of useful commands that will make your life easy working with the Spark client. 

## Common Mistakes to Avoid
Spark on Kubernetes is a complex environment with many moving parts. Sometimes, small mistakes can take a lot of time to debug and figure out.
Please follow our list of [common mistakes](/docs/gotchas.md) to avoid while setting up and playing with Spark on Kubernetes.

## Contributing
We are excited to share this initiative with the community. Although the project is in it's nascent stages, we are always on
the lookout to collaborate with great engineers. If you think you have a great idea to delight the Spark community, please follow
the [Contributing](/docs/contributing.md) guide to connect with us!
