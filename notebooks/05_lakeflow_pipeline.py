# Databricks notebook source
# MAGIC %md
# MAGIC # Lab 5: Production Pipeline with Lakeflow Declarative Pipelines
# MAGIC
# MAGIC **Pattern:** Auto Loader → Bronze → Silver (AI enrichment) → Gold (quality-gated)
# MAGIC
# MAGIC The previous labs demonstrated AI Functions interactively. This lab shows how to
# MAGIC **productionize** the same patterns using Lakeflow Declarative Pipelines (formerly Delta Live Tables).
# MAGIC
# MAGIC Key advantages:
# MAGIC - **Incremental:** only new documents / records are processed
# MAGIC - **Self-healing:** retries and lineage tracking built-in
# MAGIC - **Quality gates:** `CONSTRAINT` clauses drop or quarantine bad AI outputs
# MAGIC - **Scheduled:** runs on a cron, triggered by file arrival, or on-demand via the API
# MAGIC
# MAGIC > **Note:** This notebook is a **pipeline definition file** — run it via the Lakeflow
# MAGIC > pipeline UI or via `databricks bundle run`, not as a regular notebook.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Architecture
# MAGIC
# MAGIC ```
# MAGIC /Volumes/.../documents/    (new PDFs land here continuously)
# MAGIC         |
# MAGIC         v   Auto Loader (cloudFiles)
# MAGIC  bronze_documents          raw binary + metadata
# MAGIC         |
# MAGIC         v   ai_parse_document
# MAGIC  silver_parsed             extracted text
# MAGIC         |
# MAGIC         v   ai_query (responseFormat)  +  ai_classify
# MAGIC  silver_enriched           structured, typed AI outputs
# MAGIC         |
# MAGIC         v   quality CONSTRAINT filters
# MAGIC  gold_insights             clean, trusted, analytics-ready
# MAGIC ```

# COMMAND ----------

import dlt
from pyspark.sql.functions import col, current_timestamp, regexp_extract

# ---------------------------------------------------------------------------
# Widget values — injected by the pipeline config
# ---------------------------------------------------------------------------
catalog        = spark.conf.get("pipeline.catalog",        "main")
schema_prefix  = spark.conf.get("pipeline.schema_prefix",  "ai_functions_workshop")
industry       = spark.conf.get("pipeline.industry",       "fins")
schema         = f"{schema_prefix}_{industry}"
volume_path    = f"/Volumes/{catalog}/{schema}/documents"
endpoint       = "databricks-meta-llama-3-3-70b-instruct"

# ---------------------------------------------------------------------------
# BRONZE: ingest raw files from the volume using Auto Loader
# ---------------------------------------------------------------------------

@dlt.table(
    name="bronze_documents",
    comment="Raw document bytes ingested from the Unity Catalog volume via Auto Loader",
)
def bronze_documents():
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "binaryFile")
        .option("pathGlobFilter", "*.pdf")
        .load(volume_path)
        .select(
            col("path"),
            col("content"),
            col("length").alias("file_size_bytes"),
            col("modificationTime").alias("file_modified_at"),
            regexp_extract(col("path"), r"[^/]+$", 0).alias("filename"),
            current_timestamp().alias("ingested_at"),
        )
    )

# ---------------------------------------------------------------------------
# SILVER: parse document text
# ---------------------------------------------------------------------------

@dlt.table(
    name="silver_parsed",
    comment="Parsed text extracted from PDF documents using ai_parse_document",
)
def silver_parsed():
    return dlt.read_stream("bronze_documents").selectExpr(
        "path",
        "filename",
        "file_size_bytes",
        "file_modified_at",
        "ai_parse_document(content) AS parsed_text",
        "ingested_at",
        "current_timestamp() AS parsed_at",
    )

# ---------------------------------------------------------------------------
# SILVER: AI enrichment — structured extraction + classification
# ---------------------------------------------------------------------------

if industry == "fins":
    @dlt.table(
        name="silver_enriched",
        comment="Structured product data extracted from parsed product sheets",
    )
    @dlt.expect("has_product_name", "extracted.product_name IS NOT NULL")
    @dlt.expect_or_drop("valid_apr", "extracted.apr_low > 0 AND extracted.apr_high >= extracted.apr_low")
    def silver_enriched_fins():
        return dlt.read_stream("silver_parsed").selectExpr(
            "path", "filename", "parsed_at",
            f"""ai_query(
                '{endpoint}',
                CONCAT('Extract financial product details from: ', parsed_text),
                responseFormat => schema_of_json('{{"product_name":"string","product_type":"string","apr_low":0.0,"apr_high":0.0,"min_income_usd":0,"max_amount_usd":0}}')
            ) AS extracted""",
            f"""ai_classify(parsed_text, ARRAY('secured_loan','unsecured_loan','premium_credit_card','standard_credit_card','secured_card')) AS product_category""",
        )

