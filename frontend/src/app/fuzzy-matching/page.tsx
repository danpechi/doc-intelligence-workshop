"use client";

import { useIndustry } from "@/lib/useIndustry";
import WorkshopStep from "@/components/WorkshopStep";
import CodeBlock from "@/components/CodeBlock";
import InfoBox from "@/components/InfoBox";

const SIMILARITY_EXAMPLES: Record<string, { pairwise: string; bestMatch: string; validate: string; matchDesc: string }> = {
  fins: {
    matchDesc: "Match raw transaction merchant names against a canonical merchant registry, even when abbreviated, misspelled, or truncated.",
    pairwise: `-- Score every (transaction, merchant) pair
SELECT
    t.transaction_id,
    t.merchant_name_raw,
    c.canonical_name,
    c.category,
    ROUND(ai_similarity(t.merchant_name_raw, c.canonical_name), 3) AS similarity_score
FROM merchant_transactions t
CROSS JOIN merchant_canonical c
WHERE t.transaction_id IN ('TXN00001', 'TXN00002', 'TXN00003')
ORDER BY t.transaction_id, similarity_score DESC;`,
    bestMatch: `-- Best-match: top-1 canonical merchant per transaction
WITH scored AS (
    SELECT
        t.transaction_id,
        t.merchant_name_raw,
        t.amount,
        c.merchant_id,
        c.canonical_name,
        c.category,
        ai_similarity(t.merchant_name_raw, c.canonical_name) AS sim_score,
        ROW_NUMBER() OVER (
            PARTITION BY t.transaction_id
            ORDER BY ai_similarity(t.merchant_name_raw, c.canonical_name) DESC
        ) AS rnk
    FROM merchant_transactions t
    CROSS JOIN merchant_canonical c
    LIMIT 1000  -- limit cross join for demo
)
SELECT
    transaction_id,
    merchant_name_raw,
    amount,
    canonical_name   AS matched_merchant,
    category,
    ROUND(sim_score, 3) AS confidence
FROM scored
WHERE rnk = 1
ORDER BY confidence DESC
LIMIT 30;`,
    validate: `-- Validate top matches with ai_query as a judge
WITH top_matches AS (
    SELECT
        t.transaction_id, t.merchant_name_raw, c.canonical_name, c.category,
        ROW_NUMBER() OVER (PARTITION BY t.transaction_id ORDER BY ai_similarity(t.merchant_name_raw, c.canonical_name) DESC) AS rnk
    FROM merchant_transactions t CROSS JOIN merchant_canonical c LIMIT 500
)
SELECT
    transaction_id, merchant_name_raw, canonical_name, category,
    ai_query(
        'databricks-meta-llama-3-3-70b-instruct',
        CONCAT('Does "', merchant_name_raw, '" refer to the merchant "', canonical_name, '"? Answer YES or NO.'),
        responseFormat => schema_of_json('{"match_confirmed": false, "confidence": "string", "reason": "string"}')
    ) AS validation
FROM top_matches
WHERE rnk = 1
LIMIT 10;`,
  },
  gaming: {
    matchDesc: "Match player conduct incident descriptions against policy violation definitions to identify the most applicable rule.",
    pairwise: `-- Score incident descriptions against policy definitions
WITH policies AS (
    SELECT 'POL001' AS policy_id, 'Harassment: Repeated targeted offensive behavior toward a specific player' AS definition UNION ALL
    SELECT 'POL002', 'Cheating: Use of unauthorized software or exploits to gain unfair advantage' UNION ALL
    SELECT 'POL003', 'Hate Speech: Discriminatory language based on protected characteristics' UNION ALL
    SELECT 'POL004', 'Griefing: Intentional disruption of other players experience'
)
SELECT
    r.report_id,
    r.incident_type,
    p.policy_id,
    ROUND(ai_similarity(r.description, p.definition), 3) AS match_score
FROM player_reports r
CROSS JOIN policies p
WHERE r.report_id IN ('RPT00001','RPT00002','RPT00003')
ORDER BY r.report_id, match_score DESC;`,
    bestMatch: `WITH policies AS (
    SELECT 'POL001' AS id, 'Harassment: Repeated targeted offensive behavior toward a specific player' AS def UNION ALL
    SELECT 'POL002', 'Cheating: Use of unauthorized software or exploits' UNION ALL
    SELECT 'POL003', 'Hate Speech: Discriminatory language based on protected characteristics' UNION ALL
    SELECT 'POL004', 'Griefing: Intentional disruption of gameplay'
),
scored AS (
    SELECT r.report_id, r.incident_type, p.id AS policy_id, p.def,
           ai_similarity(r.description, p.def) AS sim,
           ROW_NUMBER() OVER (PARTITION BY r.report_id ORDER BY ai_similarity(r.description, p.def) DESC) AS rnk
    FROM player_reports r CROSS JOIN policies p LIMIT 400
)
SELECT report_id, incident_type, policy_id, ROUND(sim, 3) AS match_confidence
FROM scored WHERE rnk = 1 ORDER BY match_confidence DESC LIMIT 30;`,
    validate: `WITH policies AS (SELECT 'POL001' AS id, 'Harassment' AS def UNION ALL SELECT 'POL002', 'Cheating'),
top AS (SELECT r.report_id, r.description, p.id, p.def,
        ROW_NUMBER() OVER (PARTITION BY r.report_id ORDER BY ai_similarity(r.description, p.def) DESC) AS rnk
        FROM player_reports r CROSS JOIN policies p LIMIT 200)
SELECT report_id, id AS policy_matched,
       ai_query('databricks-meta-llama-3-3-70b-instruct',
         CONCAT('Does this incident violate this policy? Incident: ', description, ' | Policy: ', def),
         responseFormat => schema_of_json('{"policy_violated":false,"confidence":"string","recommended_action":"string"}')
       ) AS validation
FROM top WHERE rnk = 1 LIMIT 10;`,
  },
  dnb: {
    matchDesc: "Match prospect company descriptions against Ideal Customer Profile (ICP) definitions to score and rank leads.",
    pairwise: `SELECT
    p.prospect_id,
    p.company_name,
    i.icp_id,
    i.name AS icp_name,
    ROUND(ai_similarity(p.description, i.description), 3) AS icp_fit_score
FROM prospect_companies p
CROSS JOIN icp_profiles i
WHERE p.prospect_id IN ('PROS0001','PROS0002','PROS0003')
ORDER BY p.prospect_id, icp_fit_score DESC;`,
    bestMatch: `WITH scored AS (
    SELECT
        p.prospect_id, p.company_name, p.funding_stage,
        i.icp_id, i.name AS icp_name,
        ai_similarity(p.description, i.description) AS fit_score,
        ROW_NUMBER() OVER (PARTITION BY p.prospect_id ORDER BY ai_similarity(p.description, i.description) DESC) AS rnk
    FROM prospect_companies p CROSS JOIN icp_profiles i LIMIT 500
)
SELECT prospect_id, company_name, funding_stage, icp_name,
       ROUND(fit_score, 3) AS icp_fit_score
FROM scored WHERE rnk = 1
ORDER BY icp_fit_score DESC LIMIT 30;`,
    validate: `WITH top AS (SELECT p.prospect_id, p.company_name, p.description, i.icp_id, i.name, i.description AS icp_desc,
         ROW_NUMBER() OVER (PARTITION BY p.prospect_id ORDER BY ai_similarity(p.description, i.description) DESC) AS rnk
         FROM prospect_companies p CROSS JOIN icp_profiles i LIMIT 300)
SELECT prospect_id, company_name, name AS best_icp,
    ai_query('databricks-meta-llama-3-3-70b-instruct',
        CONCAT('Is this company a fit for this ICP? Company: ', description, ' | ICP: ', icp_desc),
        responseFormat => schema_of_json('{"is_fit":false,"fit_reason":"string","recommended_email_angle":"string"}')
    ) AS icp_validation
FROM top WHERE rnk = 1 LIMIT 10;`,
  },
  telco: {
    matchDesc: "Match call transcripts to resolution playbooks to automatically route each call type to the correct response procedure.",
    pairwise: `SELECT
    c.call_id,
    c.issue_type   AS actual_issue,
    p.playbook_id,
    p.title        AS playbook_name,
    ROUND(ai_similarity(c.transcript, p.steps), 3) AS relevance_score
FROM customer_calls c
CROSS JOIN resolution_playbooks p
WHERE c.call_id IN ('CALL00001','CALL00002','CALL00003')
ORDER BY c.call_id, relevance_score DESC;`,
    bestMatch: `WITH scored AS (
    SELECT
        c.call_id, c.issue_type, c.agent_id,
        p.playbook_id, p.title,
        ai_similarity(c.transcript, p.steps) AS relevance,
        ROW_NUMBER() OVER (PARTITION BY c.call_id ORDER BY ai_similarity(c.transcript, p.steps) DESC) AS rnk
    FROM customer_calls c CROSS JOIN resolution_playbooks p LIMIT 500
)
SELECT call_id, issue_type, agent_id, title AS matched_playbook,
       ROUND(relevance, 3) AS relevance_score
FROM scored WHERE rnk = 1
ORDER BY relevance_score DESC LIMIT 30;`,
    validate: `WITH top AS (SELECT c.call_id, c.transcript, p.playbook_id, p.title, p.steps,
         ROW_NUMBER() OVER (PARTITION BY c.call_id ORDER BY ai_similarity(c.transcript, p.steps) DESC) AS rnk
         FROM customer_calls c CROSS JOIN resolution_playbooks p LIMIT 400)
SELECT call_id, title AS recommended_playbook,
    ai_query('databricks-meta-llama-3-3-70b-instruct',
        CONCAT('Is this playbook correct for this call? Call: ', transcript, ' | Playbook: ', steps),
        responseFormat => schema_of_json('{"playbook_correct":false,"confidence":"string","alternative_action":"string"}')
    ) AS validation
FROM top WHERE rnk = 1 LIMIT 10;`,
  },
  mfg: {
    matchDesc: "Match technician notes and maintenance log descriptions to canonical failure mode definitions to standardize and route root cause analysis.",
    pairwise: `WITH failure_defs AS (
    SELECT 'Bearing Failure' AS mode, 'Metal fatigue or contamination causing rotating component seizure, vibration, metal shavings' AS definition UNION ALL
    SELECT 'Coolant Leak',   'Hydraulic line fracture or seal failure, coolant loss, production stoppage' UNION ALL
    SELECT 'Belt Tear',      'Conveyor belt longitudinal tear from mechanical overload or age-related wear' UNION ALL
    SELECT 'Sensor Drift',   'Calibration error causing measurement deviation beyond acceptable quality threshold'
)
SELECT
    m.log_id, m.failure_mode AS reported_mode,
    f.mode AS candidate_mode,
    ROUND(ai_similarity(m.technician_notes, f.definition), 3) AS semantic_match
FROM maintenance_logs m CROSS JOIN failure_defs f
WHERE m.log_id IN ('MNT00001','MNT00002','MNT00003')
ORDER BY m.log_id, semantic_match DESC;`,
    bestMatch: `WITH defs AS (
    SELECT 'Bearing Failure' AS mode, 'Metal fatigue, vibration, metal shavings in rotating component' AS def UNION ALL
    SELECT 'Coolant Leak', 'Hydraulic line fracture, coolant loss, seal failure' UNION ALL
    SELECT 'Belt Tear', 'Conveyor belt longitudinal tear from overload or age' UNION ALL
    SELECT 'Sensor Drift', 'Pressure sensor calibration error, measurement deviation'
),
scored AS (
    SELECT m.log_id, m.failure_mode AS reported, d.mode AS candidate,
           ai_similarity(m.technician_notes, d.def) AS sim,
           ROW_NUMBER() OVER (PARTITION BY m.log_id ORDER BY ai_similarity(m.technician_notes, d.def) DESC) AS rnk
    FROM maintenance_logs m CROSS JOIN defs d LIMIT 400
)
SELECT log_id, reported, candidate AS ai_matched_mode, ROUND(sim, 3) AS confidence
FROM scored WHERE rnk = 1
ORDER BY confidence DESC LIMIT 30;`,
    validate: `WITH defs AS (SELECT 'Bearing Failure' AS mode, 'Metal fatigue in rotating components' AS def UNION ALL
               SELECT 'Coolant Leak', 'Hydraulic line fracture causing coolant loss'),
top AS (SELECT m.log_id, m.technician_notes, d.mode, d.def,
        ROW_NUMBER() OVER (PARTITION BY m.log_id ORDER BY ai_similarity(m.technician_notes, d.def) DESC) AS rnk
        FROM maintenance_logs m CROSS JOIN defs d LIMIT 200)
SELECT log_id, mode AS matched_failure_mode,
    ai_query('databricks-meta-llama-3-3-70b-instruct',
        CONCAT('Do these technician notes match this failure mode? Notes: ', technician_notes, ' | Mode: ', def),
        responseFormat => schema_of_json('{"match_correct":false,"actual_failure_mode":"string","confidence":"string"}')
    ) AS validation
FROM top WHERE rnk = 1 LIMIT 10;`,
  },
};

