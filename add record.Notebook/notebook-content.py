# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "dab98636-1291-4c03-876c-74071a46c00a",
# META       "default_lakehouse_name": "autoclaimsdata",
# META       "default_lakehouse_workspace_id": "c02b4576-1584-40be-9f45-199c6a36437e",
# META       "known_lakehouses": [
# META         {
# META           "id": "dab98636-1291-4c03-876c-74071a46c00a"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

# ─────────────────────────────────────────────────────────
# CELL 1 — Imports
# ─────────────────────────────────────────────────────────
from pyspark.sql import Row
from pyspark.sql.functions import max as spark_max
from datetime import datetime

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# ─────────────────────────────────────────────────────────
# CELL 2 — Configure your new claim (edit values here)
# ─────────────────────────────────────────────────────────
CLAIM_AMOUNT    = 80000
CLAIM_STATUS    = "Under Review"
CLAIM_TYPE      = 1        # 1=Collision  2=Theft  3=Glass  4=Liability  5=Weather  6=Vandalism
POLICY_ID       = 433      # Lamborghini policy created earlier
CUSTOMER_ID     = "e5d4c3b2-a1f0-4e2d-9c8b-7a6b5c4d3e2f.501"
VEHICLE_ID      = 331      # Lamborghini Huracán EVO
ADJUSTER_ID     = 109      # Sandra Kim
REPAIR_SHOP_ID  = 607      # Metro Precision Auto (Luxury Vehicles)
CLAIM_DATE      = datetime.now().strftime("%-m/%-d/%Y 0:00")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# ─────────────────────────────────────────────────────────
# CELL 3 — Auto-generate next Claim_ID
# ─────────────────────────────────────────────────────────
claims_df = spark.table("claims_fact")

next_id = claims_df.agg(spark_max("Claim_ID").alias("max_id")).collect()[0]["max_id"] + 1
print(f"Next Claim_ID: {next_id}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# ─────────────────────────────────────────────────────────
# CELL 4 — Build new row using existing table schema
# ─────────────────────────────────────────────────────────
new_row = spark.createDataFrame(
    [(
        next_id,
        POLICY_ID,
        CUSTOMER_ID,
        VEHICLE_ID,
        ADJUSTER_ID,
        REPAIR_SHOP_ID,
        CLAIM_DATE,
        None,           # Claim_CloseDate — blank while Under Review
        CLAIM_AMOUNT,
        CLAIM_STATUS,
        CLAIM_TYPE
    )],
    schema=claims_df.schema
)

new_row.show(truncate=False)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# ─────────────────────────────────────────────────────────
# CELL 5 — Append to Delta table & verify
# ─────────────────────────────────────────────────────────
new_row.write.mode("append").saveAsTable("claims_fact")

# Confirm the insert
spark.table("claims_fact") \
     .filter(f"Claim_ID = {next_id}") \
     .show(truncate=False)

print(f"✓ Claim {next_id} written — ${CLAIM_AMOUNT:,} | {CLAIM_STATUS}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
