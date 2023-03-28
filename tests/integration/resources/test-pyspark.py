import sys
from random import random
from operator import add
from pyspark.context import SparkContext
from pyspark.sql.session import SparkSession
sc = SparkContext()
spark = SparkSession(sc)
for conf in spark.sparkContext.getConf().getAll(): print (conf)
partitions = 10
n = 1000000 * partitions
def f(_: int) -> float:
    x, y = random(), random()
    return x * x + y * y < 1
count = spark.sparkContext.parallelize(range(n), partitions).filter(f).count()
print ("Pi is roughly %f" % (4.0 * count / n))