# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "76aa6c3d-b425-4f55-95f6-e4455223e1a6",
# META       "default_lakehouse_name": "insurance_data",
# META       "default_lakehouse_workspace_id": "c02b4576-1584-40be-9f45-199c6a36437e"
# META     }
# META   }
# META }

# MARKDOWN ********************

# # Auto Claims Demo Dataset â€” Fabric Lakehouse (Delta Tables)
# **Workspace:** fabriciq  
# **Lakehouse:** insurance_data  
# 
# This notebook creates and populates all dimension and fact tables as managed Delta tables in the attached Lakehouse.
# 
# > **Pre-requisite:** Attach this notebook to the `insurance_data` Lakehouse before running.

# CELL ********************

from pyspark.sql.types import StructType, StructField, IntegerType, StringType, DateType, DecimalType
from datetime import date
from decimal import Decimal

# MARKDOWN ********************

# ## 1. ClaimType_Dim

# CELL ********************

claim_type_schema = StructType([
    StructField("Claim_Type_ID", IntegerType(), False),
    StructField("Claim_Type_Name", StringType(), False)
])

claim_type_data = [
    (1, "Collision"),
    (2, "Theft"),
    (3, "Glass Damage"),
    (4, "Liability"),
    (5, "Weather"),
    (6, "Vandalism")
]

df_claim_type = spark.createDataFrame(claim_type_data, schema=claim_type_schema)
df_claim_type.write.mode("overwrite").format("delta").saveAsTable("ClaimType_Dim")
print(f"ClaimType_Dim: {df_claim_type.count()} rows written")

# MARKDOWN ********************

# ## 2. Adjuster_Dim

# CELL ********************

adjuster_schema = StructType([
    StructField("Adjuster_ID", IntegerType(), False),
    StructField("Adjuster_Name", StringType(), False),
    StructField("Experience_Years", IntegerType(), False),
    StructField("Region", StringType(), False)
])

adjuster_data = [
    (101, "Alicia Gomez", 12, "West"),
    (102, "Marcus Reed", 8, "South"),
    (103, "Priya Narang", 15, "Northeast"),
    (104, "Daniel Brooks", 6, "Midwest"),
    (105, "Helen Zhao", 10, "West"),
    (106, "Jared Mills", 4, "South"),
    (107, "Nina Patel", 9, "Northeast"),
    (108, "Owen Carter", 13, "Midwest")
]

df_adjuster = spark.createDataFrame(adjuster_data, schema=adjuster_schema)
df_adjuster.write.mode("overwrite").format("delta").saveAsTable("Adjuster_Dim")
print(f"Adjuster_Dim: {df_adjuster.count()} rows written")

# MARKDOWN ********************

# ## 3. Customer_Dim

# CELL ********************

customer_schema = StructType([
    StructField("Customer_ID", StringType(), False),
    StructField("Customer_Name", StringType(), False),
    StructField("Date_of_Birth", DateType(), False),
    StructField("Customer_Age", IntegerType(), False),
    StructField("Gender", StringType(), False),
    StructField("Address", StringType(), False),
    StructField("City", StringType(), False),
    StructField("State", StringType(), False)
])

