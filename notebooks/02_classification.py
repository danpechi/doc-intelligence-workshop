# Databricks notebook source
# MAGIC %md
# MAGIC # Lab 2: Classification & Entity Extraction
# MAGIC
# MAGIC **AI Functions:** `ai_classify()` and `ai_extract()`
# MAGIC
# MAGIC These are purpose-built SQL functions for high-volume classification and extraction tasks.
# MAGIC Unlike `ai_query`, they require **no prompt engineering** — just provide a list of labels
# MAGIC or entity names, and the model handles the rest.
# MAGIC
# MAGIC | Function | Use Case | Syntax |
# MAGIC |---|---|---|
# MAGIC | `ai_classify` | Label text into one of N categories | `ai_classify(content, ARRAY('cat1', 'cat2'))` |
# MAGIC | `ai_extract` | Pull named entities from text | `ai_extract(content, ARRAY('name', 'amount', 'date'))` |
# MAGIC
# MAGIC Both are designed for **batch inference at scale** with minimal configuration.

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

# COMMAND ----------

# MAGIC %md ## `ai_classify` – Zero-shot text classification

# COMMAND ----------

# MAGIC %md
# MAGIC ```sql
# MAGIC -- Syntax
# MAGIC ai_classify(
# MAGIC   content,                       -- text column or expression
# MAGIC   ARRAY('label1', 'label2', ...) -- exhaustive label set
# MAGIC )
# MAGIC ```
# MAGIC
# MAGIC Returns the **most appropriate label** from the provided array.
# MAGIC The labels should be mutually exclusive and cover all cases.

# COMMAND ----------

if industry == "gaming":
    # Content moderation: classify chat messages
    display(spark.sql("""
        SELECT
            message_id,
            player_id,
            message_text,
            ai_classify(
                message_text,
                ARRAY('safe', 'offensive_language', 'harassment', 'hate_speech', 'threat')
            ) AS moderation_label,
            expected_label
        FROM chat_logs
        LIMIT 30
    """))

elif industry == "fins":
    # Risk classification of transactions
    display(spark.sql("""
        SELECT
            transaction_id,
            merchant_name_raw,
            amount,
            ai_classify(
                CONCAT('Transaction of $', CAST(amount AS STRING), ' at ', merchant_name_raw),
                ARRAY('low_risk', 'medium_risk', 'high_risk', 'potential_fraud')
            ) AS risk_label
        FROM merchant_transactions
        LIMIT 30
    """))

elif industry == "dnb":
    # Lead quality classification
    display(spark.sql("""
        SELECT
            prospect_id,
            company_name,
            funding_stage,
            ai_classify(
                description,
                ARRAY('hot_lead', 'warm_lead', 'cold_lead', 'not_qualified')
            ) AS lead_quality
        FROM prospect_companies
        LIMIT 30
    """))

elif industry == "telco":
    # Classify call type + churn risk
    display(spark.sql("""
        SELECT
            call_id,
            agent_id,
            ai_classify(
                transcript,
                ARRAY('billing_issue', 'technical_problem', 'plan_change_request', 'churn_risk', 'general_enquiry', 'positive_feedback')
            ) AS call_category,
            ai_classify(
                transcript,
                ARRAY('high_churn_risk', 'medium_churn_risk', 'low_churn_risk', 'no_churn_risk')
            ) AS churn_risk_label
        FROM customer_calls
        LIMIT 30
    """))

elif industry == "mfg":
    # Failure mode classification + severity
    display(spark.sql("""
        SELECT
            log_id,
            line_id,
            failure_mode,
            ai_classify(
                technician_notes,
                ARRAY('mechanical_failure', 'electrical_fault', 'hydraulic_issue', 'software_error', 'quality_defect', 'operator_error')
            ) AS failure_category_ai,
            ai_classify(
                technician_notes,
                ARRAY('critical', 'major', 'minor', 'informational')
            ) AS severity_ai,
            severity AS severity_original
        FROM maintenance_logs
        LIMIT 30
    """))

# COMMAND ----------

# MAGIC %md ## Accuracy check – Compare AI classification vs ground truth labels

# COMMAND ----------

if industry == "gaming":
    display(spark.sql("""
        WITH classified AS (
            SELECT
                message_id,
                expected_label,
                ai_classify(
                    message_text,
                    ARRAY('safe', 'offensive_language', 'harassment', 'hate_speech', 'threat')
                ) AS ai_label
            FROM chat_logs
            LIMIT 100
        )
        SELECT
            expected_label,
            ai_label,
            COUNT(*) AS count,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY expected_label), 1) AS pct
        FROM classified
        GROUP BY expected_label, ai_label
        ORDER BY expected_label, count DESC
    """))

elif industry == "mfg":
    display(spark.sql("""
        WITH classified AS (
            SELECT
                log_id,
                severity AS ground_truth,
                ai_classify(
                    technician_notes,
                    ARRAY('critical', 'major', 'minor', 'informational')
                ) AS ai_severity
            FROM maintenance_logs
            LIMIT 100
        )
        SELECT
            ground_truth,
            ai_severity,
            COUNT(*) AS count
        FROM classified
        GROUP BY ground_truth, ai_severity
        ORDER BY ground_truth
    """))

