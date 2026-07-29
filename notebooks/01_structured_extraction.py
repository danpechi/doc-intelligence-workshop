# Databricks notebook source
# MAGIC %md
# MAGIC # Lab 1: Structured Extraction with `ai_query`
# MAGIC
# MAGIC **AI Function:** `ai_query(endpoint, prompt, responseFormat => '<json_schema>')`
# MAGIC
# MAGIC The core challenge with unstructured text is that it is not directly queryable in SQL.
# MAGIC `ai_query` with `responseFormat` solves this by instructing the model to return
# MAGIC a **typed JSON struct** — making every response directly queryable with standard SQL.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## How it works
# MAGIC
# MAGIC ```sql
# MAGIC -- WITHOUT responseFormat: returns unstructured text
# MAGIC SELECT ai_query('databricks-meta-llama-3-3-70b-instruct', 'Extract the APR from: ...') AS raw_text
# MAGIC
# MAGIC -- WITH responseFormat: returns a typed STRUCT you can query with SQL
# MAGIC SELECT from_json(ai_query(
# MAGIC   'databricks-meta-llama-3-3-70b-instruct',
# MAGIC   CONCAT('Extract product details from: ', document_text),
# MAGIC   responseFormat => '{"type":"json_schema","json_schema":{"name":"response","schema":{"type":"object","properties":{"product_name":{"type":"string"},"apr_low":{"type":"number"},"apr_high":{"type":"number"},"min_income":{"type":"integer"}}}}}'
# MAGIC ), 'product_name STRING, apr_low DOUBLE, apr_high DOUBLE, min_income BIGINT').apr_low AS apr_low
# MAGIC ```

# COMMAND ----------

dbutils.widgets.dropdown("industry", "fins", ["fins", "gaming", "dnb", "telco", "mfg"])
dbutils.widgets.text("catalog", "main")
dbutils.widgets.text("schema_prefix", "ai_functions_workshop")

industry = dbutils.widgets.get("industry")
catalog = dbutils.widgets.get("catalog")
schema_prefix = dbutils.widgets.get("schema_prefix")
schema = f"{schema_prefix}_{industry}"
full_schema = f"{catalog}.{schema}"

spark.sql(f"USE {full_schema}")
print(f"Using schema: {full_schema}")

# COMMAND ----------

# MAGIC %md ## Step 1 – Understand the raw data

# COMMAND ----------

if industry == "fins":
    display(spark.sql("SELECT product_id, product_name, document_text FROM product_documents LIMIT 5"))
elif industry == "gaming":
    display(spark.sql("SELECT report_id, incident_type, description FROM player_reports LIMIT 5"))
elif industry == "dnb":
    display(spark.sql("SELECT prospect_id, company_name, description FROM prospect_companies LIMIT 5"))
elif industry == "telco":
    display(spark.sql("SELECT call_id, issue_type, transcript FROM customer_calls LIMIT 5"))
elif industry == "mfg":
    display(spark.sql("SELECT log_id, failure_mode, technician_notes FROM maintenance_logs LIMIT 5"))

# COMMAND ----------

# MAGIC %md ## Step 2 – Without `responseFormat` (unstructured, hard to parse)

# COMMAND ----------

if industry == "fins":
    display(spark.sql("""
        SELECT
            product_id,
            ai_query(
                'databricks-meta-llama-3-3-70b-instruct',
                CONCAT('Extract the APR range and minimum income from this product description. Reply in plain text: ', document_text)
            ) AS raw_extraction
        FROM product_documents
        LIMIT 3
    """))

elif industry == "gaming":
    display(spark.sql("""
        SELECT
            report_id,
            ai_query(
                'databricks-meta-llama-3-3-70b-instruct',
                CONCAT('Identify the incident type, severity, and any specific player IDs mentioned. Reply in plain text: ', description)
            ) AS raw_extraction
        FROM player_reports
        LIMIT 3
    """))

elif industry == "dnb":
    display(spark.sql("""
        SELECT
            prospect_id,
            ai_query(
                'databricks-meta-llama-3-3-70b-instruct',
                CONCAT('Extract company size, funding stage, and main pain point. Reply in plain text: ', description)
            ) AS raw_extraction
        FROM prospect_companies
        LIMIT 3
    """))

elif industry == "telco":
    display(spark.sql("""
        SELECT
            call_id,
            ai_query(
                'databricks-meta-llama-3-3-70b-instruct',
                CONCAT('Extract the main issue, customer sentiment, and whether the issue was resolved. Reply in plain text: ', transcript)
            ) AS raw_extraction
        FROM customer_calls
        LIMIT 3
    """))

elif industry == "mfg":
    display(spark.sql("""
        SELECT
            log_id,
            ai_query(
                'databricks-meta-llama-3-3-70b-instruct',
                CONCAT('Extract the failure mode, root cause, and affected component batch. Reply in plain text: ', technician_notes)
            ) AS raw_extraction
        FROM maintenance_logs
        LIMIT 3
    """))

