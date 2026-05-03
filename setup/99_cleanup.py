# Databricks notebook source
# MAGIC %md
# MAGIC # Cleanup: Drop All Workshop Schemas
# MAGIC
# MAGIC Drops all schemas matching the workshop prefix across all industries.
# MAGIC **Warning:** This is irreversible.

# COMMAND ----------

dbutils.widgets.text("catalog", "main")
dbutils.widgets.text("schema_prefix", "ai_functions_workshop")

catalog = dbutils.widgets.get("catalog")
schema_prefix = dbutils.widgets.get("schema_prefix")

# COMMAND ----------

spark.sql(f"USE CATALOG {catalog}")

schemas = spark.sql(f"SHOW SCHEMAS IN {catalog}").filter(
    f"databaseName LIKE '{schema_prefix}%'"
).collect()

print(f"Found {len(schemas)} schema(s) to drop:")
for row in schemas:
    print(f"  {catalog}.{row['databaseName']}")

# COMMAND ----------

for row in schemas:
    schema_name = row["databaseName"]
    print(f"Dropping: {catalog}.{schema_name}")
    spark.sql(f"DROP SCHEMA IF EXISTS {catalog}.{schema_name} CASCADE")

print("Cleanup complete.")