elif industry == "gaming":
    @dlt.table(
        name="silver_enriched",
        comment="Structured appeal analysis from parsed ban appeal letters",
    )
    @dlt.expect_or_drop("has_recommendation", "extracted.recommended_decision IS NOT NULL")
    def silver_enriched_gaming():
        return dlt.read_stream("silver_parsed").selectExpr(
            "path", "filename", "parsed_at",
            f"""ai_query(
                '{endpoint}',
                CONCAT('Analyze this player ban appeal: ', parsed_text),
                responseFormat => schema_of_json('{{"player_id":"string","ban_reason":"string","appeal_credibility":"string","recommended_decision":"string","evidence_provided":false}}')
            ) AS extracted""",
            f"""ai_classify(parsed_text, ARRAY('grant_appeal','deny_appeal','escalate_for_review','insufficient_evidence')) AS decision_label""",
        )

elif industry == "dnb":
    @dlt.table(
        name="silver_enriched",
        comment="ICP scoring from parsed company prospect profiles",
    )
    @dlt.expect("has_company", "extracted.company_name IS NOT NULL")
    @dlt.expect_or_drop("scored", "extracted.databricks_fit_score > 0")
    def silver_enriched_dnb():
        return dlt.read_stream("silver_parsed").selectExpr(
            "path", "filename", "parsed_at",
            f"""ai_query(
                '{endpoint}',
                CONCAT('Score this prospect profile for Databricks fit: ', parsed_text),
                responseFormat => schema_of_json('{{"company_name":"string","industry_sector":"string","funding_stage":"string","primary_pain_point":"string","databricks_fit_score":0}}')
            ) AS extracted""",
            f"""ai_classify(parsed_text, ARRAY('hot_lead','warm_lead','cold_lead','not_qualified')) AS lead_quality""",
        )

elif industry == "telco":
    @dlt.table(
        name="silver_enriched",
        comment="Survey analysis from parsed customer satisfaction surveys",
    )
    @dlt.expect_or_drop("has_nps", "extracted.nps_score >= 0")
    def silver_enriched_telco():
        return dlt.read_stream("silver_parsed").selectExpr(
            "path", "filename", "parsed_at",
            f"""ai_query(
                '{endpoint}',
                CONCAT('Extract NPS and sentiment from this survey: ', parsed_text),
                responseFormat => schema_of_json('{{"customer_id":"string","nps_score":0,"nps_category":"string","issue_type":"string","follow_up_required":false}}')
            ) AS extracted""",
            f"""ai_classify(parsed_text, ARRAY('promoter','passive','detractor')) AS nps_label""",
        )

elif industry == "mfg":
    @dlt.table(
        name="silver_enriched",
        comment="Root cause analysis from parsed inspection reports",
    )
    @dlt.expect("has_failure_mode", "extracted.failure_mode IS NOT NULL")
    @dlt.expect_or_drop("valid_downtime", "extracted.downtime_hours >= 0")
    def silver_enriched_mfg():
        return dlt.read_stream("silver_parsed").selectExpr(
            "path", "filename", "parsed_at",
            f"""ai_query(
                '{endpoint}',
                CONCAT('Extract root cause analysis from this inspection report: ', parsed_text),
                responseFormat => schema_of_json('{{"report_id":"string","failure_mode":"string","severity":"string","component_batch_id":"string","root_cause":"string","supplier_involved":false,"downtime_hours":0.0}}')
            ) AS extracted""",
            f"""ai_classify(parsed_text, ARRAY('critical_stop_production','major_schedule_maintenance','minor_monitor_only')) AS severity_action""",
        )

# ---------------------------------------------------------------------------
# GOLD: quality-gated analytics-ready table (batch, not streaming)
# ---------------------------------------------------------------------------

@dlt.table(
    name="gold_insights",
    comment="Analytics-ready AI enrichment results, quality-gated and deduped",
)
def gold_insights():
    enriched = dlt.read("silver_enriched")
    return enriched.select(
        "filename",
        "extracted.*",
        "parsed_at",
    ).dropDuplicates(["filename"])