customer_data = [
    ("4b155aa0-945d-435f-90cc-9daf7471af1d.869", "Emma Johnson", date(1988, 3, 14), 37, "Female", "1452 Maple St", "Seattle", "WA"),
    ("98f90fba-62fd-40f2-ab09-81a80144ea9f.217", "Liam Davis", date(1979, 11, 2), 46, "Male", "2208 Pine Ave", "Dallas", "TX"),
    ("3ad75bb1-5090-4cc8-9dc8-5f4c6ae8ac76.341", "Sophia Martinez", date(1992, 6, 21), 33, "Female", "19 River Rd", "Miami", "FL"),
    ("b13f4f08-af70-4f69-9370-5fd82a8b6e24.903", "Noah Wilson", date(1985, 1, 9), 41, "Male", "87 Lakeview Dr", "Chicago", "IL"),
    ("7f6733ed-51ce-4489-8edd-838210272f6d.622", "Ava Brown", date(1995, 9, 30), 30, "Female", "623 Cedar Ln", "Phoenix", "AZ"),
    ("0aaaf6f6-60e8-4f4d-b6a6-c58340ec8cb5.115", "Mason Clark", date(1982, 12, 11), 43, "Male", "411 Highland Blvd", "Denver", "CO"),
    ("39eb41d5-6407-42fa-b834-8ef905ff7b5b.776", "Isabella Lewis", date(1990, 4, 27), 35, "Female", "52 Broadway", "New York", "NY"),
    ("ec00cf1e-4f43-42de-9195-a0f8f6418f3e.254", "Ethan Walker", date(1976, 8, 16), 49, "Male", "900 Elm St", "Atlanta", "GA"),
    ("5c86d136-4898-4b2f-b89f-6067514f2f91.498", "Mia Hall", date(1989, 2, 18), 37, "Female", "311 Oak Ct", "San Diego", "CA"),
    ("a14f42bb-7fcf-4daa-9fcb-c8444aa4ec89.730", "James Allen", date(1993, 7, 12), 32, "Male", "712 Sunset Blvd", "Los Angeles", "CA"),
    ("2ff1131f-7039-4ba7-8726-cf8f6bbd4d2e.360", "Charlotte Young", date(1987, 5, 5), 38, "Female", "45 Willow Way", "Boston", "MA"),
    ("d9cc6911-da61-43c2-8248-03d6fd4d8059.144", "Benjamin King", date(1981, 10, 23), 44, "Male", "123 Harbor St", "Portland", "OR")
]

df_customer = spark.createDataFrame(customer_data, schema=customer_schema)
df_customer.write.mode("overwrite").format("delta").saveAsTable("Customer_Dim")
print(f"Customer_Dim: {df_customer.count()} rows written")

# MARKDOWN ********************

# ## 4. Vehicle_Dim

# CELL ********************

vehicle_schema = StructType([
    StructField("Vehicle_ID", IntegerType(), False),
    StructField("Vehicle_VIN", StringType(), False),
    StructField("Make", StringType(), False),
    StructField("Model", StringType(), False),
    StructField("Year", IntegerType(), False),
    StructField("Vehicle_Type", StringType(), False),
    StructField("Value", DecimalType(12, 2), False)
])

vehicle_data = [
    (301, "1HGBH41JXMN000301", "Toyota", "Camry", 2021, "Sedan", Decimal("23500.00")),
    (302, "1HGBH41JXMN000302", "Honda", "CR-V", 2020, "SUV", Decimal("26800.00")),
    (303, "1HGBH41JXMN000303", "Ford", "F-150", 2019, "Truck", Decimal("31200.00")),
    (304, "1HGBH41JXMN000304", "Tesla", "Model 3", 2022, "Sedan", Decimal("42500.00")),
    (305, "1HGBH41JXMN000305", "Chevrolet", "Equinox", 2018, "SUV", Decimal("18900.00")),
    (306, "1HGBH41JXMN000306", "Nissan", "Altima", 2021, "Sedan", Decimal("22100.00")),
    (307, "1HGBH41JXMN000307", "Jeep", "Wrangler", 2020, "SUV", Decimal("33800.00")),
    (308, "1HGBH41JXMN000308", "Hyundai", "Elantra", 2019, "Sedan", Decimal("17600.00")),
    (309, "1HGBH41JXMN000309", "BMW", "X3", 2021, "SUV", Decimal("44800.00")),
    (310, "1HGBH41JXMN000310", "Kia", "Sorento", 2022, "SUV", Decimal("33200.00")),
    (311, "1HGBH41JXMN000311", "Subaru", "Outback", 2020, "Wagon", Decimal("28900.00")),
    (312, "1HGBH41JXMN000312", "Audi", "A4", 2019, "Sedan", Decimal("30700.00"))
]

df_vehicle = spark.createDataFrame(vehicle_data, schema=vehicle_schema)
df_vehicle.write.mode("overwrite").format("delta").saveAsTable("Vehicle_Dim")
print(f"Vehicle_Dim: {df_vehicle.count()} rows written")

# MARKDOWN ********************

# ## 5. Repair_Shop_Dim

# CELL ********************