elif industry == "telco":
    display(spark.sql("""
        WITH classified AS (
            SELECT
                call_id,
                issue_type AS ground_truth,
                ai_classify(
                    transcript,
                    ARRAY('billing_issue', 'technical_problem', 'plan_change_request', 'churn_risk', 'general_enquiry', 'positive_feedback')
                ) AS ai_category
            FROM customer_calls
            LIMIT 100
        )
        SELECT
            ground_truth,
            ai_category,
            COUNT(*) AS count
        FROM classified
        GROUP BY ground_truth, ai_category
        ORDER BY ground_truth
    """))

# COMMAND ----------

# MAGIC %md ## `ai_extract` – Named entity extraction

# COMMAND ----------

# MAGIC %md
# MAGIC ```sql
# MAGIC -- Syntax
# MAGIC ai_extract(
# MAGIC   content,                           -- text column
# MAGIC   ARRAY('entity_name_1', 'entity_2') -- what to extract
# MAGIC )
# MAGIC ```
# MAGIC
# MAGIC Returns a STRUCT where each field corresponds to one entity name.
# MAGIC Entities not found in the text return `NULL`.

# COMMAND ----------

if industry == "fins":
    display(spark.sql("""
        SELECT
            transaction_id,
            merchant_name_raw,
            amount,
            ai_extract(
                CONCAT('Transaction: ', merchant_name_raw, ', Amount: $', CAST(amount AS STRING)),
                ARRAY('merchant_name', 'transaction_amount', 'currency', 'merchant_category')
            ) AS entities
        FROM merchant_transactions
        LIMIT 20
    """))

elif industry == "gaming":
    display(spark.sql("""
        SELECT
            report_id,
            ai_extract(
                description,
                ARRAY('reported_player_action', 'location_in_game', 'evidence_type', 'duration_of_incident')
            ) AS entities
        FROM player_reports
        LIMIT 20
    """))

elif industry == "dnb":
    display(spark.sql("""
        SELECT
            prospect_id,
            company_name,
            ai_extract(
                description,
                ARRAY('company_size', 'funding_amount', 'technology_platform', 'pain_point', 'growth_rate')
            ) AS entities
        FROM prospect_companies
        LIMIT 20
    """))

elif industry == "telco":
    display(spark.sql("""
        SELECT
            call_id,
            ai_extract(
                transcript,
                ARRAY('issue_description', 'customer_request', 'amount_disputed', 'service_affected', 'resolution_offered')
            ) AS entities
        FROM customer_calls
        LIMIT 20
    """))

elif industry == "mfg":
    display(spark.sql("""
        SELECT
            log_id,
            line_id,
            ai_extract(
                technician_notes,
                ARRAY('component_batch_id', 'supplier_name', 'failure_symptom', 'measurement_value', 'corrective_action_taken')
            ) AS entities
        FROM maintenance_logs
        LIMIT 20
    """))

# COMMAND ----------

# MAGIC %md ## Combine `ai_classify` + `ai_extract` in one pass

# COMMAND ----------

if industry == "mfg":
    display(spark.sql("""
        SELECT
            log_id,
            line_id,
            downtime_hours,
            ai_classify(
                technician_notes,
                ARRAY('mechanical_failure', 'electrical_fault', 'hydraulic_issue', 'quality_defect')
            ) AS failure_category,
            ai_classify(
                technician_notes,
                ARRAY('critical', 'major', 'minor')
            ) AS ai_severity,
            ai_extract(
                technician_notes,
                ARRAY('component_batch_id', 'supplier_name', 'root_cause')
            ) AS extracted_entities
        FROM maintenance_logs
        LIMIT 30
    """))

elif industry == "telco":
    display(spark.sql("""
        SELECT
            call_id,
            ai_classify(transcript, ARRAY('billing_issue', 'technical_problem', 'churn_risk', 'plan_change_request', 'other')) AS call_type,
            ai_classify(transcript, ARRAY('high_churn_risk', 'low_churn_risk', 'no_churn_risk')) AS churn_risk,
            ai_extract(transcript, ARRAY('disputed_amount', 'service_name', 'resolution_timeline')) AS key_entities
        FROM customer_calls
        LIMIT 30
    """))

elif industry == "gaming":
    display(spark.sql("""
        SELECT
            message_id,
            message_text,
            ai_classify(message_text, ARRAY('safe', 'warning', 'violation', 'ban_worthy')) AS severity,
            ai_extract(message_text, ARRAY('target_player', 'offensive_term', 'threat_type')) AS entities
        FROM chat_logs
        WHERE expected_label != 'safe'
        LIMIT 20
    """))

elif industry == "dnb":
    display(spark.sql("""
        SELECT
            prospect_id,
            company_name,
            ai_classify(description, ARRAY('hot_lead', 'warm_lead', 'cold_lead')) AS lead_quality,
            ai_extract(description, ARRAY('annual_revenue', 'headcount', 'growth_rate', 'primary_tool')) AS biz_entities
        FROM prospect_companies
        LIMIT 30
    """))

elif industry == "fins":
    display(spark.sql("""
        SELECT
            product_id,
            product_name,
            ai_classify(document_text, ARRAY('secured_loan', 'unsecured_loan', 'credit_card', 'line_of_credit')) AS product_type,
            ai_extract(document_text, ARRAY('minimum_income', 'maximum_amount', 'apr_range', 'loan_term')) AS terms
        FROM product_documents
    """))
