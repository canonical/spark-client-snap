## Common Gotchas

An incomplete summary of tips, tricks and gotchas to run Apache Spark on Kubernetes smoothly, even in small, local environments

* For `spark-client.spark-submit` to work correctly, make sure DNS is enabled.
  * For example, if you are working with MicroK8s,  run ```microk8s enable dns``` before submitting the spark job
* In case executor pods fail to schedule due to insufficient CPU resources, make [fractional](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#resource-units-in-kubernetes) CPU requests
* Don't forget to enable default Kubernetes config access for the snap, otherwise it will complain not able to find kubeconfig file even after providing the valid default kubeconfig file
* Make sure the namespace provided to `spark-submit` is valid and the service account provided belongs to that namespace. To keep it simple, use the `setup-spark-k8s` script to create the account.
* When working with k8s control plane url, please note that it has a prefix something like `k8s://https://`


***

* Previous: [ Use the interactive shells](https://discourse.charmhub.io/t/spark-client-snap-tutorial-interactive-mode/8954)
 * [Charmed Spark Documentation](https://discourse.charmhub.io/t/charmed-spark-documentation/8963)