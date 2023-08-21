# Charmed Spark Documentation

Charmed Spark is a set of Canonical supported artifacts (including charms, ROCK OCI images and SNAPs) that makes operating Spark workloads on Kubernetes seamless, secure and production-ready. 

The solution helps to simplify user interaction with Spark applications and the underlying Kubernetes cluster whilst retaining the traditional semantics and command line tooling that users already know. Operators benefit from straightforward, automated deployment of Spark components (e.g. Spark History Server) to the Kubernetes cluster, using [Juju](https://juju.is/). 

Deploying Spark applications to Kubernetes has several benefits over other cluster resource managers such as Apache YARN, as it greatly simplifies deployment, operation, authentication while allowing for flexibility and scaling. However, it requires knowledge on Kubernetes, networking and coordination between the different components of the Spark ecosystem in order to provide a scalable, secure and production-ready environment. As a consequence, this can significantly increase complexity for the end user and administrators, as a number of parameters need to be configured and prerequisites must be met for the application to deploy correctly or for using the Spark CLI interface (e.g. pyspark and spark-shell). 
Charmed Spark helps to address these usability concerns and provides a consistent management interface for operations engineers and cluster administrators who need to manage enablers like Spark History Server.

The Spark Client Snap is a utility client application that allows for running Apache Spark on Kubernetes in a simple and seamless manner. All necessary components are packed in a single confined [Snap](https://snapcraft.io/) package:

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
| 2     | e-component-overview           | [Component Overview]()                                                                                               |
| 2     | e-configuration                | [Spark Client Hierarchical Configuration](/t/spark-client-snap-explanation-hierarchical-configuration-handling/8956) |


# Redirects

[details=Mapping table]
| Path | Location |
| ---- | -------- |
[/details]