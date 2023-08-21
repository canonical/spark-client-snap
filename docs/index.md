# Charmed Spark Documentation

The Spark Client Snap is a utility client application that allows for running Apache Spark on Kubernetes in a simple and seamless manner. All necessary components are packed in a single confined [Snap](https://snapcraft.io/) package:

* [Apache Spark](https://spark.apache.org/downloads.html) (binaries, executables and libraries)
* [spark8t](https://github.com/canonical/spark-k8s-toolkit-py) Python package to enhance Spark capabilities allowing to manage Spark jobs and service accounts, with hierarchical level of configuration
* Expose simple Snap commands to run and manage Spark Jobs

The `spark-client` Snap can be used to deploy and manage Apache Spark on different Kubernetes distributions, like
* [microk8s](https://microk8s.io/), which is the simplest production-grade conformant K8s. Lightweight and focused. 
Single command install on Linux, Windows and macOS.
    * Setup instructions are available in the Spark Tutorial [Set up the environment chapter](https://discourse.charmhub.io/t/spark-client-snap-tutorial-setup-environment/8951)
* [Charmed Kubernetes](https://ubuntu.com/kubernetes/charmed-k8s), which is a platform independent, model-driven distribution of Kubernetes powered by [juju](https://juju.is/) 

The `spark-client` Snap can effectively be used by:
* cluster administrators, who create and manage Spark service accounts (as shown [here](/t/spark-client-snap-tutorial-setup-environment/8952)) 
* developers and data-scientists, who need to launch Spark Jobs (as shown [here](/t/spark-client-snap-tutorial-spark-submit/8953)) or perform interactive analysis
using `pyspark` and `spark-shell`  (as shown [here](https://discourse.charmhub.io/t/spark-client-snap-tutorial-interactive-mode/8954))

The spark-client snap can be installed such as:
```
snap install spark-client --edge
```


## Project and community

Spark Client Snap is an official distribution of Apache Spark. It’s an open-source project that welcomes community contributions, suggestions, fixes and constructive feedback.
- [Read our Code of Conduct](https://ubuntu.com/community/code-of-conduct)
- [Join the Discourse forum](https://discourse.charmhub.io/tag/spark)
- [Contribute and report bugs](https://github.com/canonical/spark-client-snap)


# Navigation

| Level | Path                           | Navlink                                                                                                              |
|-------|--------------------------------|----------------------------------------------------------------------------------------------------------------------|
| 1     | overview                       | [Overview](/t/spark-client-snap-documentation/8963)                                                                  | 
| 1     | tutorial                       | [Tutorial]()                                                                                                         |
| 2     | t-overview                     | [1. Introduction](/t/spark-client-snap-tutorial/8957)                                                                |
| 2     | t-setup-environment            | [2. Set up the environment](/t/spark-client-snap-tutorial-setup-environment/8951)                                    |
| 2     | t-spark-service-accounts       | [3. Manage Spark service accounts](/t/spark-client-snap-tutorial-setup-environment/8952)                             |
| 2     | t-spark-job                    | [4. Submit a Spark Job](/t/spark-client-snap-tutorial-spark-submit/8953)                                             |
| 2     | t-spark-shells                 | [5. Use interactive shells](/t/spark-client-snap-tutorial-interactive-mode/8954)                                     |
| 2     | t-tips-and-tricks              | [6. Tips and Tricks](/t/spark-client-snap-tutorial-common-gotchas/8955)                                              |
| 1     | how-to                         | [How To]()                                                                                                           |
| 2     | h-setup-k8s                    | [Setup Environment](/t/charmed-spark-k8s-documentation-how-to-setup-k8s-environment/11618)                           |
| 2     | h-manage-service-accounts      | [Manage Service Accounts](/t/spark-client-snap-how-to-manage-spark-accounts/8959)                                    |
| 2     | h-use-spark-client-from-python | [Use the Spark Client Python API](/t/spark-client-snap-how-to-python-api/8958)                                       |
| 2     | h-run-on-k8s-pod               | [Run on K8s pods](/t/spark-client-snap-how-to-run-on-k8s-in-a-pod/8961)                                              |
| 2     | h-deploy-spark-history         | [Deploy Spark History Server](/t/charmed-spark-k8s-documentation-how-to-deploy-spark-history-server/10979)           |
| 2     | h-spark-streaming              | [Run Spark Streaming Jobs](/t/charmed-spark-how-to-run-a-spark-streaming-job/10880)                                  |
| 1     | reference                      | [Reference]()                                                                                                        |
| 2     | r-requirements                 | [Requirements](/t/spark-client-snap-reference-requirements/8962)                                                     |
| 1     | explanation                    | [Explanation]()                                                                                                      |
| 2     | e-configuration                | [Spark Client Hierarchical Configuration](/t/spark-client-snap-explanation-hierarchical-configuration-handling/8956) |


# Redirects

[details=Mapping table]
| Path | Location |
| ---- | -------- |
[/details]