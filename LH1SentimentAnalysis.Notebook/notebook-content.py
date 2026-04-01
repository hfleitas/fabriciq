# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "6dc2c94a-578b-4527-bdef-7e7f36d7da43",
# META       "default_lakehouse_name": "LH1",
# META       "default_lakehouse_workspace_id": "65324039-09f8-4ecd-897c-c3e6b82aab52",
# META       "known_lakehouses": [
# META         {
# META           "id": "6dc2c94a-578b-4527-bdef-7e7f36d7da43"
# META         }
# META       ]
# META     }
# META   }
# META }

# MARKDOWN ********************

# # Sentiment Analysis — Invoke User Data Function
# 
# This notebook **invokes** the `analyze_transcript_sentiment` User Data Function deployed in your workspace,
# then writes the results to a Delta table **`call_sentiment_analysis`** in Tables/.
# 
# **Prerequisites:**
# 1. Deploy `sentiment_udf.py` as a User Data Functions item in the BCDR1 workspace.
# 2. Add `textblob` via Library Management in the UDF item.
# 3. Add a connection to the LH1 Lakehouse with alias `LH1`.
# 4. Publish the function.

# CELL ********************

# ── Cell 1: Invoke the User Data Function ──

# Get functions from the "Sentiment" UDF item
myFunctions = notebookutils.udf.getFunctions('Sentiment', '65324039-09f8-4ecd-897c-c3e6b82aab52')

# Invoke the function
result = myFunctions.analyze_transcript_sentiment(fileName="claims_call_transcript.txt")

print(f"UDF returned {len(result)} scored lines")
result[:3]  # Preview first 3

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# ── Cell 2: Convert UDF results to Spark DataFrame ──
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

# Coerce numeric fields to float to avoid FloatType rejecting int values
float_fields = ["polarity", "confidencePositive", "confidenceNeutral", "confidenceNegative"]
clean_result = []
for row in result:
    r = dict(row)
    for f in float_fields:
        if f in r:
            r[f] = float(r[f])
    clean_result.append(r)

df = spark.createDataFrame(clean_result)
df.show(truncate=60)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# ── Cell 3: Save as Delta table ──
(df.write
 .format("delta")
 .mode("overwrite")
 .saveAsTable("call_sentiment_analysis"))

print("✓ Table 'call_sentiment_analysis' written to Tables/")
spark.sql("SELECT * FROM call_sentiment_analysis").show(truncate=60)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# ── Cell 4: Summary stats ──
print("=== Sentiment by Speaker ===")
spark.sql("""
    SELECT speaker, role,
           COUNT(*) as lines,
           ROUND(AVG(confidencePositive), 3) as avgPositive,
           ROUND(AVG(confidenceNeutral), 3) as avgNeutral,
           ROUND(AVG(confidenceNegative), 3) as avgNegative
    FROM call_sentiment_analysis
    GROUP BY speaker, role
""").show()

print("=== Sentiment Distribution ===")
spark.sql("""
    SELECT sentiment, COUNT(*) as count
    FROM call_sentiment_analysis
    GROUP BY sentiment
    ORDER BY count DESC
""").show()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
