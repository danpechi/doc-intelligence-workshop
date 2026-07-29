"use client";

import { useIndustry } from "@/lib/useIndustry";
import WorkshopStep from "@/components/WorkshopStep";
import CodeBlock from "@/components/CodeBlock";
import InfoBox from "@/components/InfoBox";
import { responseFormat, ddl } from "@/lib/aiResponseFormat";

const EXAMPLES: Record<string, { table: string; textCol: string; schema: string; queryStep: string }> = {
  fins: {
    table: "product_documents",
    textCol: "document_text",
    schema: '{"product_name":"string","product_type":"string","apr_low":0.0,"apr_high":0.0,"min_income_usd":0,"max_amount_usd":0}',
    queryStep: `SELECT
    product_id,
    extracted.product_type,
    extracted.apr_low,
    extracted.apr_high,
    extracted.min_income_usd
FROM extracted_products
ORDER BY extracted.apr_low`,
  },
  gaming: {
    table: "player_reports",
    textCol: "description",
    schema: '{"incident_category":"string","severity_level":"string","involves_threat":false,"recommended_action":"string"}',
    queryStep: `SELECT
    info.incident_category,
    info.severity_level,
    COUNT(*) AS report_count
FROM extracted_reports
GROUP BY info.incident_category, info.severity_level
ORDER BY report_count DESC`,
  },
  dnb: {
    table: "prospect_companies",
    textCol: "description",
    schema: '{"company_type":"string","funding_stage":"string","primary_pain_point":"string","databricks_fit_score":0}',
    queryStep: `SELECT
    company_name,
    extracted.funding_stage,
    extracted.databricks_fit_score
FROM extracted_prospects
ORDER BY extracted.databricks_fit_score DESC
LIMIT 20`,
  },
  telco: {
    table: "customer_calls",
    textCol: "transcript",
    schema: '{"issue_type":"string","customer_sentiment":"string","churn_risk":"string","resolution_achieved":false}',
    queryStep: `SELECT
    info.issue_type,
    info.churn_risk,
    COUNT(*) AS calls,
    AVG(CASE WHEN info.resolution_achieved THEN 1.0 ELSE 0.0 END) AS resolution_rate
FROM extracted_calls
GROUP BY info.issue_type, info.churn_risk`,
  },
  mfg: {
    table: "maintenance_logs",
    textCol: "technician_notes",
    schema: '{"failure_mode":"string","failure_category":"string","severity":"string","component_batch_id":"string","supplier_involved":false}',
    queryStep: `SELECT
    info.failure_category,
    info.severity,
    COUNT(*) AS events,
    AVG(downtime_hours) AS avg_downtime,
    SUM(CASE WHEN info.supplier_involved THEN 1 ELSE 0 END) AS supplier_issues
FROM extracted_logs
GROUP BY info.failure_category, info.severity`,
  },
};

