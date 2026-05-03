"use client";

import { useIndustry } from "@/lib/useIndustry";
import WorkshopStep from "@/components/WorkshopStep";
import CodeBlock from "@/components/CodeBlock";
import InfoBox from "@/components/InfoBox";

export default function ClassificationPage() {
  const { config, industry } = useIndustry();
  const schema = `main.ai_functions_workshop_${industry}`;
  const table = config.primaryTable;
  const textCol = config.primaryTextColumn;
  const labels = config.classifyLabels.map(l => `'${l}'`).join(", ");
  const entities = config.extractEntities.map(e => `'${e}'`).join(", ");

  const accuracyExample: Record<string, string> = {
    gaming: `-- gaming: compare ai_classify vs ground truth label
WITH classified AS (
    SELECT message_id, expected_label,
           ai_classify(message_text, ARRAY('safe','offensive_language','harassment','hate_speech','threat')) AS ai_label
    FROM chat_logs LIMIT 100
)
SELECT
    expected_label,
    ai_label,
    COUNT(*) AS count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY expected_label), 1) AS pct
FROM classified
GROUP BY expected_label, ai_label
ORDER BY expected_label, count DESC;`,
    mfg: `-- mfg: compare ai severity vs original severity
WITH classified AS (
    SELECT log_id, severity AS ground_truth,
           ai_classify(technician_notes, ARRAY('critical','major','minor')) AS ai_severity
    FROM maintenance_logs LIMIT 100
)
SELECT ground_truth, ai_severity, COUNT(*) AS count
FROM classified GROUP BY ground_truth, ai_severity ORDER BY ground_truth;`,
    telco: `-- telco: compare ai issue type vs recorded issue_type
WITH classified AS (
    SELECT call_id, issue_type AS ground_truth,
           ai_classify(transcript, ARRAY('billing_issue','technical_problem','churn_risk','plan_change_request','other')) AS ai_type
    FROM customer_calls LIMIT 100
)
SELECT ground_truth, ai_type, COUNT(*) AS count
FROM classified GROUP BY ground_truth, ai_type ORDER BY ground_truth;`,
    fins: `-- fins: check classification consistency on product_documents
SELECT
    product_id, product_name,
    ai_classify(document_text, ARRAY('secured_loan','unsecured_loan','premium_credit_card','standard_credit_card')) AS product_type
FROM product_documents;`,
    dnb: `-- dnb: lead quality across funding stages
WITH classified AS (
    SELECT funding_stage,
           ai_classify(description, ARRAY('hot_lead','warm_lead','cold_lead','not_qualified')) AS lead_quality
    FROM prospect_companies LIMIT 100
)
SELECT funding_stage, lead_quality, COUNT(*) AS count
FROM classified
GROUP BY funding_stage, lead_quality
ORDER BY funding_stage, count DESC;`,
  };

  const combineExample: Record<string, string> = {
    gaming: `SELECT
    message_id, message_text,
    ai_classify(message_text, ARRAY('safe', 'warning', 'violation', 'ban_worthy')) AS severity,
    ai_extract(message_text, ARRAY('target_player', 'offensive_term', 'threat_type')) AS entities
FROM chat_logs
WHERE expected_label != 'safe'
LIMIT 30;`,
    mfg: `SELECT
    log_id, line_id, downtime_hours,
    ai_classify(technician_notes, ARRAY('mechanical_failure','electrical_fault','hydraulic_issue','quality_defect')) AS failure_category,
    ai_classify(technician_notes, ARRAY('critical','major','minor')) AS ai_severity,
    ai_extract(technician_notes, ARRAY('component_batch_id','supplier_name','root_cause')) AS entities
FROM maintenance_logs
LIMIT 30;`,
    telco: `SELECT
    call_id, agent_id,
    ai_classify(transcript, ARRAY('billing_issue','technical_problem','churn_risk','plan_change_request','other')) AS call_type,
    ai_classify(transcript, ARRAY('high_churn_risk','low_churn_risk','no_churn_risk')) AS churn_risk,
    ai_extract(transcript, ARRAY('disputed_amount','service_name','resolution_timeline')) AS key_entities
FROM customer_calls
LIMIT 30;`,
    dnb: `SELECT
    prospect_id, company_name,
    ai_classify(description, ARRAY('hot_lead','warm_lead','cold_lead')) AS lead_quality,
    ai_extract(description, ARRAY('annual_revenue','headcount','growth_rate','primary_tool')) AS biz_entities
FROM prospect_companies
LIMIT 30;`,
    fins: `SELECT
    product_id, product_name,
    ai_classify(document_text, ARRAY('secured_loan','unsecured_loan','premium_credit_card','standard_credit_card')) AS product_type,
    ai_extract(document_text, ARRAY('minimum_income','maximum_amount','apr_range','loan_term')) AS terms
FROM product_documents;`,
  };

  return (
    <div className="max-w-5xl mx-auto px-6 py-10">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <span className="text-4xl">🏷️</span>
          <div>
            <h1 className="text-3xl font-bold text-white">Classification & Extraction</h1>
            <p className="text-orange-400 font-mono text-sm">ai_classify · ai_extract</p>
          </div>
        </div>
        <p className="text-slate-400 text-base max-w-3xl">
          Purpose-built functions for high-volume classification and entity extraction.
          No prompt engineering — just provide your label set or entity list and apply across any table.
        </p>
        <div className="mt-3 text-sm text-slate-500">
          Industry: <span className="text-white font-semibold">{config.icon} {config.fullName}</span>
          {" "}| Table: <code className="text-sky-400">{schema}.{table}</code>
        </div>
      </div>

      {/* Function comparison */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-10">
        {[
          {
            fn: "ai_classify(content, ARRAY(...))",
            when: "You know the label set in advance",
            returns: "One label from your array — the best match",
            example: `ai_classify(transcript, ARRAY('billing_issue', 'churn_risk', 'technical'))`,
            color: "blue",
          },
          {
            fn: "ai_extract(content, ARRAY(...))",
            when: "You need named entities from text",
            returns: "A STRUCT with one field per entity name",
            example: `ai_extract(notes, ARRAY('batch_id', 'supplier', 'root_cause'))`,
            color: "purple",
          },
        ].map((item) => (
          <div
            key={item.fn}
            className="p-5 rounded-xl border border-slate-700/50"
            style={{ backgroundColor: "var(--color-navy-light)" }}
          >
            <p className={`font-mono text-sm font-bold mb-2 text-${item.color}-400`}>{item.fn}</p>
            <p className="text-slate-400 text-xs mb-1"><span className="text-slate-300">Use when:</span> {item.when}</p>
            <p className="text-slate-400 text-xs mb-3"><span className="text-slate-300">Returns:</span> {item.returns}</p>
            <code className="text-xs text-slate-400 font-mono bg-slate-800 block p-2 rounded">{item.example}</code>
          </div>
        ))}
      </div>

      <WorkshopStep number={1} title={`ai_classify — ${config.fullName} use case`}>
        <InfoBox type="info" title="Zero-shot classification">
          No fine-tuning, no training data. Just define your label set and the model infers the best match
          from context. Labels should be mutually exclusive and cover all cases.
        </InfoBox>
        <CodeBlock
          language="sql"
          title={`Classify ${table} — ${config.fullName}`}
          code={`SELECT
    *,
    ai_classify(
        ${textCol},
        ARRAY(${labels})
    ) AS ai_label
FROM ${table}
LIMIT 50;`}
        />
      </WorkshopStep>

      <WorkshopStep number={2} title="Validate against ground truth labels">
        <p className="text-slate-400 text-sm mb-4">
          Where your dataset has existing labels, compare them to the AI classification to measure accuracy.
        </p>
        <CodeBlock
          language="sql"
          title="Accuracy check — AI vs ground truth"
          code={accuracyExample[industry]}
        />
        <InfoBox type="tip" title="Expected accuracy">
          For well-defined, mutually exclusive label sets on clear text, expect 75-90% agreement with
          human labels. For ambiguous categories, expect lower — and consider refining your label definitions.
        </InfoBox>
      </WorkshopStep>

      <WorkshopStep number={3} title="ai_extract — pull named entities">
        <CodeBlock
          language="sql"
          title={`Extract entities from ${table}`}
          code={`SELECT
    *,
    ai_extract(
        ${textCol},
        ARRAY(${entities})
    ) AS entities
FROM ${table}
LIMIT 20;

-- Access individual fields
-- entities.${config.extractEntities[0]}
-- entities.${config.extractEntities[1]}`}
        />
        <InfoBox type="info" title="Missing entities">
          If an entity is not present in the text, its field returns <code>NULL</code>.
          Use <code>COALESCE</code> or <code>IS NOT NULL</code> filters as needed.
        </InfoBox>
      </WorkshopStep>

      <WorkshopStep number={4} title="Combine classify + extract in one pass">
        <p className="text-slate-400 text-sm mb-4">
          Both functions read the same column — combine them to enrich records in a single SQL statement
          without hitting the model twice unnecessarily.
        </p>
        <CodeBlock
          language="sql"
          title="classify + extract combined"
          code={combineExample[industry]}
        />
      </WorkshopStep>

      <WorkshopStep number={5} title="Aggregate classified results for reporting">
        <CodeBlock
          language="sql"
          title="Analytics on AI-classified data"
          code={`WITH enriched AS (
    SELECT
        *,
        ai_classify(${textCol}, ARRAY(${labels})) AS label
    FROM ${table}
    LIMIT 200
)
SELECT
    label,
    COUNT(*)                                               AS record_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1)   AS pct_of_total
FROM enriched
GROUP BY label
ORDER BY record_count DESC;`}
        />
      </WorkshopStep>
    </div>
  );
}
