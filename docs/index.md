## Spark Client Snap Documentation 
The Spark Client Snap is a utility client application that makes running Apache Spark on Kubernetes simple 
and seamless. It packages in a single confined [snap](https://snapcraft.io/):

* Apache Spark OCI Image compliant with Rock standards 
* Python package/CLI to enhance Spark capabilities/customization, allowing to create, configure and 
manage dedicated Spark service accounts, with hierarchical level of configuration
* Expose simple SNAP commands to run and manage Spark Jobs

The Spark Client Snap can be used to deploy and manage Apache Spark on different distribution of Kubernetes, like
* [microk8s](https://microk8s.io/), which is the simplest production-grade conformant K8s. Lightweight and focused. 
Single command install on Linux, Windows and macOS.
* [Charmed Kubernetes](https://ubuntu.com/kubernetes/charmed-k8s), which is a platform independent, model-driven distribution 
of Kubernetes powered by [juju](https://juju.is/) 

The Spark Client Snap can effectively be used by anyone in the pipeline of processing 
data using Spark, ranging from administrators, who create and manage Spark service accounts, to 
developers and data-scientists, who need to launch Spark Jobs or perform interactive analysis
using `pyspark` and `spark-shell`.


## Project and community

Spark Client Snap is an official distribution of Apache Spark. It’s an open-source project that welcomes community contributions, suggestions, fixes and constructive feedback.
- [Read our Code of Conduct](https://ubuntu.com/community/code-of-conduct)
- [Join the Discourse forum](https://discourse.charmhub.io/tag/spark)
- [Contribute and report bugs](https://github.com/canonical/spark-client-snap)


# Navigation

* [Set up the environment]()
* [Manage Spark service accounts]()
* [Submit a Spark Job]()
* [Use the interactive shells]()
* [Tips and Tricks](https://discourse.charmhub.io/t/spark-client-snap-tutorial-common-gotchas/8955)


| Level | Path                                | Navlink                                                                                                                                           |
|-------|-------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------|
| 1     | tutorial                            | [Tutorial]()                                                                                                                                      |
| 2     | tutorial-overview                   | [1. Introduction](https://discourse.charmhub.io/t/spark-client-snap-tutorial/8957)                                                                |
| 2     | tutorial-setup-environment          | [2. Set up the environment](https://discourse.charmhub.io/t/spark-client-snap-tutorial-setup-environment/8951)                                    |
| 2     | tutorial-spark-service-accounts     | [3. Manage Spark service accounts](https://discourse.charmhub.io/t/spark-client-snap-tutorial-setup-environment/8952)                             |
| 2     | tutorial-spark-job                  | [4. Submit a Spark Job](https://discourse.charmhub.io/t/spark-client-snap-tutorial-spark-submit/8953)                                             |
| 2     | tutorial-spark-shells               | [5. Use the spark-shell](https://discourse.charmhub.io/t/spark-client-snap-tutorial-interactive-mode/8954)                                        |
| 2     | tutorial-tips-and-tricks            | [7. Tips and Tricks](https://discourse.charmhub.io/t/spark-client-snap-tutorial-common-gotchas/8955)                                              |
| 1     | how-to                              | [How To]()                                                                                                                                        |
| 2     | how-to-manage-service-accounts      | [Manage Service Accounts](https://discourse.charmhub.io/t/spark-client-snap-how-to-manage-spark-accounts/8959)                                    |
| 2     | how-to-use-spark-client-from-python | [Use the Spark Client Python API](https://discourse.charmhub.io/t/spark-client-snap-how-to-python-api/8958)                                       |
| 2     | how-to-run-on-charmed-k8s           | [Run on Charmed Kubernetes](https://discourse.charmhub.io/t/spark-client-snap-how-to-run-on-charmed-kubernetes/8960)                              |
| 2     | how-to-run-on-k8s-pod               | [Run on K8s pods](https://discourse.charmhub.io/t/spark-client-snap-how-to-run-on-k8s-in-a-pod/8961)                                                                                                                               |
| 1     | reference                           | [Reference]()                                                                                                                                     |
| 2     | refs-requirements                   | [Requirements](https://discourse.charmhub.io/t/spark-client-snap-reference-requirements/8962)                                                                                                                                  |
| 1     | explanation                         | [Reference]()                                                                                                                                     |
| 2     | expl-configuration                  | [Spark Client Hierarchical Configuration](https://discourse.charmhub.io/t/spark-client-snap-explanation-hierarchical-configuration-handling/8956) |


# Redirects

[details=Mapping table]
| Path | Location |
| ---- | -------- |
[/details]