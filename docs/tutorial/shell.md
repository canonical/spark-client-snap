## Run Spark Interactively

Apache Spark comes with two shells to be used in interactive mode:
* `spark-shell`, that is built on top of the Scala REPL shell
* `pyspark`, that is built on top of the python interpreter shell

### Interactive Spark Shell
For interactive use cases, spark-client snap ships with Apache Spark's spark-shell utility.

It's a useful tool to quickly validate your assumptions about Spark in Scala before finding out after an actual long running job failure.

Great! Let us test out our spark-shell setup with the official Pi example from the Spark distribution.

```shell
$ spark-client.spark-shell
....
....
Spark session available as 'spark'.
Welcome to
      ____              __
     / __/__  ___ _____/ /__
    _\ \/ _ \/ _ `/ __/  '_/
   /___/ .__/\_,_/_/ /_/\_\   version 3.3.0
      /_/
....
....
scala> import scala.math.random
scala> val slices = 1000
scala> val n = math.min(100000L * slices, Int.MaxValue).toInt
scala> val count = spark.sparkContext.parallelize(1 until n, slices).map { i => val x = random * 2 - 1; val y = random * 2 - 1;  if (x*x + y*y <= 1) 1 else 0;}.reduce(_ + _)
scala> println(s"Pi is roughly ${4.0 * count / (n - 1)}")
scala> :quit
```

### Interactive PySpark Shell
For interactive use case using python shell, spark-client snap ships with Apache Spark's pyspark utility.

Make sure python is installed on your system. Then, execute the following commands to validate your pyspark setup with the official Pi example
that ships with Apache Spark.

```bash
$ spark-client.pyspark
....
....
Welcome to
      ____              __
     / __/__  ___ _____/ /__
    _\ \/ _ \/ _ `/ __/  '_/
   /__ / .__/\_,_/_/ /_/\_\   version 3.3.0
      /_/
....
....
>>> from random import random
>>> from operator import add
>>> partitions = 1000
>>> n = 100000 * partitions
>>> def f(_: int) -> float:
...     x = random() * 2 - 1
...     y = random() * 2 - 1
...     return 1 if x ** 2 + y ** 2 <= 1 else 0
...
>>> count = spark.sparkContext.parallelize(range(1, n + 1), partitions).map(f).reduce(add)
>>> print("Pi is roughly %f" % (4.0 * count / n))
>>> quit()
```