# COMMAND ----------

# MAGIC %md
# MAGIC > **Notice:** The raw text responses vary in format and cannot be reliably joined,
# MAGIC > aggregated, or filtered in SQL. The next step fixes this.

# COMMAND ----------

# MAGIC %md ## Step 3 – With `responseFormat` (typed STRUCT, directly queryable)

# COMMAND ----------

if industry == "fins":
    display(spark.sql("""
        SELECT
            product_id,
            product_name,
            from_json(ai_query(
                'databricks-meta-llama-3-3-70b-instruct',
                CONCAT('Extract financial product details from this description: ', document_text),
                responseFormat => '{"type":"json_schema","json_schema":{"name":"response","schema":{"type":"object","properties":{"product_name":{"type":"string"},"product_type":{"type":"string"},"apr_low":{"type":"number"},"apr_high":{"type":"number"},"min_income_usd":{"type":"integer"},"max_amount_usd":{"type":"integer"},"key_benefit":{"type":"string"}}}}}'
            ), 'product_name STRING, product_type STRING, apr_low DOUBLE, apr_high DOUBLE, min_income_usd BIGINT, max_amount_usd BIGINT, key_benefit STRING') AS extracted
        FROM product_documents
    """))

elif industry == "gaming":
    display(spark.sql("""
        SELECT
            report_id,
            incident_type,
            from_json(ai_query(
                'databricks-meta-llama-3-3-70b-instruct',
                CONCAT('Analyze this player conduct report and extract structured details: ', description),
                responseFormat => '{"type":"json_schema","json_schema":{"name":"response","schema":{"type":"object","properties":{"incident_category":{"type":"string"},"severity_level":{"type":"string"},"repeated_offense":{"type":"boolean"},"involves_personal_threat":{"type":"boolean"},"recommended_action":{"type":"string"}}}}}'
            ), 'incident_category STRING, severity_level STRING, repeated_offense BOOLEAN, involves_personal_threat BOOLEAN, recommended_action STRING') AS extracted
        FROM player_reports
    """))

elif industry == "dnb":
    display(spark.sql("""
        SELECT
            prospect_id,
            company_name,
            from_json(ai_query(
                'databricks-meta-llama-3-3-70b-instruct',
                CONCAT('Extract structured business intelligence from this company description: ', description),
                responseFormat => '{"type":"json_schema","json_schema":{"name":"response","schema":{"type":"object","properties":{"company_type":{"type":"string"},"employee_range":{"type":"string"},"funding_stage":{"type":"string"},"current_tech_stack":{"type":"string"},"primary_pain_point":{"type":"string"},"databricks_fit_score":{"type":"integer"}}}}}'
            ), 'company_type STRING, employee_range STRING, funding_stage STRING, current_tech_stack STRING, primary_pain_point STRING, databricks_fit_score BIGINT') AS extracted
        FROM prospect_companies
        LIMIT 20
    """))

elif industry == "telco":
    display(spark.sql("""
        SELECT
            call_id,
            agent_id,
            from_json(ai_query(
                'databricks-meta-llama-3-3-70b-instruct',
                CONCAT('Extract structured information from this call transcript: ', transcript),
                responseFormat => '{"type":"json_schema","json_schema":{"name":"response","schema":{"type":"object","properties":{"issue_type":{"type":"string"},"customer_sentiment":{"type":"string"},"churn_risk":{"type":"string"},"resolution_achieved":{"type":"boolean"},"follow_up_required":{"type":"boolean"},"key_complaint":{"type":"string"}}}}}'
            ), 'issue_type STRING, customer_sentiment STRING, churn_risk STRING, resolution_achieved BOOLEAN, follow_up_required BOOLEAN, key_complaint STRING') AS extracted
        FROM customer_calls
        LIMIT 20
    """))

elif industry == "mfg":
    display(spark.sql("""
        SELECT
            log_id,
            line_id,
            from_json(ai_query(
                'databricks-meta-llama-3-3-70b-instruct',
                CONCAT('Extract root cause analysis details from this maintenance log: ', technician_notes),
                responseFormat => '{"type":"json_schema","json_schema":{"name":"response","schema":{"type":"object","properties":{"failure_mode":{"type":"string"},"failure_category":{"type":"string"},"severity":{"type":"string"},"component_batch_id":{"type":"string"},"root_cause_summary":{"type":"string"},"supplier_involved":{"type":"boolean"},"safety_risk":{"type":"boolean"}}}}}'
            ), 'failure_mode STRING, failure_category STRING, severity STRING, component_batch_id STRING, root_cause_summary STRING, supplier_involved BOOLEAN, safety_risk BOOLEAN') AS extracted
        FROM maintenance_logs
        LIMIT 20
    """))

# COMMAND ----------

