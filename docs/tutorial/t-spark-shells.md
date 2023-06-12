## Run Spark Interactively

Apache Spark comes with two shells to be used in interactive mode:
* `spark-shell`, that is built on top of the Scala REPL shell
* `pyspark`, that is built on top of the python interpreter shell

### Interactive Spark Shell
For interactive use cases, spark-client snap ships with Apache Spark's spark-shell utility.

It's a useful tool to quickly validate your assumptions about Spark in Scala before finding out after an actual long running job failure.

Great! Let us test out our spark-shell setup with a simple example.

```shell
$ spark-client.spark-shell
....
....
Spark session available as 'spark'.
Welcome to
      ____              __
     / __/__  ___ _____/ /__
    _\ \/ _ \/ _ `/ __/  '_/
   /___/ .__/\_,_/_/ /_/\_\   version 3.3.2
      /_/
....
....
scala> import scala.math.random
scala> val slices = 1000
scala> val n = math.min(100000L * slices, Int.MaxValue).toInt
scala> val squares_sum = spark.sparkContext.parallelize(1 until n, slices).map { i => i * i }.reduce(_ + _)
scala> println(s"Sum of squares is ${squares_sum}")
scala> :quit
```

### Interactive PySpark Shell
For interactive use case using python shell, spark-client snap ships with Apache Spark's pyspark utility.

Make sure python is installed on your system. Then, execute the following commands to validate 
that your pyspark setup is working.

```bash
$ spark-client.pyspark
....
....
Welcome to
      ____              __
     / __/__  ___ _____/ /__
    _\ \/ _ \/ _ `/ __/  '_/
   /__ / .__/\_,_/_/ /_/\_\   version 3.3.2
      /_/
....
....
>>> from operator import add
>>> partitions = 1000
>>> n = 100000 * partitions
>>> def square(x: int) -> float:
...     return x ** 2
...
>>> squares_sum = spark.sparkContext.parallelize(range(1, n + 1), partitions).map(square).reduce(add)
>>> print("Sum of squares is %f" % (squares_sum))
>>> quit()
```

***

 * Previous: [Submit a Spark Job](https://discourse.charmhub.io/t/spark-client-snap-tutorial-spark-submit/8953)
 * Next: [Tips and Tricks](https://discourse.charmhub.io/t/spark-client-snap-tutorial-common-gotchas/8955)