# Databricks notebook source
# MAGIC %md
# MAGIC # Lab 4: Semantic Matching with `ai_similarity` & Vector Search
# MAGIC
# MAGIC **AI Functions:** `ai_similarity()`, `vector_search()`, `ai_query` (for summarization)
# MAGIC
# MAGIC Exact string matching breaks down in the real world. Merchant names get abbreviated,
# MAGIC customer queries use informal language, product descriptions use technical jargon.
# MAGIC
# MAGIC This lab shows two complementary approaches:
# MAGIC
# MAGIC | Approach | Function | Best For |
# MAGIC |---|---|---|
# MAGIC | Pairwise similarity | `ai_similarity(text1, text2)` | Scoring known candidate pairs |
# MAGIC | Semantic retrieval | `vector_search(index, query)` | Finding top-K matches from a large catalog |
# MAGIC
# MAGIC ---
# MAGIC ## The "Summarize → Embed → Match → Validate" Pattern
# MAGIC
# MAGIC ```
# MAGIC Raw text → ai_query (summarize) → Vector Search index (embeddings)
# MAGIC                                           |
# MAGIC Query → vector_search (top-K) → ai_query (validate match) → Ranked results
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

# COMMAND ----------

# MAGIC %md ## `ai_similarity` – Score pairwise text similarity

# COMMAND ----------

# MAGIC %md
# MAGIC ```sql
# MAGIC ai_similarity(text1, text2)   -- returns DOUBLE between 0.0 (dissimilar) and 1.0 (identical)
# MAGIC ```
# MAGIC
# MAGIC Useful for:
# MAGIC - Fuzzy merchant name matching
# MAGIC - Deduplication of product descriptions
# MAGIC - Validating vector search matches

# COMMAND ----------

if industry == "fins":
    # Fuzzy merchant name matching: raw transaction vs canonical names
    display(spark.sql("""
        SELECT
            t.transaction_id,
            t.merchant_name_raw,
            c.canonical_name,
            c.category,
            ROUND(ai_similarity(t.merchant_name_raw, c.canonical_name), 3) AS similarity_score
        FROM merchant_transactions t
        CROSS JOIN merchant_canonical c
        WHERE t.transaction_id IN ('TXN00001', 'TXN00002', 'TXN00003', 'TXN00004', 'TXN00005')
        ORDER BY t.transaction_id, similarity_score DESC
    """))

elif industry == "gaming":
    # Match incident descriptions to policy violation types
    policies = [
        ("POL001", "Harassment: Repeated targeted offensive behavior toward a specific player"),
        ("POL002", "Cheating: Use of unauthorized software or exploits to gain unfair advantage"),
        ("POL003", "Hate Speech: Use of discriminatory language based on race, gender, nationality"),
        ("POL004", "Griefing: Intentional disruption of other players' gameplay experience"),
    ]
    spark.createDataFrame(policies, ["policy_id", "policy_description"]).createOrReplaceTempView("policies")

    display(spark.sql("""
        SELECT
            r.report_id,
            r.incident_type,
            p.policy_id,
            p.policy_description,
            ROUND(ai_similarity(r.description, p.policy_description), 3) AS match_score
        FROM player_reports r CROSS JOIN policies p
        WHERE r.report_id IN ('RPT00001','RPT00002','RPT00003')
        ORDER BY r.report_id, match_score DESC
    """))

elif industry == "telco":
    display(spark.sql("""
        SELECT
            c.call_id,
            c.transcript,
            p.playbook_id,
            p.title,
            ROUND(ai_similarity(c.transcript, p.steps), 3) AS relevance_score
        FROM customer_calls c
        CROSS JOIN resolution_playbooks p
        WHERE c.call_id IN ('CALL00001','CALL00002','CALL00003')
        ORDER BY c.call_id, relevance_score DESC
    """))

elif industry == "mfg":
    # Match maintenance log notes to failure mode descriptions
    display(spark.sql("""
        WITH failure_definitions AS (
            SELECT 'Bearing Failure' AS mode, 'Metal fatigue or contamination causing rotating component seizure' AS definition UNION ALL
            SELECT 'Coolant Leak',   'Hydraulic line fracture or seal failure causing coolant loss' UNION ALL
            SELECT 'Belt Tear',      'Mechanical overload or age-related longitudinal belt tearing' UNION ALL
            SELECT 'Sensor Drift',   'Calibration error causing measurement deviation beyond acceptable threshold'
        )
        SELECT
            m.log_id,
            m.failure_mode AS reported_mode,
            f.mode AS definition_mode,
            ROUND(ai_similarity(m.technician_notes, f.definition), 3) AS semantic_match
        FROM maintenance_logs m CROSS JOIN failure_definitions f
        WHERE m.log_id IN ('MNT00001','MNT00002','MNT00003')
        ORDER BY m.log_id, semantic_match DESC
    """))

elif industry == "dnb":
    display(spark.sql("""
        SELECT
            p.prospect_id,
            p.company_name,
            i.icp_id,
            i.name AS icp_name,
            ROUND(ai_similarity(p.description, i.description), 3) AS icp_fit_score
        FROM prospect_companies p
        CROSS JOIN icp_profiles i
        WHERE p.prospect_id IN ('PROS0001','PROS0002','PROS0003')
        ORDER BY p.prospect_id, icp_fit_score DESC
    """))

# COMMAND ----------

# MAGIC %md ## Best-match: select top-1 match per record using window functions

# COMMAND ----------

