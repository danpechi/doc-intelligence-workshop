# Databricks notebook source
# MAGIC %md
# MAGIC # Lab 3: Document Parsing with `ai_parse_document`
# MAGIC
# MAGIC **AI Function:** `ai_parse_document(content)`
# MAGIC
# MAGIC `ai_parse_document` bridges the gap between **file-based data** stored in Unity Catalog Volumes
# MAGIC and SQL analytics. It natively parses PDFs, images, Word documents, and more — extracting
# MAGIC their text content in a format ready for downstream AI Functions like `ai_query` and `ai_classify`.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## The Pattern
# MAGIC
# MAGIC ```
# MAGIC Volume (PDFs)
# MAGIC      |
# MAGIC      v
# MAGIC read_files(..., format => 'binaryFile')   -- read raw bytes
# MAGIC      |
# MAGIC      v
# MAGIC ai_parse_document(content)                -- extract text/structure
# MAGIC      |
# MAGIC      v
# MAGIC ai_query / ai_classify / ai_extract       -- analyze extracted content
# MAGIC      |
# MAGIC      v
# MAGIC Delta Lake table                           -- queryable results
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
volume_path = f"/Volumes/{catalog}/{schema}/documents"

spark.sql(f"USE {full_schema}")
print(f"Volume: {volume_path}")

# COMMAND ----------

# MAGIC %md ## Step 1 – Inspect documents in the volume

# COMMAND ----------

display(spark.sql(f"""
    SELECT
        path,
        length,
        ROUND(length / 1024.0, 1) AS size_kb,
        modificationTime
    FROM read_files(
        '{volume_path}',
        format => 'binaryFile',
        pathGlobFilter => '*.pdf'
    )
    ORDER BY modificationTime DESC
"""))

# COMMAND ----------

# MAGIC %md ## Step 2 – Parse raw bytes with `ai_parse_document`

# COMMAND ----------

# MAGIC %md
# MAGIC `ai_parse_document` takes the **binary content** column from `read_files` and returns
# MAGIC the extracted text as a string. It handles:
# MAGIC - **PDFs** (text and scanned with OCR)
# MAGIC - **Images** (PNG, JPEG)
# MAGIC - **Microsoft Office** (Word, PowerPoint)

# COMMAND ----------

display(spark.sql(f"""
    SELECT
        path,
        CAST(ai_parse_document(content) AS STRING) AS parsed_text
    FROM read_files(
        '{volume_path}',
        format => 'binaryFile',
        pathGlobFilter => '*.pdf'
    )
    LIMIT 3
"""))

# COMMAND ----------

# MAGIC %md ## Step 3 – Chain `ai_parse_document` with `ai_query`
# MAGIC
# MAGIC The real power: parse the document *and* extract structured data in one SQL statement.

# COMMAND ----------

if industry == "fins":
    display(spark.sql(f"""
        SELECT
            REGEXP_EXTRACT(path, '[^/]+$', 0) AS filename,
            from_json(ai_query(
                'databricks-meta-llama-3-3-70b-instruct',
                CONCAT(
                    'Extract the following from this financial product sheet: ',
                    CAST(ai_parse_document(content) AS STRING)
                ),
                responseFormat => '{{"type":"json_schema","json_schema":{{"name":"response","schema":{{"type":"object","properties":{{"product_name":{{"type":"string"}},"product_id":{{"type":"string"}},"apr_low":{{"type":"number"}},"apr_high":{{"type":"number"}},"min_income_usd":{{"type":"integer"}},"max_amount_usd":{{"type":"integer"}},"key_benefit":{{"type":"string"}}}}}}}}}}'
            ), 'product_name STRING, product_id STRING, apr_low DOUBLE, apr_high DOUBLE, min_income_usd BIGINT, max_amount_usd BIGINT, key_benefit STRING') AS structured_product
        FROM read_files(
            '{volume_path}',
            format => 'binaryFile',
            pathGlobFilter => '*.pdf'
        )
    """))

elif industry == "gaming":
    display(spark.sql(f"""
        SELECT
            REGEXP_EXTRACT(path, '[^/]+$', 0) AS filename,
            from_json(ai_query(
                'databricks-meta-llama-3-3-70b-instruct',
                CONCAT(
                    'Analyze this player ban appeal document: ',
                    CAST(ai_parse_document(content) AS STRING)
                ),
                responseFormat => '{{"type":"json_schema","json_schema":{{"name":"response","schema":{{"type":"object","properties":{{"player_id":{{"type":"string"}},"ban_reason":{{"type":"string"}},"account_age_years":{{"type":"integer"}},"appeal_credibility":{{"type":"string"}},"recommended_decision":{{"type":"string"}},"evidence_provided":{{"type":"boolean"}}}}}}}}}}'
            ), 'player_id STRING, ban_reason STRING, account_age_years BIGINT, appeal_credibility STRING, recommended_decision STRING, evidence_provided BOOLEAN') AS appeal_analysis
        FROM read_files(
            '{volume_path}',
            format => 'binaryFile',
            pathGlobFilter => '*.pdf'
        )
    """))

