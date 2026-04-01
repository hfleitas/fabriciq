-- Fabric notebook source

-- METADATA ********************

-- META {
-- META   "kernel_info": {
-- META     "name": "synapse_pyspark"
-- META   },
-- META   "dependencies": {
-- META     "lakehouse": {
-- META       "default_lakehouse": "6dc2c94a-578b-4527-bdef-7e7f36d7da43",
-- META       "default_lakehouse_name": "LH1",
-- META       "default_lakehouse_workspace_id": "65324039-09f8-4ecd-897c-c3e6b82aab52",
-- META       "known_lakehouses": [
-- META         {
-- META           "id": "6dc2c94a-578b-4527-bdef-7e7f36d7da43"
-- META         }
-- META       ]
-- META     }
-- META   }
-- META }

-- CELL ********************

select * from adjuster_dim

-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

update adjuster_dim
set Experience_Years = 15
where Adjuster_ID = 101

-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

select * from adjuster_dim

-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

delete from adjuster_dim
where Adjuster_ID=109

-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }
