# Databricks notebook source
# MAGIC %md
# MAGIC # Setup: Catalog, Schema & Volumes
# MAGIC
# MAGIC Creates the Unity Catalog schema and volume for the selected industry vertical.
# MAGIC
# MAGIC **Parameters** (passed by DAB job):
# MAGIC - `catalog` – UC catalog to use (default: `main`)
# MAGIC - `schema_prefix` – prefix for schemas (default: `ai_functions_workshop`)
# MAGIC - `industry` – one of `fins | gaming | dnb | telco | mfg`

# COMMAND ----------

dbutils.widgets.text("catalog", "main")
dbutils.widgets.text("schema_prefix", "ai_functions_workshop")
dbutils.widgets.text("industry", "fins")

catalog = dbutils.widgets.get("catalog")
schema_prefix = dbutils.widgets.get("schema_prefix")
industry = dbutils.widgets.get("industry").lower().strip()

schema = f"{schema_prefix}_{industry}"

print(f"catalog  : {catalog}")
print(f"schema   : {schema}")
print(f"industry : {industry}")

# COMMAND ----------

valid_industries = {"fins", "gaming", "dnb", "telco", "mfg"}
assert industry in valid_industries, f"industry must be one of {sorted(valid_industries)}, got '{industry}'"

# COMMAND ----------

# MAGIC %md ## Create schema & volume

# COMMAND ----------

spark.sql(f"USE CATALOG {catalog}")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {schema} COMMENT 'AI Functions Workshop – {industry.upper()} vertical'")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {catalog}.{schema}.documents COMMENT 'PDF documents for ai_parse_document exercises'")

print(f"Schema  : {catalog}.{schema}")
print(f"Volume  : /Volumes/{catalog}/{schema}/documents/")

# COMMAND ----------

# MAGIC %md ## Verify

# COMMAND ----------

display(spark.sql(f"SHOW SCHEMAS IN {catalog} LIKE '{schema_prefix}*'"))
display(spark.sql(f"SHOW VOLUMES IN {catalog}.{schema}"))
