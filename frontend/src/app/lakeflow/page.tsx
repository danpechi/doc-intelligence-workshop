"use client";

import { useIndustry } from "@/lib/useIndustry";
import WorkshopStep from "@/components/WorkshopStep";
import CodeBlock from "@/components/CodeBlock";
import InfoBox from "@/components/InfoBox";

const PIPELINE_CONFIGS: Record<string, { pipelineJson: string; goldQuery: string; description: string }> = {
  fins: {
    description: "Process new product documents and transactions continuously as they arrive, extracting merchant details and product terms.",
    pipelineJson: `{
  "name": "ai-functions-workshop-fins",
  "catalog": "main",
  "target": "ai_functions_workshop_fins",
  "configuration": {
    "pipeline.industry": "fins",
    "pipeline.schema_prefix": "ai_functions_workshop"
  },
  "libraries": [{ "notebook": { "path": "/path/to/notebooks/05_lakeflow_pipeline.py" } }],
  "serverless": true,
  "channel": "PREVIEW"
}`,
    goldQuery: `-- Explore the gold layer
SELECT
    filename,
    product_name,
    product_type,
    apr_low,
    apr_high,
    min_income_usd,
    processed_at
FROM main.ai_functions_workshop_fins.gold_insights
ORDER BY apr_low;`,
  },
  gaming: {
    description: "Process ban appeal PDFs continuously as players submit them, classify each appeal and surface high-priority cases.",
    pipelineJson: `{
  "name": "ai-functions-workshop-gaming",
  "catalog": "main",
  "target": "ai_functions_workshop_gaming",
  "configuration": {
    "pipeline.industry": "gaming",
    "pipeline.schema_prefix": "ai_functions_workshop"
  },
  "libraries": [{ "notebook": { "path": "/path/to/notebooks/05_lakeflow_pipeline.py" } }],
  "serverless": true,
  "channel": "PREVIEW"
}`,
    goldQuery: `-- Review classified appeals
SELECT
    filename,
    player_id,
    ban_reason,
    appeal_credibility,
    recommended_decision,
    processed_at
FROM main.ai_functions_workshop_gaming.gold_insights
ORDER BY processed_at DESC;`,
  },
  dnb: {
    description: "Score incoming prospect profile PDFs against your ICP as soon as they are uploaded by the SDR team.",
    pipelineJson: `{
  "name": "ai-functions-workshop-dnb",
  "catalog": "main",
  "target": "ai_functions_workshop_dnb",
  "configuration": {
    "pipeline.industry": "dnb",
    "pipeline.schema_prefix": "ai_functions_workshop"
  },
  "libraries": [{ "notebook": { "path": "/path/to/notebooks/05_lakeflow_pipeline.py" } }],
  "serverless": true,
  "channel": "PREVIEW"
}`,
    goldQuery: `-- Top prospects by Databricks fit score
SELECT
    filename,
    company_name,
    industry_sector,
    funding_stage,
    primary_pain_point,
    databricks_fit_score
FROM main.ai_functions_workshop_dnb.gold_insights
ORDER BY databricks_fit_score DESC
LIMIT 20;`,
  },
  telco: {
    description: "Process incoming customer satisfaction survey PDFs daily, classify NPS category, and flag detractors for immediate follow-up.",
    pipelineJson: `{
  "name": "ai-functions-workshop-telco",
  "catalog": "main",
  "target": "ai_functions_workshop_telco",
  "configuration": {
    "pipeline.industry": "telco",
    "pipeline.schema_prefix": "ai_functions_workshop"
  },
  "libraries": [{ "notebook": { "path": "/path/to/notebooks/05_lakeflow_pipeline.py" } }],
  "serverless": true,
  "channel": "PREVIEW"
}`,
    goldQuery: `-- Detractors requiring immediate follow-up
SELECT
    filename,
    customer_id,
    nps_score,
    issue_type,
    follow_up_required,
    processed_at
FROM main.ai_functions_workshop_telco.gold_insights
WHERE nps_score <= 6 OR follow_up_required = true
ORDER BY nps_score ASC;`,
  },
  mfg: {
    description: "Process the full backlog of weekly inspection report PDFs, classify severity, extract root causes, and link to component batches — enabling proactive quality management.",
    pipelineJson: `{
  "name": "ai-functions-workshop-mfg",
  "catalog": "main",
  "target": "ai_functions_workshop_mfg",
  "configuration": {
    "pipeline.industry": "mfg",
    "pipeline.schema_prefix": "ai_functions_workshop"
  },
  "libraries": [{ "notebook": { "path": "/path/to/notebooks/05_lakeflow_pipeline.py" } }],
  "serverless": true,
  "channel": "PREVIEW"
}`,
    goldQuery: `-- Critical incidents by failure mode
SELECT
    failure_mode,
    severity,
    component_batch_id,
    root_cause,
    supplier_involved,
    downtime_hours,
    processed_at
FROM main.ai_functions_workshop_mfg.gold_insights
WHERE severity = 'critical_stop_production'
ORDER BY downtime_hours DESC;`,
  },
};