export default function StructuredExtractionPage() {
  const { config, industry } = useIndustry();
  const ex = EXAMPLES[industry];
  const schema = `main.ai_functions_workshop_${industry}`;

  return (
    <div className="max-w-5xl mx-auto px-6 py-10">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <span className="text-4xl">🔍</span>
          <div>
            <h1 className="text-3xl font-bold text-white">Structured Extraction</h1>
            <p className="text-orange-400 font-mono text-sm">ai_query with responseFormat</p>
          </div>
        </div>
        <p className="text-slate-400 text-base max-w-3xl">
          Unstructured text is not directly queryable in SQL. <code className="text-orange-300">ai_query</code> with{" "}
          <code className="text-orange-300">responseFormat</code> solves this by instructing the model to return a{" "}
          <strong className="text-white">typed JSON struct</strong> — making every AI response directly filterable,
          aggregatable, and joinable.
        </p>
        <div className="mt-3 text-sm text-slate-500">
          Current industry: <span className="text-white font-semibold">{config.icon} {config.fullName}</span>
          {" "}| Schema: <code className="text-sky-400">{schema}</code>
        </div>
      </div>

      {/* Before / After */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-10 p-5 rounded-xl border border-slate-700/50"
        style={{ backgroundColor: "var(--color-navy-light)" }}>
        <div className="border border-red-500/20 rounded-lg p-4 bg-red-500/5">
          <p className="text-red-400 font-semibold text-sm mb-2">❌ Without responseFormat</p>
          <p className="text-slate-400 text-xs">Returns free-form text. Format varies per call. Cannot filter, aggregate, or join. Breaks at scale.</p>
        </div>
        <div className="border border-green-500/20 rounded-lg p-4 bg-green-500/5">
          <p className="text-green-400 font-semibold text-sm mb-2">✅ With responseFormat</p>
          <p className="text-slate-400 text-xs">Returns a typed STRUCT. Every field is queryable with standard SQL. Consistent across millions of rows.</p>
        </div>
      </div>

      <WorkshopStep number={1} title="Understand your raw data">
        <p className="text-slate-400 text-sm mb-4">
          The <code className="text-orange-300">{ex.table}</code> table contains unstructured text in the{" "}
          <code className="text-orange-300">{ex.textCol}</code> column. Our goal: make it queryable.
        </p>
        <CodeBlock
          language="sql"
          title="Preview the raw data"
          code={`USE ${schema};

SELECT *
FROM ${ex.table}
LIMIT 5;`}
        />
      </WorkshopStep>

      <WorkshopStep number={2} title="Without responseFormat — unstructured output">
        <InfoBox type="warning" title="The problem">
          Free-text AI responses vary in format, use different field names, and cannot be reliably parsed with SQL.
          Try running 100 rows and notice how the output structure differs.
        </InfoBox>
        <CodeBlock
          language="sql"
          title="ai_query without responseFormat"
          code={`SELECT
    ${ex.textCol === "document_text" ? "product_id," : ex.textCol === "description" ? "prospect_id," : ""}
    ai_query(
        'databricks-meta-llama-3-3-70b-instruct',
        CONCAT('Summarize the key details from this text: ', ${ex.textCol})
    ) AS raw_text_output  -- varies every call, not queryable
FROM ${ex.table}
LIMIT 3;`}
        />
      </WorkshopStep>

      <WorkshopStep number={3} title="With responseFormat — typed STRUCT output">
        <InfoBox type="tip" title="Use a json_schema responseFormat">
          Pass a <code>json_schema</code> string to <code>responseFormat</code> to define the output structure.
          The model returns JSON matching that schema; wrap the call in <code>from_json(...)</code> to
          get a typed STRUCT you can query field-by-field.
        </InfoBox>
        <CodeBlock
          language="sql"
          title="ai_query with responseFormat — structured extraction"
          code={`SELECT
    *,
    from_json(ai_query(
        'databricks-meta-llama-3-3-70b-instruct',
        CONCAT('Extract key details from this ${industry} record: ', ${ex.textCol}),
        responseFormat => '${responseFormat(ex.schema)}'
    ), '${ddl(ex.schema)}') AS extracted
FROM ${ex.table}
LIMIT 20;`}
        />
        <InfoBox type="success" title="What to notice">
          Each row now has a STRUCT column. Click a cell to expand it — every field has the correct type.
          You can query <code>extracted.field_name</code> directly in SQL.
        </InfoBox>
      </WorkshopStep>

      <WorkshopStep number={4} title="Query the extracted fields with SQL">
        <p className="text-slate-400 text-sm mb-4">
          Save the extracted results in a CTE or table, then query the struct fields like any other column.
        </p>
        <CodeBlock
          language="sql"
          title="Aggregate extracted fields — real analytics from unstructured data"
          code={`WITH extracted AS (
    SELECT
        *,
        from_json(ai_query(
            'databricks-meta-llama-3-3-70b-instruct',
            CONCAT('Extract key details: ', ${ex.textCol}),
            responseFormat => '${responseFormat(ex.schema)}'
        ), '${ddl(ex.schema)}') AS info
    FROM ${ex.table}
    LIMIT 100
)
${ex.queryStep};`}
        />
      </WorkshopStep>

      <WorkshopStep number={5} title="Save results to Delta Lake">
        <CodeBlock
          language="sql"
          title="Persist extracted results"
          code={`CREATE OR REPLACE TABLE ${schema}.extracted_${ex.table} AS
SELECT
    *,
    from_json(ai_query(
        'databricks-meta-llama-3-3-70b-instruct',
        CONCAT('Extract structured details: ', ${ex.textCol}),
        responseFormat => '${responseFormat(ex.schema)}'
    ), '${ddl(ex.schema)}') AS extracted,
    current_timestamp() AS ai_processed_at
FROM ${ex.table};

-- Verify
SELECT COUNT(*), COUNT(extracted) AS rows_with_extraction
FROM ${schema}.extracted_${ex.table};`}
        />
        <InfoBox type="info" title="Production tip">
          In production, wrap this in a Lakeflow Declarative Pipeline (Lab 5) so new records are processed
          incrementally rather than re-running the full table every time.
        </InfoBox>
      </WorkshopStep>
    </div>
  );
}