if industry == "fins":
    display(spark.sql("""
        WITH scores AS (
            SELECT
                t.transaction_id,
                t.merchant_name_raw,
                t.amount,
                c.merchant_id,
                c.canonical_name,
                c.category,
                ai_similarity(t.merchant_name_raw, c.canonical_name) AS sim_score,
                ROW_NUMBER() OVER (PARTITION BY t.transaction_id ORDER BY ai_similarity(t.merchant_name_raw, c.canonical_name) DESC) AS rank
            FROM merchant_transactions t
            CROSS JOIN merchant_canonical c
            LIMIT 500  -- limit cross join for demo
        )
        SELECT
            transaction_id,
            merchant_name_raw,
            amount,
            canonical_name AS matched_merchant,
            category,
            ROUND(sim_score, 3) AS confidence
        FROM scores
        WHERE rank = 1
        ORDER BY confidence DESC
        LIMIT 20
    """))

elif industry == "telco":
    display(spark.sql("""
        WITH scored AS (
            SELECT
                c.call_id,
                c.issue_type AS actual_issue,
                p.playbook_id,
                p.title AS playbook_title,
                ai_similarity(c.transcript, p.steps) AS relevance,
                ROW_NUMBER() OVER (PARTITION BY c.call_id ORDER BY ai_similarity(c.transcript, p.steps) DESC) AS rnk
            FROM customer_calls c
            CROSS JOIN resolution_playbooks p
            LIMIT 500
        )
        SELECT call_id, actual_issue, playbook_title, ROUND(relevance, 3) AS relevance_score
        FROM scored
        WHERE rnk = 1
        ORDER BY relevance_score DESC
    """))

elif industry == "mfg":
    display(spark.sql("""
        WITH defs AS (
            SELECT 'Bearing Failure' AS mode, 'Metal fatigue in rotating components, high vibration, metal shavings' AS definition UNION ALL
            SELECT 'Coolant Leak', 'Hydraulic line fracture, coolant loss, seal failure' UNION ALL
            SELECT 'Belt Tear', 'Conveyor belt longitudinal tear from overload' UNION ALL
            SELECT 'Sensor Drift', 'Pressure sensor calibration error, measurement deviation'
        ),
        scored AS (
            SELECT
                m.log_id, m.failure_mode AS reported, d.mode AS candidate,
                ai_similarity(m.technician_notes, d.definition) AS sim,
                ROW_NUMBER() OVER (PARTITION BY m.log_id ORDER BY ai_similarity(m.technician_notes, d.definition) DESC) AS rnk
            FROM maintenance_logs m CROSS JOIN defs d LIMIT 300
        )
        SELECT log_id, reported, candidate AS ai_matched_mode, ROUND(sim, 3) AS confidence
        FROM scored WHERE rnk = 1
        ORDER BY confidence DESC LIMIT 20
    """))

# COMMAND ----------

# MAGIC %md ## AI-powered match validation with `ai_query`
# MAGIC
# MAGIC Use the LLM as a judge to verify whether a matched pair is semantically correct —
# MAGIC adding explainability and a confidence signal beyond the raw similarity score.

# COMMAND ----------

if industry == "fins":
    display(spark.sql("""
        WITH top_matches AS (
            SELECT
                t.transaction_id,
                t.merchant_name_raw,
                c.canonical_name,
                c.category,
                ROW_NUMBER() OVER (PARTITION BY t.transaction_id ORDER BY ai_similarity(t.merchant_name_raw, c.canonical_name) DESC) AS rnk
            FROM merchant_transactions t CROSS JOIN merchant_canonical c LIMIT 200
        )
        SELECT
            transaction_id,
            merchant_name_raw,
            canonical_name,
            category,
            from_json(ai_query(
                'databricks-meta-llama-3-3-70b-instruct',
                CONCAT('Does "', merchant_name_raw, '" refer to the merchant "', canonical_name, '"? Answer YES or NO and give a one-sentence reason.'),
                responseFormat => '{"type":"json_schema","json_schema":{"name":"response","schema":{"type":"object","properties":{"match_confirmed":{"type":"boolean"},"confidence":{"type":"string"},"reason":{"type":"string"}}}}}'
            ), 'match_confirmed BOOLEAN, confidence STRING, reason STRING') AS validation
        FROM top_matches
        WHERE rnk = 1
        LIMIT 10
    """))

elif industry == "telco":
    display(spark.sql("""
        WITH top_playbooks AS (
            SELECT
                c.call_id, c.transcript, p.playbook_id, p.title, p.steps,
                ROW_NUMBER() OVER (PARTITION BY c.call_id ORDER BY ai_similarity(c.transcript, p.steps) DESC) AS rnk
            FROM customer_calls c CROSS JOIN resolution_playbooks p LIMIT 300
        )
        SELECT
            call_id,
            title AS recommended_playbook,
            from_json(ai_query(
                'databricks-meta-llama-3-3-70b-instruct',
                CONCAT('Does this call transcript require this resolution playbook? Transcript: ', transcript, ' | Playbook: ', steps),
                responseFormat => '{"type":"json_schema","json_schema":{"name":"response","schema":{"type":"object","properties":{"playbook_relevant":{"type":"boolean"},"confidence_level":{"type":"string"},"alternative_suggestion":{"type":"string"}}}}}'
            ), 'playbook_relevant BOOLEAN, confidence_level STRING, alternative_suggestion STRING') AS validation
        FROM top_playbooks WHERE rnk = 1 LIMIT 10
    """))
