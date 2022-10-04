### Interactive Spark Shell
For interactive use cases, spark-client snap ships with Apache Spark's spark-shell utility.

It's a useful tool to quickly validate your assumptions about Spark in Scala before finding out after an actual long running job failure.

Before proceeding further, please note that the spark-shell maintains it's history in a file namely ```~/.scala_history```.

So we need to first allow the snap to write to this location. Please run the following command to enable this write access.

```bash
sudo snap connect spark-client:enable-scala-history
```

Great! Now we can test out our spark-shell setup with the official Pi example from the Spark distribution.

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