export default function LakeflowPage() {
  const { config, industry } = useIndustry();
  const schema = `main.ai_functions_workshop_${industry}`;
  const pc = PIPELINE_CONFIGS[industry];

  return (
    <div className="max-w-5xl mx-auto px-6 py-10">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <span className="text-4xl">⚙️</span>
          <div>
            <h1 className="text-3xl font-bold text-white">Production Pipeline</h1>
            <p className="text-orange-400 font-mono text-sm">Lakeflow Declarative Pipelines · Auto Loader · Quality Gates</p>
          </div>
        </div>
        <p className="text-slate-400 text-base max-w-3xl">
          The previous labs showed AI Functions interactively. This lab productionizes the same patterns
          using <strong className="text-white">Lakeflow Declarative Pipelines</strong> — a declarative
          framework for incremental, self-healing, quality-gated data pipelines.
        </p>
        <div className="mt-3 text-sm text-slate-500">
          Industry: <span className="text-white font-semibold">{config.icon} {config.fullName}</span>
        </div>
      </div>

      {/* Architecture */}
      <div
        className="rounded-xl border border-slate-700/50 p-6 mb-10"
        style={{ backgroundColor: "var(--color-navy-light)" }}
      >
        <h3 className="text-slate-300 font-semibold mb-4">Medallion architecture with AI Functions</h3>
        <p className="text-slate-400 text-sm mb-5">{pc.description}</p>
        <div className="space-y-2">
          {[
            { layer: "Bronze", color: "text-amber-700 bg-amber-700/10 border-amber-700/30", desc: "Raw file bytes + metadata ingested via Auto Loader (cloudFiles). Schema-on-read, append-only." },
            { layer: "Silver — Parsed", color: "text-sky-400 bg-sky-500/10 border-sky-500/30", desc: "ai_parse_document() applied to extract text. One row per source document." },
            { layer: "Silver — Enriched", color: "text-blue-400 bg-blue-500/10 border-blue-500/30", desc: "ai_query() + ai_classify() applied to parsed text. CONSTRAINT filters drop bad AI outputs." },
            { layer: "Gold — Insights", color: "text-yellow-400 bg-yellow-500/10 border-yellow-500/30", desc: "Quality-gated, deduped, analytics-ready results. Joins, aggregations, and downstream consumption." },
          ].map((row) => (
            <div key={row.layer} className="flex items-start gap-3">
              <span className={`flex-shrink-0 px-2 py-0.5 rounded text-xs font-mono font-bold border ${row.color}`}>
                {row.layer}
              </span>
              <p className="text-slate-400 text-xs leading-relaxed">{row.desc}</p>
            </div>
          ))}
        </div>
      </div>

      <WorkshopStep number={1} title="Review the pipeline notebook">
        <p className="text-slate-400 text-sm mb-4">
          The pipeline is defined in <code className="text-orange-300">notebooks/05_lakeflow_pipeline.py</code>.
          It uses <code>@dlt.table</code> decorators to declare each layer — no imperative scheduling code.
        </p>
        <InfoBox type="info" title="Key patterns in the pipeline notebook">
          <ul className="list-disc list-inside space-y-1 text-xs">
            <li><strong>Auto Loader:</strong> <code>spark.readStream.format(&quot;cloudFiles&quot;)</code> for incremental file ingestion</li>
            <li><strong>Streaming tables:</strong> Bronze and Silver layers process new files automatically</li>
            <li><strong>Quality constraints:</strong> <code>@dlt.expect_or_drop()</code> filters bad AI outputs before Gold</li>
            <li><strong>Batch Gold:</strong> Final layer is a regular (non-streaming) table for easy querying</li>
          </ul>
        </InfoBox>
        <CodeBlock
          language="python"
          title="Bronze layer — Auto Loader"
          filename="notebooks/05_lakeflow_pipeline.py (excerpt)"
          code={`@dlt.table(
    name="bronze_documents",
    comment="Raw document bytes ingested via Auto Loader",
)
def bronze_documents():
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "binaryFile")
        .option("pathGlobFilter", "*.pdf")
        .load(volume_path)
        .select("path", "content", "length", "modificationTime", ...)
    )`}
        />
        <CodeBlock
          language="python"
          title="Silver — parse + enrich with quality gate"
          filename="notebooks/05_lakeflow_pipeline.py (excerpt)"
          code={`@dlt.table(name="silver_enriched")
@dlt.expect("has_failure_mode", "extracted.failure_mode IS NOT NULL")
@dlt.expect_or_drop("valid_downtime", "extracted.downtime_hours >= 0")
def silver_enriched_mfg():
    return dlt.read_stream("silver_parsed").selectExpr(
        "path", "filename", "parsed_at",
        """from_json(ai_query(
            'databricks-meta-llama-3-3-70b-instruct',
            CONCAT('Extract RCA from: ', parsed_text),
            responseFormat => '{"type":"json_schema","json_schema":{"name":"response","schema":{"type":"object","properties":{"failure_mode":{"type":"string"},"severity":{"type":"string"},"downtime_hours":{"type":"number"}}}}}'
        ), 'failure_mode STRING, severity STRING, downtime_hours DOUBLE') AS extracted""",
        "ai_classify(parsed_text, ARRAY('critical','major','minor')) AS severity_action",
    )`}
        />
      </WorkshopStep>

      <WorkshopStep number={2} title="Create the Lakeflow pipeline">
        <p className="text-slate-400 text-sm mb-4">
          Create the pipeline via the Databricks UI, CLI, or via the DAB bundle.
          The pipeline configuration passes the industry as a Spark configuration variable.
        </p>
        <CodeBlock
          language="json"
          title="Pipeline configuration (UI or API)"
          code={pc.pipelineJson}
        />
        <InfoBox type="warning" title="PREVIEW channel required">
          <code>ai_parse_document</code> requires the <code>&quot;channel&quot;: &quot;PREVIEW&quot;</code> setting in the pipeline
          configuration, as it is a preview-stage AI Function.
        </InfoBox>
      </WorkshopStep>

      <WorkshopStep number={3} title="Run and monitor the pipeline">
        <CodeBlock
          language="bash"
          title="Trigger via CLI or DAB"
          code={`# Via Databricks CLI
databricks pipelines start --pipeline-id <pipeline_id>

# Via DAB bundle run
databricks bundle run -e dev setup_job --var industry=${industry}

# Check status
databricks pipelines get --pipeline-id <pipeline_id>`}
        />
        <InfoBox type="tip" title="What to watch in the UI">
          The pipeline graph shows each table layer with:
          <ul className="list-disc list-inside space-y-1 mt-1 text-xs">
            <li>Record counts processed per run</li>
            <li>Quality constraint pass/fail rates (look for CONSTRAINT violations)</li>
            <li>Processing time per layer</li>
          </ul>
        </InfoBox>
      </WorkshopStep>

      <WorkshopStep number={4} title="Query the Gold layer results">
        <p className="text-slate-400 text-sm mb-4">
          Once the pipeline has run, the Gold table contains clean, structured, AI-enriched data
          ready for analytics and downstream ML.
        </p>
        <CodeBlock
          language="sql"
          title={`Query Gold insights — ${config.fullName}`}
          code={pc.goldQuery}
        />
      </WorkshopStep>

      <WorkshopStep number={5} title="Schedule for production">
        <CodeBlock
          language="yaml"
          title="Add a scheduled trigger in databricks.yml"
          code={`resources:
  pipelines:
    ${industry}_pipeline:
      name: "AI Functions Workshop - ${config.name}"
      catalog: main
      target: ai_functions_workshop_${industry}
      serverless: true
      channel: PREVIEW
      configuration:
        pipeline.industry: ${industry}
        pipeline.schema_prefix: ai_functions_workshop
      libraries:
        - notebook:
            path: ./notebooks/05_lakeflow_pipeline.py
      # Trigger daily at 6 AM UTC
      trigger:
        cron:
          quartz_cron_expression: "0 0 6 * * ?"
          timezone_id: "UTC"`}
        />
        <InfoBox type="success" title="You've completed the workshop!">
          You now know how to apply all major Databricks AI Functions end-to-end:
          <br />🔍 <code>ai_query</code> → structured extraction from any text
          <br />🏷️ <code>ai_classify / ai_extract</code> → zero-shot labeling at scale
          <br />📄 <code>ai_parse_document</code> → bridge files to SQL
          <br />🔗 <code>ai_similarity</code> → semantic fuzzy matching
          <br />⚙️ Lakeflow Declarative Pipelines → production-grade orchestration
        </InfoBox>
      </WorkshopStep>
    </div>
  );
}
