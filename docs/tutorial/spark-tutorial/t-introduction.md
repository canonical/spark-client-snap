## Charmed Spark Solution Tutorial

### Introduction

Apache Spark is a data processing framework that can quickly perform processing tasks on very large data sets, distributing data processing tasks across multiple computers and perfectly matching the needs of people working with big data and machine learning.

During the past few years, Apache Spark has gained significant interest and attention in the big data community and has now been established as a preferred tool for big data processing. Spark is now preferred over it's main competitor Apache Hadoop for data processing. The major features that made it popular over Hadoop were its ability to process data in real time, and the architecture that enabled it to store and process data in internal memory compared to extensive usage of external storage in Apache Hadoop. Moreover, Spark has built in support for several programming languages like R, Scala, Python, Java, C# and F# and has built in integrations for streaming, machine learning and SQL. It is easy to integrate Spark with Kafka, ElasticSearch, Redis, Cassandra, MySQL, PostreSQL and many more.

The Apache Spark architecture consists of a driver program which contains the application logic, that talks with the cluster manager that provisions and manages the resources needed for multiple executors to run the workload. The job is broken down into smaller jobs and distributed to the worker nodes, the execution of which is controlled by the driver program.

Apache Spark consists of Spark Core along with different built in modules like Spark SQL, MLlib, GraphX and Spark Streaming for SQL support, machine learning, graph processing and streaming support respectively.

There are several cluster managers supported by Spark, which are:
1. Standalone 
2. Apache Mesos (deprecated)
3. Hadoop YARN
4. Kubernetes

Since 2018, Apache Spark can now be run on top of Kubernetes. However, getting Apache Spark to work with Kuberenetes is not that simple and straightforwar and has a steep learning curve. Charmed Spark is a Canonical product that aims to solve this problem by providing users with everything that is needed to run Apache Spark on Kubernetes. It is a set of Canonical supported artifacts that makes running Spark on top of Kubernetes seamless, secure and production-ready. The following are the components that are included in Charmed Spark solution:
1. Spark Rock OCI Image (Provides a reliable Spark image to be used in Spark jobs)
2. Spark Client Snap (Simplifies client interaction with a Spark K8s cluster)
3. Observability charms (Provides charms to manage Web UIs services like Spark History Server and Grafana to monitor spark jobs via Juju)

The Spark rock image is used to run containers in the executor pods by Spark. The user can submit jobs to the Spark cluster using the spark-client snap. The snap also enables users to create Kubernetes service accounts and set configurations to integrate Spark with other applications. Finally, the history, status and metrics of the jobs can be viewed and analyzed by using the observability charms that are deployed via Juju.

The sections that follow takes you through a comprehensive tutorial on how to submit jobs to Spark cluster, how to interact with it, how to view the results, how to process streaming data and how to monitor the status of the jobs in it.

This tutorial can be divided into the following sections:
1. Introduction to Spark and Charmed Spark 
2. Setting up Environment for the Tutorial
3. Submitting Jobs with Spark Submit
4. Interacting with Spark using interactive shells
5. Streaming Workload with Charmed Spark
6. Monitoring with Spark History Server
7. Monitoring with Canonical Observability Stack
8. Wrapping Up