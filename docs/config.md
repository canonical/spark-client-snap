### Configuration Setup and Runtime behavior for Apache Spark client
Apache Spark comes with a lots of configuration properties which can be set. The list is pretty extensible as well.

Passing each and every configuration in command line is not tenable, so Apache Spark supports the use of properties 
files where the user can place most of the configuration for reuse across submissions. 

In addition, the user can still add or override more configuration values in this file in the command line.

For this Spark client, Canonical has come up with a rich set of options for the user to specify configuration properties and also override
them in a spirit similar to Apache Spark.

Following is the hierarchy of configurations merged during spark-submit
* Canonical provided immutable defaults
* Set up time generated immutable defaults kept as a secret collection in Kubernetes. Valid across sessions and machines. Please refer to the [setup](/docs/setup.md) section, specifically the part about ```service-account```. 
* Properties in file specified via environment variable (```$SNAP_SPARK_ENV_CONF```) valid across spark-submit commands in a shell session.
* Properties in file specified as a parameter (```--properties-file```) in spark-submit command
* Properties specified as parameters (list of ```--conf```) in spark-submit command.

The configurations are resolved i.e. merged preferring the latter sources over the previous ones during spark-submit.