elif industry == "dnb":
    display(spark.sql(f"""
        SELECT
            REGEXP_EXTRACT(path, '[^/]+$', 0) AS filename,
            from_json(ai_query(
                'databricks-meta-llama-3-3-70b-instruct',
                CONCAT(
                    'Extract ICP scoring factors from this company profile: ',
                    CAST(ai_parse_document(content) AS STRING)
                ),
                responseFormat => '{{"type":"json_schema","json_schema":{{"name":"response","schema":{{"type":"object","properties":{{"company_name":{{"type":"string"}},"industry_sector":{{"type":"string"}},"employee_count":{{"type":"integer"}},"funding_stage":{{"type":"string"}},"data_maturity":{{"type":"string"}},"databricks_fit_score":{{"type":"integer"}},"recommended_outreach_angle":{{"type":"string"}}}}}}}}}}'
            ), 'company_name STRING, industry_sector STRING, employee_count BIGINT, funding_stage STRING, data_maturity STRING, databricks_fit_score BIGINT, recommended_outreach_angle STRING') AS icp_score
        FROM read_files(
            '{volume_path}',
            format => 'binaryFile',
            pathGlobFilter => '*.pdf'
        )
    """))

elif industry == "telco":
    display(spark.sql(f"""
        SELECT
            REGEXP_EXTRACT(path, '[^/]+$', 0) AS filename,
            from_json(ai_query(
                'databricks-meta-llama-3-3-70b-instruct',
                CONCAT(
                    'Analyze this customer satisfaction survey: ',
                    CAST(ai_parse_document(content) AS STRING)
                ),
                responseFormat => '{{"type":"json_schema","json_schema":{{"name":"response","schema":{{"type":"object","properties":{{"customer_id":{{"type":"string"}},"nps_score":{{"type":"integer"}},"nps_category":{{"type":"string"}},"issue_type":{{"type":"string"}},"sentiment_summary":{{"type":"string"}},"follow_up_required":{{"type":"boolean"}},"key_verbatim_theme":{{"type":"string"}}}}}}}}}}'
            ), 'customer_id STRING, nps_score BIGINT, nps_category STRING, issue_type STRING, sentiment_summary STRING, follow_up_required BOOLEAN, key_verbatim_theme STRING') AS survey_analysis
        FROM read_files(
            '{volume_path}',
            format => 'binaryFile',
            pathGlobFilter => '*.pdf'
        )
    """))

elif industry == "mfg":
    display(spark.sql(f"""
        SELECT
            REGEXP_EXTRACT(path, '[^/]+$', 0) AS filename,
            from_json(ai_query(
                'databricks-meta-llama-3-3-70b-instruct',
                CONCAT(
                    'Extract root cause analysis from this quality inspection report: ',
                    CAST(ai_parse_document(content) AS STRING)
                ),
                responseFormat => '{{"type":"json_schema","json_schema":{{"name":"response","schema":{{"type":"object","properties":{{"report_id":{{"type":"string"}},"failure_mode":{{"type":"string"}},"failure_category":{{"type":"string"}},"severity":{{"type":"string"}},"component_batch_id":{{"type":"string"}},"root_cause":{{"type":"string"}},"supplier_involved":{{"type":"boolean"}},"corrective_action":{{"type":"string"}},"downtime_hours":{{"type":"number"}}}}}}}}}}'
            ), 'report_id STRING, failure_mode STRING, failure_category STRING, severity STRING, component_batch_id STRING, root_cause STRING, supplier_involved BOOLEAN, corrective_action STRING, downtime_hours DOUBLE') AS rca_result
        FROM read_files(
            '{volume_path}',
            format => 'binaryFile',
            pathGlobFilter => '*.pdf'
        )
    """))

# COMMAND ----------

# MAGIC %md ## Step 4 – Chain with `ai_classify` for bulk categorization

# COMMAND ----------

