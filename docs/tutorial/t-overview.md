# `spark-client` Snap tutorial

The `spark-client` Snap package delivers Spark utility client applications, that allow for simple and seamless usage of Apache Spark on Kubernetes.

First this tutorial provides instructions on how to get a simple Kubernetes distribution up and running. Then it describes how to run Spark Jobs, either as a separate process or interactively. 

Through this tutorial you will learn a variety of operations, ranging from service account management, to actual computation. Finally we also provide a list of tips and tricks of common problems you may face when using Spark on Kubernetes. 

This tutorial has been split into the following sections:

1. [Seting up your environment with microK8s and the `spark-clinet` snap](https://discourse.charmhub.io/t/spark-client-snap-tutorial-setup-environment/8951)
1. [Setup and manage Spark service accounts](https://discourse.charmhub.io/t/spark-client-snap-tutorial-setup-environment/8952)
1. [Submit a Spark Job using an enhanced version of `spark-submit`](https://discourse.charmhub.io/t/spark-client-snap-tutorial-spark-submit/8953)
1. [Perform a simple analysis using `spark-shell` using Scala, and `pyspark` using Python](https://discourse.charmhub.io/t/spark-client-snap-tutorial-interactive-mode/8954)
1. [Review a list of common tips, tricks and issues you may face when using Spark on Kubernetes](https://discourse.charmhub.io/t/spark-client-snap-tutorial-common-gotchas/8955)

While this tutorial intends to guide and teach you to deploy Apache Spark using Charmed Spark, it will be most beneficial if you are familiar with: 
- Basic terminal commands.
- Apache Spark concepts and Kubernetes basic knowledge.

This tutorial can be run as in on the latest stable LTS version of Ubuntu 22.04.

***

* Next: [ Setup Kubernetes and Spark Client Snap](https://discourse.charmhub.io/t/spark-client-snap-tutorial-setup-environment/8951)
* [Charmed Spark Documentation](https://discourse.charmhub.io/t/charmed-spark-documentation/8963)