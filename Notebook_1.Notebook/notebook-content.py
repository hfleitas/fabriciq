# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "warehouse": {
# META       "default_warehouse": "4777ad95-c7ab-4fcd-95a9-b8a1a6f75816",
# META       "known_warehouses": [
# META         {
# META           "id": "4777ad95-c7ab-4fcd-95a9-b8a1a6f75816",
# META           "type": "Lakewarehouse"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

{
  "cells": [
    {
      "cell_type": "code",
      "metadata": {
        "language": "python"
      },
      "source": [
        "from pyspark.sql import functions as F",
        "from pyspark.sql.types import DecimalType",
        "",
        "# If insurance_data Lakehouse is attached as default, dbo.claims_fact will work.",
        "# Otherwise use: insurance_data.dbo.claims_fact",
        "table_name = \"dbo.claims_fact\"",
        "",
        "df = spark.table(table_name)",
        "df2 = df.withColumn(\"Claim_Amount\", F.col(\"Claim_Amount\").cast(DecimalType(18, 2)))",
        "",
        "(",
        "    df2.write",
        "      .mode(\"overwrite\")",
        "      .option(\"overwriteSchema\", \"true\")",
        "      .saveAsTable(table_name)",
        ")",
        "",
        "# Verify",
        "spark.sql(f\"DESCRIBE TABLE {table_name}\").filter(\"col_name = 'Claim_Amount'\").show(truncate=False)"
      ]
    }
  ],
  "metadata": {},
  "nbformat": 4,
  "nbformat_minor": 5
}

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

spark.sql("DESCRIBE TABLE dbo.claims_fact").filter("col_name = 'Claim_Amount'").show(truncate=False)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

{
  "cells": [
    {
      "cell_type": "code",
      "metadata": {
        "language": "python"
      },
      "source": [
        "from pyspark.sql import functions as F",
        "from pyspark.sql.types import DecimalType",
        "",
        "table_name = \"dbo.claims_fact\"  # use \"insurance_data.dbo.claims_fact\" if needed",
        "",
        "df = spark.table(table_name)",
        "df_updated = df.withColumn(\"Claim_Amount\", F.col(\"Claim_Amount\").cast(DecimalType(18, 2)))",
        "",
        "(",
        "    df_updated.write",
        "      .mode(\"overwrite\")",
        "      .option(\"overwriteSchema\", \"true\")",
        "      .saveAsTable(table_name)",
        ")",
        "",
        "spark.sql(f\"DESCRIBE TABLE {table_name}\").filter(\"col_name = 'Claim_Amount'\").show(truncate=False)"
      ]
    }
  ],
  "metadata": {},
  "nbformat": 4,
  "nbformat_minor": 5
}

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