if industry == "gaming":
    display(spark.sql(f"""
        SELECT
            REGEXP_EXTRACT(path, '[^/]+$', 0) AS filename,
            ai_classify(
                CAST(ai_parse_document(content) AS STRING),
                ARRAY('grant_appeal', 'deny_appeal', 'escalate_for_review', 'insufficient_evidence')
            ) AS appeal_decision
        FROM read_files(
            '{volume_path}',
            format => 'binaryFile',
            pathGlobFilter => '*.pdf'
        )
    """))

elif industry == "mfg":
    display(spark.sql(f"""
        SELECT
            REGEXP_EXTRACT(path, '[^/]+$', 0) AS filename,
            ai_classify(
                CAST(ai_parse_document(content) AS STRING),
                ARRAY('critical_stop_production', 'major_schedule_maintenance', 'minor_monitor_only', 'informational')
            ) AS severity_action,
            ai_classify(
                CAST(ai_parse_document(content) AS STRING),
                ARRAY('supplier_quality_issue', 'operator_error', 'design_defect', 'maintenance_gap', 'environmental_factor')
            ) AS root_cause_category
        FROM read_files(
            '{volume_path}',
            format => 'binaryFile',
            pathGlobFilter => '*.pdf'
        )
    """))

elif industry == "telco":
    display(spark.sql(f"""
        SELECT
            REGEXP_EXTRACT(path, '[^/]+$', 0) AS filename,
            ai_classify(
                CAST(ai_parse_document(content) AS STRING),
                ARRAY('promoter', 'passive', 'detractor')
            ) AS nps_category,
            ai_classify(
                CAST(ai_parse_document(content) AS STRING),
                ARRAY('billing_issue', 'technical_problem', 'service_quality', 'plan_related', 'other')
            ) AS issue_category
        FROM read_files(
            '{volume_path}',
            format => 'binaryFile',
            pathGlobFilter => '*.pdf'
        )
    """))

elif industry == "dnb":
    display(spark.sql(f"""
        SELECT
            REGEXP_EXTRACT(path, '[^/]+$', 0) AS filename,
            ai_classify(
                CAST(ai_parse_document(content) AS STRING),
                ARRAY('hot_lead', 'warm_lead', 'cold_lead', 'not_qualified')
            ) AS lead_quality
        FROM read_files(
            '{volume_path}',
            format => 'binaryFile',
            pathGlobFilter => '*.pdf'
        )
    """))

elif industry == "fins":
    display(spark.sql(f"""
        SELECT
            REGEXP_EXTRACT(path, '[^/]+$', 0) AS filename,
            ai_classify(
                CAST(ai_parse_document(content) AS STRING),
                ARRAY('secured_loan', 'unsecured_loan', 'premium_credit_card', 'standard_credit_card', 'secured_card')
            ) AS product_category
        FROM read_files(
            '{volume_path}',
            format => 'binaryFile',
            pathGlobFilter => '*.pdf'
        )
    """))

# COMMAND ----------

# MAGIC %md ## Step 5 – Save results to Delta

# COMMAND ----------

parsed_results_table = f"{full_schema}.parsed_documents"

if industry == "mfg":
    spark.sql(f"""
        CREATE OR REPLACE TABLE {parsed_results_table} AS
        SELECT
            REGEXP_EXTRACT(path, '[^/]+$', 0) AS filename,
            path,
            CAST(ai_parse_document(content) AS STRING) AS raw_text,
            ai_classify(
                CAST(ai_parse_document(content) AS STRING),
                ARRAY('critical_stop_production', 'major_schedule_maintenance', 'minor_monitor_only')
            ) AS severity_action,
            ai_extract(
                CAST(ai_parse_document(content) AS STRING),
                ARRAY('component_batch_id', 'failure_mode', 'root_cause', 'downtime_hours')
            ) AS extracted_entities,
            NOW() AS processed_at
        FROM read_files(
            '{volume_path}',
            format => 'binaryFile',
            pathGlobFilter => '*.pdf'
        )
    """)
else:
    spark.sql(f"""
        CREATE OR REPLACE TABLE {parsed_results_table} AS
        SELECT
            REGEXP_EXTRACT(path, '[^/]+$', 0) AS filename,
            path,
            CAST(ai_parse_document(content) AS STRING) AS raw_text,
            NOW() AS processed_at
        FROM read_files(
            '{volume_path}',
            format => 'binaryFile',
            pathGlobFilter => '*.pdf'
        )
    """)

display(spark.sql(f"SELECT * FROM {parsed_results_table} LIMIT 5"))
print(f"Saved {spark.sql(f'SELECT COUNT(*) FROM {parsed_results_table}').first()[0]} rows to {parsed_results_table}")