export default function FuzzyMatchingPage() {
  const { config, industry } = useIndustry();
  const ex = SIMILARITY_EXAMPLES[industry];

  return (
    <div className="max-w-5xl mx-auto px-6 py-10">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <span className="text-4xl">🔗</span>
          <div>
            <h1 className="text-3xl font-bold text-white">Semantic Matching</h1>
            <p className="text-orange-400 font-mono text-sm">ai_similarity · vector_search()</p>
          </div>
        </div>
        <p className="text-slate-400 text-base max-w-3xl">
          Exact string matching breaks down in the real world — merchant names get abbreviated,
          customer queries use informal language, failure descriptions vary by technician.
          <code className="text-orange-300"> ai_similarity</code> scores semantic closeness between any two text strings,
          enabling fuzzy matching directly in SQL.
        </p>
        <div className="mt-3 text-sm text-slate-500">
          Industry: <span className="text-white font-semibold">{config.icon} {config.fullName}</span>
          {" "}| Matching: <span className="text-slate-300">{ex.matchDesc}</span>
        </div>
      </div>

      {/* When to use what */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-10">
        {[
          {
            fn: "ai_similarity(text1, text2)",
            returns: "DOUBLE between 0.0 and 1.0",
            bestFor: "Scoring known candidate pairs. Use with CROSS JOIN + ROW_NUMBER() for best-match selection.",
            when: "Catalog size < 10,000 entries",
            color: "blue",
          },
          {
            fn: "vector_search(index, query, ...)",
            returns: "Top-K matching rows with similarity scores",
            bestFor: "Finding matches from a large catalog without a CROSS JOIN. Millisecond latency at any scale.",
            when: "Catalog size > 10,000 entries",
            color: "purple",
          },
        ].map((item) => (
          <div
            key={item.fn}
            className="p-5 rounded-xl border border-slate-700/50"
            style={{ backgroundColor: "var(--color-navy-light)" }}
          >
            <p className={`font-mono text-sm font-bold mb-2 text-${item.color}-400`}>{item.fn}</p>
            <p className="text-slate-400 text-xs mb-1"><span className="text-slate-300">Returns:</span> {item.returns}</p>
            <p className="text-slate-400 text-xs mb-1"><span className="text-slate-300">Best for:</span> {item.bestFor}</p>
            <p className="text-slate-400 text-xs"><span className="text-slate-300">Use when:</span> {item.when}</p>
          </div>
        ))}
      </div>

      <WorkshopStep number={1} title="Score pairwise similarity with ai_similarity">
        <p className="text-slate-400 text-sm mb-4">
          Use a CROSS JOIN to generate all candidate pairs, then score each with <code className="text-orange-300">ai_similarity</code>.
          This is perfect for small catalogs (hundreds to low thousands of entries).
        </p>
        <CodeBlock
          language="sql"
          title="Pairwise similarity scoring"
          code={ex.pairwise}
        />
        <InfoBox type="info" title="Score interpretation">
          <ul className="list-disc list-inside space-y-1 text-xs">
            <li><strong>0.9 – 1.0:</strong> Near-identical or same entity with minor formatting differences</li>
            <li><strong>0.7 – 0.9:</strong> Strong semantic match — likely the same concept</li>
            <li><strong>0.5 – 0.7:</strong> Related but distinct — review manually</li>
            <li><strong>Below 0.5:</strong> Semantically dissimilar</li>
          </ul>
        </InfoBox>
      </WorkshopStep>

      <WorkshopStep number={2} title="Select the best match per record">
        <p className="text-slate-400 text-sm mb-4">
          Use <code className="text-orange-300">ROW_NUMBER() OVER (PARTITION BY ... ORDER BY similarity DESC)</code>{" "}
          to pick the top-1 match per source record.
        </p>
        <CodeBlock
          language="sql"
          title="Best-match selection with window functions"
          code={ex.bestMatch}
        />
      </WorkshopStep>

      <WorkshopStep number={3} title="Validate matches with ai_query as a judge">
        <p className="text-slate-400 text-sm mb-4">
          Add a validation layer: use the LLM to confirm whether the top similarity match is actually correct,
          providing explainability and a quality gate beyond the raw score.
        </p>
        <CodeBlock
          language="sql"
          title="LLM-as-judge validation"
          code={ex.validate}
        />
        <InfoBox type="tip" title="The summarize-embed-validate pattern">
          For large catalogs, the full production pattern is:
          <br />1. <strong>Summarize</strong> catalog entries with <code>ai_query</code> to improve embedding quality
          <br />2. <strong>Embed</strong> using a Vector Search Delta Sync index (auto-updated)
          <br />3. <strong>Retrieve</strong> top-K matches with <code>vector_search()</code>
          <br />4. <strong>Validate</strong> top match with <code>ai_query</code> as a judge
        </InfoBox>
      </WorkshopStep>

      <WorkshopStep number={4} title="Generate semantic summaries for better embeddings">
        <p className="text-slate-400 text-sm mb-4">
          Before embedding, generate a concise 2-3 sentence summary. This dramatically improves retrieval
          quality because the embedding captures semantic meaning rather than formatting artifacts.
        </p>
        <CodeBlock
          language="sql"
          title="Summarize catalog entries before embedding"
          code={`-- Step 1: generate summaries (store in a new column)
ALTER TABLE ${config.matchTarget.split("(")[0].trim()}
ADD COLUMN IF NOT EXISTS semantic_summary STRING;

UPDATE main.ai_functions_workshop_${industry}.${config.primaryTable}
SET semantic_summary = ai_query(
    'databricks-meta-llama-3-3-70b-instruct',
    CONCAT('Write a 2-sentence plain-language description of this record that captures its key meaning: ', ${config.primaryTextColumn})
)
WHERE semantic_summary IS NULL;

-- Step 2: the Vector Search Delta Sync index picks up the new column automatically`}
        />
      </WorkshopStep>

      <WorkshopStep number={5} title="vector_search() — scale to millions of entries">
        <InfoBox type="info" title="Prerequisites">
          A Vector Search endpoint and Delta Sync index must be created first. See the
          Databricks documentation or use the <code>databricks-vector-search</code> skill to set them up.
        </InfoBox>
        <CodeBlock
          language="sql"
          title="Semantic retrieval with vector_search()"
          code={`-- After creating a Vector Search index on the catalog table:
SELECT
    source.*,
    vs.score
FROM (
    SELECT explode(result) AS vs_result
    FROM vector_search(
        index    => 'main.ai_functions_workshop_${industry}.${config.primaryTable}_index',
        query    => 'Your query text here',
        num_results => 5
    )
) vs_raw
LATERAL VIEW json_tuple(to_json(vs_result), '${config.primaryTextColumn}', '_score') AS text_val, score
JOIN main.ai_functions_workshop_${industry}.${config.primaryTable} source ON source.${config.primaryTextColumn} = text_val
ORDER BY score DESC;`}
        />
      </WorkshopStep>
    </div>
  );
}
