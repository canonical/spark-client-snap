## Interacting with Spark using Interactive Shell

We can also interact with the Spark cluster directly using an interactive shell. There are two shells that are available:
1. Spark Shell (Scala)
2. PySpark (Python)


### Spark Shell

Spark shell is an interactive shell where you can directly interact with Spark cluster using Scala. The spark shell can be opened using the `spark-client` snap as:

```bash
spark-client.spark-shell \
  --username spark --namespace spark
```

Once you get inside the shell, you can type in the following commands line by line for them to be executed in the shell:

```scala
import scala.math.random
val slices = 100
val n = math.min(100000L * slices, Int.MaxValue).toInt
val count = spark.sparkContext.parallelize(1 until n, slices).map { i => val x = random * 2 - 1; val y = random * 2 - 1;  if (x*x + y*y <= 1) 1 else 0;}.reduce(_ + _)
println(s"Pi is roughly ${4.0 * count / (n - 1)}")
```

After the last command is executed, the value of Pi can be seen as an output in the console.


### PySpark
Pyspark is an interactive shell where you can directly interact with Spark cluster using Python. The PySpark shell can be opened using the `spark-client` snap as:

```bash
spark-client.pyspark \
  --username spark --namespace spark
```

Once you get inside the shell, you can type in the following commands line by line for them to be executed in the shell:

```python
from random import random

from pyspark.context import SparkContext
from pyspark.sql.session import SparkSession

sc = SparkContext()
spark = SparkSession(sc)
for conf in spark.sparkContext.getConf().getAll():
    print(conf)
partitions = 10
n = 1000000 * partitions


def f(_: int) -> float:
    x, y = random(), random()
    return x * x + y * y < 1


count = spark.sparkContext.parallelize(range(n), partitions).filter(f).count()
print("Pi is roughly %f" % (4.0 * count / n))
```

After the last command is executed, the value of Pi can be seen as an output in the console.