import scala.math.random
val slices = 10
val n = math.min(100000L * slices, Int.MaxValue).toInt
val count = spark.sparkContext.parallelize(1 until n, slices).map { i => val x = random * 2 - 1; val y = random * 2 - 1;  if (x*x + y*y <= 1) 1 else 0;}.reduce(_ + _)
println(s"Pi is roughly ${4.0 * count / (n - 1)}")
System.exit(0)