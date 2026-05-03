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
        ai_parse_document(content) AS parsed_text
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
            REGEXP_EXTRACT(path, '[^/]+$') AS filename,
            ai_query(
                'databricks-meta-llama-3-3-70b-instruct',
                CONCAT(
                    'Extract the following from this financial product sheet: ',
                    ai_parse_document(content)
                ),
                responseFormat => schema_of_json('{{
                    "product_name": "string",
                    "product_id": "string",
                    "apr_low": 0.0,
                    "apr_high": 0.0,
                    "min_income_usd": 0,
                    "max_amount_usd": 0,
                    "key_benefit": "string"
                }}')
            ) AS structured_product
        FROM read_files(
            '{volume_path}',
            format => 'binaryFile',
            pathGlobFilter => '*.pdf'
        )
    """))

elif industry == "gaming":
    display(spark.sql(f"""
        SELECT
            REGEXP_EXTRACT(path, '[^/]+$') AS filename,
            ai_query(
                'databricks-meta-llama-3-3-70b-instruct',
                CONCAT(
                    'Analyze this player ban appeal document: ',
                    ai_parse_document(content)
                ),
                responseFormat => schema_of_json('{{
                    "player_id": "string",
                    "ban_reason": "string",
                    "account_age_years": 0,
                    "appeal_credibility": "string",
                    "recommended_decision": "string",
                    "evidence_provided": false
                }}')
            ) AS appeal_analysis
        FROM read_files(
            '{volume_path}',
            format => 'binaryFile',
            pathGlobFilter => '*.pdf'
        )
    """))

elif industry == "dnb":
    display(spark.sql(f"""
        SELECT
            REGEXP_EXTRACT(path, '[^/]+$') AS filename,
            ai_query(
                'databricks-meta-llama-3-3-70b-instruct',
                CONCAT(
                    'Extract ICP scoring factors from this company profile: ',
                    ai_parse_document(content)
                ),
                responseFormat => schema_of_json('{{
                    "company_name": "string",
                    "industry_sector": "string",
                    "employee_count": 0,
                    "funding_stage": "string",
                    "data_maturity": "string",
                    "databricks_fit_score": 0,
                    "recommended_outreach_angle": "string"
                }}')
            ) AS icp_score
        FROM read_files(
            '{volume_path}',
            format => 'binaryFile',
            pathGlobFilter => '*.pdf'
        )
    """))

elif industry == "telco":
    display(spark.sql(f"""
        SELECT
            REGEXP_EXTRACT(path, '[^/]+$') AS filename,
            ai_query(
                'databricks-meta-llama-3-3-70b-instruct',
                CONCAT(
                    'Analyze this customer satisfaction survey: ',
                    ai_parse_document(content)
                ),
                responseFormat => schema_of_json('{{
                    "customer_id": "string",
                    "nps_score": 0,
                    "nps_category": "string",
                    "issue_type": "string",
                    "sentiment_summary": "string",
                    "follow_up_required": false,
                    "key_verbatim_theme": "string"
                }}')
            ) AS survey_analysis
        FROM read_files(
            '{volume_path}',
            format => 'binaryFile',
            pathGlobFilter => '*.pdf'
        )
    """))

elif industry == "mfg":
    display(spark.sql(f"""
        SELECT
            REGEXP_EXTRACT(path, '[^/]+$') AS filename,
            ai_query(
                'databricks-meta-llama-3-3-70b-instruct',
                CONCAT(
                    'Extract root cause analysis from this quality inspection report: ',
                    ai_parse_document(content)
                ),
                responseFormat => schema_of_json('{{
                    "report_id": "string",
                    "failure_mode": "string",
                    "failure_category": "string",
                    "severity": "string",
                    "component_batch_id": "string",
                    "root_cause": "string",
                    "supplier_involved": false,
                    "corrective_action": "string",
                    "downtime_hours": 0.0
                }}')
            ) AS rca_result
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
            REGEXP_EXTRACT(path, '[^/]+$') AS filename,
            ai_classify(
                ai_parse_document(content),
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
            REGEXP_EXTRACT(path, '[^/]+$') AS filename,
            ai_classify(
                ai_parse_document(content),
                ARRAY('critical_stop_production', 'major_schedule_maintenance', 'minor_monitor_only', 'informational')
            ) AS severity_action,
            ai_classify(
                ai_parse_document(content),
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
            REGEXP_EXTRACT(path, '[^/]+$') AS filename,
            ai_classify(
                ai_parse_document(content),
                ARRAY('promoter', 'passive', 'detractor')
            ) AS nps_category,
            ai_classify(
                ai_parse_document(content),
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
            REGEXP_EXTRACT(path, '[^/]+$') AS filename,
            ai_classify(
                ai_parse_document(content),
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
            REGEXP_EXTRACT(path, '[^/]+$') AS filename,
            ai_classify(
                ai_parse_document(content),
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
            REGEXP_EXTRACT(path, '[^/]+$') AS filename,
            path,
            ai_parse_document(content) AS raw_text,
            ai_classify(
                ai_parse_document(content),
                ARRAY('critical_stop_production', 'major_schedule_maintenance', 'minor_monitor_only')
            ) AS severity_action,
            ai_extract(
                ai_parse_document(content),
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
            REGEXP_EXTRACT(path, '[^/]+$') AS filename,
            path,
            ai_parse_document(content) AS raw_text,
            NOW() AS processed_at
        FROM read_files(
            '{volume_path}',
            format => 'binaryFile',
            pathGlobFilter => '*.pdf'
        )
    """)

display(spark.sql(f"SELECT * FROM {parsed_results_table} LIMIT 5"))
print(f"Saved {spark.sql(f'SELECT COUNT(*) FROM {parsed_results_table}').first()[0]} rows to {parsed_results_table}")