repair_shop_schema = StructType([
    StructField("Repair_Shop_ID", IntegerType(), False),
    StructField("Shop_Name", StringType(), False),
    StructField("Network_Type", StringType(), False),
    StructField("Contact_Number", StringType(), False),
    StructField("City", StringType(), False),
    StructField("State", StringType(), False),
    StructField("Avg_Repair_Days", IntegerType(), False),
    StructField("Specialty", StringType(), False)
])

repair_shop_data = [
    (601, "North Star Collision Center", "Preferred", "206-555-0181", "Seattle", "WA", 6, "Collision & Paint"),
    (602, "Lone Star Auto Body", "Preferred", "972-555-0192", "Dallas", "TX", 7, "Frame Repair"),
    (603, "Suncoast Claims Repair", "Partner", "305-555-0177", "Miami", "FL", 5, "Water Damage"),
    (604, "Lakefront Vehicle Works", "Preferred", "312-555-0144", "Chicago", "IL", 8, "Structural Repair"),
    (605, "Desert Auto Restore", "Partner", "602-555-0160", "Phoenix", "AZ", 6, "Glass & Paint"),
    (606, "Mile High Collision Hub", "Preferred", "303-555-0131", "Denver", "CO", 7, "Collision"),
    (607, "Metro Precision Auto", "Preferred", "212-555-0119", "New York", "NY", 9, "Luxury Vehicles"),
    (608, "Peachtree Auto Claims", "Partner", "404-555-0156", "Atlanta", "GA", 6, "General Repair"),
    (609, "Pacific Coast Body Shop", "Preferred", "619-555-0107", "San Diego", "CA", 7, "SUV & EV Repair"),
    (610, "SoCal Rapid Repair", "Partner", "213-555-0128", "Los Angeles", "CA", 5, "Express Repair")
]

df_repair_shop = spark.createDataFrame(repair_shop_data, schema=repair_shop_schema)
df_repair_shop.write.mode("overwrite").format("delta").saveAsTable("Repair_Shop_Dim")
print(f"Repair_Shop_Dim: {df_repair_shop.count()} rows written")

# MARKDOWN ********************

# ## 6. Policy_Dim

# CELL ********************

policy_schema = StructType([
    StructField("Policy_ID", IntegerType(), False),
    StructField("Policy_Number", StringType(), False),
    StructField("Policy_Type", StringType(), False),
    StructField("Policy_Start_Date", DateType(), False),
    StructField("Policy_End_Date", DateType(), False),
    StructField("Coverage_Limit", DecimalType(12, 2), False),
    StructField("Customer_ID", StringType(), False),
    StructField("Vehicle_ID", IntegerType(), False)
])

policy_data = [
    (401, "POL-100401", "Comprehensive", date(2024, 1, 1), date(2024, 12, 31), Decimal("100000.00"), "4b155aa0-945d-435f-90cc-9daf7471af1d.869", 301),
    (402, "POL-100402", "Liability", date(2024, 2, 15), date(2025, 2, 14), Decimal("50000.00"), "98f90fba-62fd-40f2-ab09-81a80144ea9f.217", 302),
    (403, "POL-100403", "Collision", date(2024, 3, 1), date(2025, 2, 28), Decimal("75000.00"), "3ad75bb1-5090-4cc8-9dc8-5f4c6ae8ac76.341", 303),
    (404, "POL-100404", "Comprehensive", date(2024, 1, 20), date(2025, 1, 19), Decimal("120000.00"), "b13f4f08-af70-4f69-9370-5fd82a8b6e24.903", 304),
    (405, "POL-100405", "Liability", date(2024, 4, 10), date(2025, 4, 9), Decimal("60000.00"), "7f6733ed-51ce-4489-8edd-838210272f6d.622", 305),
    (406, "POL-100406", "Collision", date(2024, 5, 1), date(2025, 4, 30), Decimal("80000.00"), "0aaaf6f6-60e8-4f4d-b6a6-c58340ec8cb5.115", 306),
    (407, "POL-100407", "Comprehensive", date(2024, 6, 1), date(2025, 5, 31), Decimal("110000.00"), "39eb41d5-6407-42fa-b834-8ef905ff7b5b.776", 307),
    (408, "POL-100408", "Liability", date(2024, 6, 15), date(2025, 6, 14), Decimal("55000.00"), "ec00cf1e-4f43-42de-9195-a0f8f6418f3e.254", 308),
    (409, "POL-100409", "Comprehensive", date(2024, 7, 1), date(2025, 6, 30), Decimal("130000.00"), "5c86d136-4898-4b2f-b89f-6067514f2f91.498", 309),
    (410, "POL-100410", "Collision", date(2024, 7, 20), date(2025, 7, 19), Decimal("90000.00"), "a14f42bb-7fcf-4daa-9fcb-c8444aa4ec89.730", 310),
    (411, "POL-100411", "Liability", date(2024, 8, 1), date(2025, 7, 31), Decimal("65000.00"), "2ff1131f-7039-4ba7-8726-cf8f6bbd4d2e.360", 311),
    (412, "POL-100412", "Comprehensive", date(2024, 8, 10), date(2025, 8, 9), Decimal("125000.00"), "d9cc6911-da61-43c2-8248-03d6fd4d8059.144", 312),
    (413, "POL-100413", "Collision", date(2024, 9, 1), date(2025, 8, 31), Decimal("85000.00"), "4b155aa0-945d-435f-90cc-9daf7471af1d.869", 302),
    (414, "POL-100414", "Comprehensive", date(2024, 10, 1), date(2025, 9, 30), Decimal("140000.00"), "3ad75bb1-5090-4cc8-9dc8-5f4c6ae8ac76.341", 304)
]

