# Fabric notebook source


# CELL ********************

from pyspark.sql import functions as F
from pyspark.sql.types import DecimalType

table_name = "insurance_data.dbo.claims_fact"
df = spark.table(table_name)
df2 = df.withColumn("Claim_Amount", F.col("Claim_Amount").cast(DecimalType(18, 2)))
(df2.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(table_name))
spark.sql(f"DESCRIBE TABLE {table_name}").where("col_name = 'Claim_Amount'").show(truncate=False)