# MAGIC %md ## Step 4 – Query the extracted struct fields directly

# COMMAND ----------

if industry == "fins":
    display(spark.sql("""
        WITH extracted AS (
            SELECT
                product_id, product_name,
                from_json(ai_query(
                    'databricks-meta-llama-3-3-70b-instruct',
                    CONCAT('Extract financial product details: ', document_text),
                    responseFormat => '{"type":"json_schema","json_schema":{"name":"response","schema":{"type":"object","properties":{"product_type":{"type":"string"},"apr_low":{"type":"number"},"apr_high":{"type":"number"},"min_income_usd":{"type":"integer"}}}}}'
                ), 'product_type STRING, apr_low DOUBLE, apr_high DOUBLE, min_income_usd BIGINT') AS info
            FROM product_documents
        )
        SELECT
            product_id,
            product_name,
            info.product_type,
            info.apr_low,
            info.apr_high,
            info.min_income_usd
        FROM extracted
        ORDER BY info.apr_low
    """))

elif industry == "mfg":
    display(spark.sql("""
        WITH extracted AS (
            SELECT
                log_id, line_id, downtime_hours,
                from_json(ai_query(
                    'databricks-meta-llama-3-3-70b-instruct',
                    CONCAT('Extract root cause details: ', technician_notes),
                    responseFormat => '{"type":"json_schema","json_schema":{"name":"response","schema":{"type":"object","properties":{"failure_category":{"type":"string"},"severity":{"type":"string"},"supplier_involved":{"type":"boolean"}}}}}'
                ), 'failure_category STRING, severity STRING, supplier_involved BOOLEAN') AS info
            FROM maintenance_logs
            LIMIT 50
        )
        SELECT
            info.failure_category,
            info.severity,
            COUNT(*) AS event_count,
            ROUND(AVG(downtime_hours), 2) AS avg_downtime_hrs,
            SUM(CASE WHEN info.supplier_involved THEN 1 ELSE 0 END) AS supplier_related_count
        FROM extracted
        GROUP BY info.failure_category, info.severity
        ORDER BY avg_downtime_hrs DESC
    """))

elif industry == "telco":
    display(spark.sql("""
        WITH extracted AS (
            SELECT
                call_id,
                from_json(ai_query(
                    'databricks-meta-llama-3-3-70b-instruct',
                    CONCAT('Classify this call transcript: ', transcript),
                    responseFormat => '{"type":"json_schema","json_schema":{"name":"response","schema":{"type":"object","properties":{"issue_type":{"type":"string"},"churn_risk":{"type":"string"},"resolution_achieved":{"type":"boolean"}}}}}'
                ), 'issue_type STRING, churn_risk STRING, resolution_achieved BOOLEAN') AS info
            FROM customer_calls
            LIMIT 50
        )
        SELECT
            info.issue_type,
            info.churn_risk,
            COUNT(*) AS call_count,
            ROUND(AVG(CASE WHEN info.resolution_achieved THEN 1.0 ELSE 0.0 END) * 100, 1) AS resolution_rate_pct
        FROM extracted
        GROUP BY info.issue_type, info.churn_risk
        ORDER BY call_count DESC
    """))

elif industry == "gaming":
    display(spark.sql("""
        WITH extracted AS (
            SELECT
                report_id,
                from_json(ai_query(
                    'databricks-meta-llama-3-3-70b-instruct',
                    CONCAT('Analyze this player report: ', description),
                    responseFormat => '{"type":"json_schema","json_schema":{"name":"response","schema":{"type":"object","properties":{"incident_category":{"type":"string"},"severity_level":{"type":"string"},"recommended_action":{"type":"string"}}}}}'
                ), 'incident_category STRING, severity_level STRING, recommended_action STRING') AS info
            FROM player_reports
        )
        SELECT
            info.incident_category,
            info.severity_level,
            info.recommended_action,
            COUNT(*) AS report_count
        FROM extracted
        GROUP BY info.incident_category, info.severity_level, info.recommended_action
        ORDER BY report_count DESC
    """))

elif industry == "dnb":
    display(spark.sql("""
        WITH extracted AS (
            SELECT
                prospect_id, company_name,
                from_json(ai_query(
                    'databricks-meta-llama-3-3-70b-instruct',
                    CONCAT('Score this prospect for Databricks: ', description),
                    responseFormat => '{"type":"json_schema","json_schema":{"name":"response","schema":{"type":"object","properties":{"company_type":{"type":"string"},"funding_stage":{"type":"string"},"databricks_fit_score":{"type":"integer"}}}}}'
                ), 'company_type STRING, funding_stage STRING, databricks_fit_score BIGINT') AS info
            FROM prospect_companies
            LIMIT 30
        )
        SELECT prospect_id, company_name, info.company_type, info.funding_stage, info.databricks_fit_score
        FROM extracted
        ORDER BY info.databricks_fit_score DESC
    """))
