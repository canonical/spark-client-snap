## Interacting with Spark using Interactive Shell

Spark comes with an interactive shell that provides a simple way to learn the API. It is available in either Scala or Python. In this section, we're going to play around a bit with Spark's shell to interact directly with the Spark cluster.

### PySpark Shell

Spark comes with a built-in Python shell where we can execute commands interactively against Spark cluster using Python programming language.

PySpark shell can be launched with `spark-client` snap as:

```bash
spark-client.pyspark \
  --username spark --namespace spark
```

Once the shell is open and ready, you should see a prompt simlar to the following:

```
Welcome to
      ____              __
     / __/__  ___ _____/ /__
    _\ \/ _ \/ _ `/ __/  '_/
   /__ / .__/\_,_/_/ /_/\_\   version 3.4.1
      /_/

Using Python version 3.10.12 (main, Jun 11 2023 05:26:28)
Spark context Web UI available at http://172.31.29.134:4040
Spark context available as 'sc' (master = k8s://https://172.31.29.134:16443, app id = spark-b364a0a9a2cb41f3a713c62b900fbd82).
SparkSession available as 'spark'.
>>> 
```

When you open the PySpark shell, Spark spawns a couple of executor pods in the background to process the commands. You can see them by fetching the list of pods in the `spark` namespace.

```bash
kubectl get pods -n spark
```

You should see output lines similar to the following:
```bash
pysparkshell-xxxxxxxxxxxxxxxx-exec-1              1/1     Running            0          xs
pysparkshell-xxxxxxxxxxxxxxxx-exec-2              1/1     Running            0          xs
```

As you can see, PySpark spawned two executor pods within the `spark` namespace. This is the namespace that we provided as a value to `--namespace` argument when launching `pyspark`. It is in these executor pods that your commands will be executed. Since we opened the PySpark shell using `spark-client` snap installed in the host machine, the driver program is running in the host machine itself.

One good thing about the shell is that the Spark context and session is already pre-loaded onto the shell and can be easily accessed with variables `sc` and `spark` respectively. This shell is just like a regular Python shell, with Spark context loaded on top of it.

For start, you can print 'hello, world!' just like you'd do in a Python shell.

```python
>>> print('hello, world!')

hello, world!
```

Let's try a simple example of counting the number of vowel characters in a string. The following is the string that we are going to use:

```python
lines = """Canonical's Charmed Data Platform solution for Apache Spark runs Spark jobs on your Kubernetes cluster.
You can get started right away with MicroK8s - the mightiest tiny Kubernetes distro around! 
The spark-client snap simplifies the setup to run Spark jobs against your Kubernetes cluster. 
Spark on Kubernetes is a complex environment with many moving parts.
Sometimes, small mistakes can take a lot of time to debug and figure out.
"""
```

The following is a function that returns the number of vowel characters in the string:

```python
def count_vowels(text: str) -> int:
  count = 0
  for char in text:
    if char.lower() in "aeiou":
      count += 1
  return count
```

To test this function, the string `lines` can now be passed into it and the number of vowels is printed to the console as follows:

```python
>>> count_vowels(lines)
128
```

Since Spark is a distributed processing framework, we can split up this task and parallellize it over multiple executor pods. This parallelization can be done as simply as:

```python
>>> from operator import add
>>> spark.sparkContext.parallelize(lines.splitlines(), 2).map(count_vowels).reduce(add)
128
```

Here, we parallelize the the tax into two executors (passed as an argument to `parallelize` function), where each line is processed by an executor pod. The number of vowels in each line is then added up to calculate the total number of occurrences of vowel characters in the string. This kind of parallelization of task is particularly useful in processing very large data sets which helps in reducing the processing time significantly.

To exit from PySpark shell, you can simply run `exit()` or press `Ctrl` + Z key combination.


### Scala Shell
Spark comes with a built-in interactive Scala shell as well. Enter the following command to enter an interactive Scala shell:

```bash
spark-client.spark-shell --username spark --namespace spark
```

Once the shell is open and ready, you should see a prompt simlar to the following:

```
Welcome to
      ____              __
     / __/__  ___ _____/ /__
    _\ \/ _ \/ _ `/ __/  '_/
   /___/ .__/\_,_/_/ /_/\_\   version 3.4.1
      /_/
         
Using Scala version 2.12.17 (OpenJDK 64-Bit Server VM, Java 11.0.20.1)
Type in expressions to have them evaluated.
Type :help for more information.

scala> 
```

Just as in PySpark shell, the spark context and spark session are readily available in the shell as `sc` and `spark` respectively. Moreover, new executor pods are created in `spark` namespace in order to execute the commands, just like in the PySpark shell.

The example of counting the vowel characters can be equivalently run in Scala with the following lines:

```scala
val lines = """Canonical's Charmed Data Platform solution for Apache Spark runs Spark jobs on your Kubernetes cluster.
You can get started right away with MicroK8s - the mightiest tiny Kubernetes distro around! 
The spark-client snap simplifies the setup to run Spark jobs against your Kubernetes cluster. 
Spark on Kubernetes is a complex environment with many moving parts.
Sometimes, small mistakes can take a lot of time to debug and figure out.
"""

def countVowels(text: String): Int = {
  text.toLowerCase.count("aeiou".contains(_))
}

sc.parallelize(lines.split("\n"), 2).map(countVowels).reduce(_ + _)
```

To exit from the Scala shell, simply press Ctrl + C key combination.

Interactive shells are a great way to try out experiments and to learn the basics of the Spark. For a more advanced use case, jobs can be submitted to the Spark cluster as scripts using `spark-submit`. That's what we will do in the next section.
<!-- 
Let's try reading a file using Spark. Since the executor pods in Kubernetes would all require shared access to the file, we're going to first upload the file to S3 bucket and then proceed to read it using Spark. The file that we're going to use in this tutorial can be downloaded from here. You can upload it to the bucket using Minio UI using AWS CLI tool in a new shell as follows:

```bash
aws s3 cp ~/Downloads/lines.txt s3://spark-tutorial/lines.txt --profile spark-tutorial
```

Now, let's try reading this file from Spark. In the PySpark shell, this is as easy as running the following:

```python
>>> df = spark.read.text("s3://spark-tutorial/lines.txt")
```

Make sure to provide the correct path for `lines.txt` to where you have downloaded them.

Let's write some lines to a file named `/tmp/lines.txt`. We'll then read the contents of this file from the PySpark shell. Writing lines is as easy as the following in Python.

```python
lines = """Canonical's Charmed Data Platform solution for Apache Spark runs Spark jobs on your Kubernetes cluster.
You can get started right away with MicroK8s - the mightiest tiny Kubernetes distro around! 
The spark-client snap simplifies the setup to run Spark jobs against your Kubernetes cluster. 
Spark on Kubernetes is a complex environment with many moving parts.
Sometimes, small mistakes can take a lot of time to debug and figure out.
"""

with open("/tmp/lines.txt", "w") as f:
  f.write(lines)
```

Let's try to load a file
Let's open a new shell and create a dummy text file at `/tmp/somelines.txt` and add a few lines to it. We'll then read the contents of this file from the PySpark shell.

```txt
Canonical's Charmed Data Platform solution for Apache Spark runs Spark jobs on your Kubernetes cluster.
You can get started right away with MicroK8s - the mightiest tiny Kubernetes distro around! 
The spark-client snap simplifies the setup to run Spark jobs against your Kubernetes cluster. 
Spark on Kubernetes is a complex environment with many moving parts.
Sometimes, small mistakes can take a lot of time to debug and figure out.
```

```python
>>> df = spark.read.text("/home/ubuntu/.kube/config")
```

As an experiment, let's try reading text from a text file and then count the Kubeconfig file we exported earlier and count the number of lines that contain the word "microk8s" on it.

For that, let's first read the file onto a dataframe using the `spark.read.text` function:

```python
>>> df = spark.read.text("/home/ubuntu/.kube/config") # Note that the username could be different in your system

>> df.first() # First row in the dataframe

```


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

After the last command is executed, the value of Pi can be seen as an output in the console. -->