df_policy = spark.createDataFrame(policy_data, schema=policy_schema)
df_policy.write.mode("overwrite").format("delta").saveAsTable("Policy_Dim")
print(f"Policy_Dim: {df_policy.count()} rows written")

# MARKDOWN ********************

# ## 7. Claims_Fact

# CELL ********************

claims_schema = StructType([
    StructField("Claim_ID", IntegerType(), False),
    StructField("Policy_ID", IntegerType(), False),
    StructField("Customer_ID", StringType(), False),
    StructField("Vehicle_ID", IntegerType(), False),
    StructField("Adjuster_ID", IntegerType(), False),
    StructField("Repair_Shop_ID", IntegerType(), True),
    StructField("Claim_Date", DateType(), False),
    StructField("Claim_CloseDate", DateType(), True),
    StructField("Claim_Amount", DecimalType(12, 2), False),
    StructField("Claim_Status", StringType(), False),
    StructField("Claim_Type", IntegerType(), False)
])

claims_data = [
    (5001, 401, "4b155aa0-945d-435f-90cc-9daf7471af1d.869", 301, 101, 601, date(2024, 2, 10), date(2024, 2, 18), Decimal("4200.00"), "Closed", 1),
    (5002, 402, "98f90fba-62fd-40f2-ab09-81a80144ea9f.217", 302, 102, 602, date(2024, 3, 5), date(2024, 3, 21), Decimal("1800.00"), "Closed", 3),
    (5003, 403, "3ad75bb1-5090-4cc8-9dc8-5f4c6ae8ac76.341", 303, 104, 603, date(2024, 3, 22), date(2024, 4, 2), Decimal("7600.00"), "Closed", 1),
    (5004, 404, "b13f4f08-af70-4f69-9370-5fd82a8b6e24.903", 304, 103, None, date(2024, 4, 11), date(2024, 5, 3), Decimal("12500.00"), "Closed", 4),
    (5005, 405, "7f6733ed-51ce-4489-8edd-838210272f6d.622", 305, 106, 605, date(2024, 5, 9), date(2024, 5, 17), Decimal("2400.00"), "Closed", 5),
    (5006, 406, "0aaaf6f6-60e8-4f4d-b6a6-c58340ec8cb5.115", 306, 108, 606, date(2024, 5, 28), date(2024, 6, 8), Decimal("5100.00"), "Closed", 1),
    (5007, 407, "39eb41d5-6407-42fa-b834-8ef905ff7b5b.776", 307, 107, None, date(2024, 6, 10), date(2024, 6, 30), Decimal("9800.00"), "Closed", 2),
    (5008, 408, "ec00cf1e-4f43-42de-9195-a0f8f6418f3e.254", 308, 102, 608, date(2024, 6, 25), None, Decimal("1300.00"), "Open", 6),
    (5009, 409, "5c86d136-4898-4b2f-b89f-6067514f2f91.498", 309, 105, 609, date(2024, 7, 7), date(2024, 7, 20), Decimal("6700.00"), "Closed", 3),
    (5010, 410, "a14f42bb-7fcf-4daa-9fcb-c8444aa4ec89.730", 310, 101, 610, date(2024, 7, 24), date(2024, 8, 9), Decimal("8900.00"), "Closed", 1),
    (5011, 411, "2ff1131f-7039-4ba7-8726-cf8f6bbd4d2e.360", 311, 104, 607, date(2024, 8, 3), None, Decimal("2200.00"), "Under Review", 5),
    (5012, 412, "d9cc6911-da61-43c2-8248-03d6fd4d8059.144", 312, 108, 610, date(2024, 8, 16), date(2024, 9, 1), Decimal("4300.00"), "Closed", 6),
    (5013, 413, "4b155aa0-945d-435f-90cc-9daf7471af1d.869", 302, 106, None, date(2024, 9, 2), date(2024, 9, 28), Decimal("11200.00"), "Closed", 4),
    (5014, 414, "3ad75bb1-5090-4cc8-9dc8-5f4c6ae8ac76.341", 304, 103, 603, date(2024, 9, 19), None, Decimal("15700.00"), "Open", 1),
    (5015, 401, "4b155aa0-945d-435f-90cc-9daf7471af1d.869", 301, 105, 601, date(2024, 10, 6), date(2024, 10, 15), Decimal("1600.00"), "Closed", 3),
    (5016, 402, "98f90fba-62fd-40f2-ab09-81a80144ea9f.217", 302, 107, None, date(2024, 10, 22), None, Decimal("5400.00"), "Under Review", 2),
    (5017, 409, "5c86d136-4898-4b2f-b89f-6067514f2f91.498", 309, 101, 609, date(2024, 11, 3), date(2024, 11, 21), Decimal("3100.00"), "Closed", 5),
    (5018, 410, "a14f42bb-7fcf-4daa-9fcb-c8444aa4ec89.730", 310, 102, 610, date(2024, 11, 17), None, Decimal("4700.00"), "Open", 1),
    (5019, 412, "d9cc6911-da61-43c2-8248-03d6fd4d8059.144", 312, 104, 607, date(2024, 12, 1), date(2024, 12, 14), Decimal("2800.00"), "Closed", 3),
    (5020, 407, "39eb41d5-6407-42fa-b834-8ef905ff7b5b.776", 307, 108, None, date(2024, 12, 10), None, Decimal("9600.00"), "Under Review", 2)
]

