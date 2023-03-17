# Spark Client Snap tutorial

The Spark Client Snap is a utility client application that makes running Apache Spark on Kubernetes simple 
and seamless.
As a first step this tutorial shows you how to get a simple Kubernetes distribution up and running and 
use the latter to run Spark Jobs, either as a separated process or interactively. 
Through this tutorial you will learn a variety of operations, ranging from creating the service account, 
configure and manage them, to then used them for actual computation. We will also 
provide towards the end a list of tips and tricks of common problems you may face when using Spark on Kubernetes. 


This tutorial has be splitted in the following sections:

- Set up your environment with microK8s and the Spark Client snap.
- Setup and manage Spark service accounts
- Submit a Spark Job using an enhanced version of `spark-submit`
- Perform a simple analysis using `spark-shell` using Scala
- Perform a simple analysis using `pyspark` using Python
- Review a list of common tips, tricks and issues you may face when using Spark on Kubernetes 

While this tutorial intends to guide and teach you as you deploy Apache Spark, it will be most beneficial if you already have a familiarity with: 
- Basic terminal commands.
- Apache Spark concepts and Kubernetes basic knowledge.

This tutorial can be run as in on the latest stable LTS version of Ubuntu 22.04.  

## Step-by-step guide

Here’s an overview of the steps required with links to our separate tutorials that deal with each individual step:
* [Set up the environment](https://discourse.charmhub.io/t/spark-client-snap-tutorial-setup-environment/8951)
* [Manage Spark service accounts](https://discourse.charmhub.io/t/spark-client-snap-tutorial-setup-environment/8952)
* [Submit a Spark Job](https://discourse.charmhub.io/t/spark-client-snap-tutorial-spark-submit/8953)
* [Use the interactive shells](https://discourse.charmhub.io/t/spark-client-snap-tutorial-interactive-mode/8954)
* [Tips and Tricks](https://discourse.charmhub.io/t/spark-client-snap-tutorial-common-gotchas/8955)

