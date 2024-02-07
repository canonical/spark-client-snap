from operator import add
from pyspark.sql import SparkSession


def count_vowels(text: str) -> int:
  count = 0
  for char in text:
    if char.lower() in "aeiou":
      count += 1
  return count

# Create a Spark session 
spark = SparkSession\
        .builder\
        .appName("SubmitExample")\
        .getOrCreate()

lines = spark.sparkContext.textFile("s3a://spark-tutorial/README.md")

n = lines.map(count_vowels).reduce(add)
print(f"The number of vowels in the string is {n}")

spark.stop()