df_claims = spark.createDataFrame(claims_data, schema=claims_schema)
df_claims.write.mode("overwrite").format("delta").saveAsTable("Claims_Fact")
print(f"Claims_Fact: {df_claims.count()} rows written")

# MARKDOWN ********************

# ## 8. Validation â€” Row Counts & Sample Join Query

# CELL ********************

tables = ["ClaimType_Dim", "Adjuster_Dim", "Customer_Dim", "Vehicle_Dim",
          "Repair_Shop_Dim", "Policy_Dim", "Claims_Fact"]

print("=== Table Row Counts ===")
for t in tables:
    cnt = spark.table(t).count()
    print(f"  {t}: {cnt}")

# CELL ********************

validation_query = """
SELECT
    c.Claim_ID,
    c.Claim_Date,
    c.Claim_Amount,
    c.Claim_Status,
    ct.Claim_Type_Name,
    cu.Customer_Name,
    p.Policy_Number,
    v.Make,
    v.Model,
    a.Adjuster_Name,
    rs.Shop_Name,
    rs.Network_Type
FROM Claims_Fact c
JOIN ClaimType_Dim ct ON c.Claim_Type = ct.Claim_Type_ID
JOIN Customer_Dim cu ON c.Customer_ID = cu.Customer_ID
JOIN Policy_Dim p ON c.Policy_ID = p.Policy_ID
JOIN Vehicle_Dim v ON c.Vehicle_ID = v.Vehicle_ID
JOIN Adjuster_Dim a ON c.Adjuster_ID = a.Adjuster_ID
LEFT JOIN Repair_Shop_Dim rs ON c.Repair_Shop_ID = rs.Repair_Shop_ID
ORDER BY c.Claim_Date DESC
LIMIT 10
"""

display(spark.sql(validation_query))
