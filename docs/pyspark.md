### Interactive PySpark Shell
For interactive use case using python shell, spark-client snap ships with Apache Spark's pyspark utility.

Make sure python is installed on your system. Then, execute the following commands to validate your pyspark setup with the official Pi example
that ships with Apache Spark.

```bash
$ spark-client.pyspark --conf spark.driver.host={LOCALHOST_IP}
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