"use client";

import { useIndustry } from "@/lib/useIndustry";
import WorkshopStep from "@/components/WorkshopStep";
import CodeBlock from "@/components/CodeBlock";
import InfoBox from "@/components/InfoBox";

const DOWNSTREAM_EXAMPLES: Record<string, { classify: string; extract: string; save: string }> = {
  fins: {
    classify: `ai_classify(
    CAST(ai_parse_document(content) AS STRING),
    ARRAY('secured_loan','unsecured_loan','premium_credit_card','standard_credit_card','secured_card')
) AS product_category`,
    extract: `ai_extract(
    CAST(ai_parse_document(content) AS STRING),
    ARRAY('product_name','apr_range','min_income','max_amount')
) AS terms`,
    save: `CREATE OR REPLACE TABLE main.ai_functions_workshop_fins.parsed_product_sheets AS
SELECT
    REGEXP_EXTRACT(path, '[^/]+$', 0) AS filename,
    CAST(ai_parse_document(content) AS STRING) AS raw_text,
    ai_classify(CAST(ai_parse_document(content) AS STRING), ARRAY('secured_loan','unsecured_loan','credit_card')) AS product_type,
    from_json(ai_query(
        'databricks-meta-llama-3-3-70b-instruct',
        CONCAT('Extract product details: ', CAST(ai_parse_document(content) AS STRING)),
        responseFormat => '{"type":"json_schema","json_schema":{"name":"response","schema":{"type":"object","properties":{"product_name":{"type":"string"},"apr_low":{"type":"number"},"apr_high":{"type":"number"},"min_income_usd":{"type":"integer"}}}}}'
    ), 'product_name STRING, apr_low DOUBLE, apr_high DOUBLE, min_income_usd BIGINT') AS structured,
    current_timestamp() AS processed_at
FROM read_files('/Volumes/main/ai_functions_workshop_fins/documents/', format => 'binaryFile', pathGlobFilter => '*.pdf');`,
  },
  gaming: {
    classify: `ai_classify(
    CAST(ai_parse_document(content) AS STRING),
    ARRAY('grant_appeal','deny_appeal','escalate_for_review','insufficient_evidence')
) AS appeal_decision`,
    extract: `ai_extract(
    CAST(ai_parse_document(content) AS STRING),
    ARRAY('player_id','ban_reason','account_age','supporting_evidence')
) AS appeal_fields`,
    save: `CREATE OR REPLACE TABLE main.ai_functions_workshop_gaming.parsed_appeals AS
SELECT
    REGEXP_EXTRACT(path, '[^/]+$', 0) AS filename,
    CAST(ai_parse_document(content) AS STRING) AS raw_text,
    ai_classify(CAST(ai_parse_document(content) AS STRING), ARRAY('grant_appeal','deny_appeal','escalate_for_review')) AS decision,
    from_json(ai_query(
        'databricks-meta-llama-3-3-70b-instruct',
        CONCAT('Analyze this ban appeal: ', CAST(ai_parse_document(content) AS STRING)),
        responseFormat => '{"type":"json_schema","json_schema":{"name":"response","schema":{"type":"object","properties":{"player_id":{"type":"string"},"ban_reason":{"type":"string"},"appeal_credibility":{"type":"string"},"recommended_decision":{"type":"string"}}}}}'
    ), 'player_id STRING, ban_reason STRING, appeal_credibility STRING, recommended_decision STRING') AS analysis,
    current_timestamp() AS processed_at
FROM read_files('/Volumes/main/ai_functions_workshop_gaming/documents/', format => 'binaryFile', pathGlobFilter => '*.pdf');`,
  },
  dnb: {
    classify: `ai_classify(
    CAST(ai_parse_document(content) AS STRING),
    ARRAY('hot_lead','warm_lead','cold_lead','not_qualified')
) AS lead_quality`,
    extract: `ai_extract(
    CAST(ai_parse_document(content) AS STRING),
    ARRAY('company_name','industry_sector','employee_count','primary_pain_point')
) AS company_fields`,
    save: `CREATE OR REPLACE TABLE main.ai_functions_workshop_dnb.parsed_prospects AS
SELECT
    REGEXP_EXTRACT(path, '[^/]+$', 0) AS filename,
    CAST(ai_parse_document(content) AS STRING) AS raw_text,
    ai_classify(CAST(ai_parse_document(content) AS STRING), ARRAY('hot_lead','warm_lead','cold_lead')) AS lead_quality,
    from_json(ai_query(
        'databricks-meta-llama-3-3-70b-instruct',
        CONCAT('Score this prospect for Databricks fit: ', CAST(ai_parse_document(content) AS STRING)),
        responseFormat => '{"type":"json_schema","json_schema":{"name":"response","schema":{"type":"object","properties":{"company_name":{"type":"string"},"funding_stage":{"type":"string"},"databricks_fit_score":{"type":"integer"},"recommended_outreach_angle":{"type":"string"}}}}}'
    ), 'company_name STRING, funding_stage STRING, databricks_fit_score BIGINT, recommended_outreach_angle STRING') AS icp_score,
    current_timestamp() AS processed_at
FROM read_files('/Volumes/main/ai_functions_workshop_dnb/documents/', format => 'binaryFile', pathGlobFilter => '*.pdf');`,
  },
  telco: {
    classify: `ai_classify(
    CAST(ai_parse_document(content) AS STRING),
    ARRAY('promoter','passive','detractor')
) AS nps_category`,
    extract: `ai_extract(
    CAST(ai_parse_document(content) AS STRING),
    ARRAY('customer_id','nps_score','issue_type','agent_id')
) AS survey_fields`,
    save: `CREATE OR REPLACE TABLE main.ai_functions_workshop_telco.parsed_surveys AS
SELECT
    REGEXP_EXTRACT(path, '[^/]+$', 0) AS filename,
    CAST(ai_parse_document(content) AS STRING) AS raw_text,
    ai_classify(CAST(ai_parse_document(content) AS STRING), ARRAY('promoter','passive','detractor')) AS nps_label,
    ai_classify(CAST(ai_parse_document(content) AS STRING), ARRAY('billing_issue','technical_problem','service_quality','other')) AS issue_type,
    from_json(ai_query(
        'databricks-meta-llama-3-3-70b-instruct',
        CONCAT('Analyze this customer satisfaction survey: ', CAST(ai_parse_document(content) AS STRING)),
        responseFormat => '{"type":"json_schema","json_schema":{"name":"response","schema":{"type":"object","properties":{"customer_id":{"type":"string"},"nps_score":{"type":"integer"},"follow_up_required":{"type":"boolean"},"key_verbatim_theme":{"type":"string"}}}}}'
    ), 'customer_id STRING, nps_score BIGINT, follow_up_required BOOLEAN, key_verbatim_theme STRING') AS survey_analysis,
    current_timestamp() AS processed_at
FROM read_files('/Volumes/main/ai_functions_workshop_telco/documents/', format => 'binaryFile', pathGlobFilter => '*.pdf');`,
  },
  mfg: {
    classify: `ai_classify(
    CAST(ai_parse_document(content) AS STRING),
    ARRAY('critical_stop_production','major_schedule_maintenance','minor_monitor_only','informational')
) AS severity_action`,
    extract: `ai_extract(
    CAST(ai_parse_document(content) AS STRING),
    ARRAY('component_batch_id','failure_mode','supplier_name','downtime_hours')
) AS report_fields`,
    save: `CREATE OR REPLACE TABLE main.ai_functions_workshop_mfg.parsed_inspection_reports AS
SELECT
    REGEXP_EXTRACT(path, '[^/]+$', 0) AS filename,
    CAST(ai_parse_document(content) AS STRING) AS raw_text,
    ai_classify(CAST(ai_parse_document(content) AS STRING), ARRAY('critical_stop_production','major_schedule_maintenance','minor_monitor_only')) AS severity_action,
    ai_classify(CAST(ai_parse_document(content) AS STRING), ARRAY('supplier_quality_issue','operator_error','design_defect','maintenance_gap')) AS root_cause_category,
    from_json(ai_query(
        'databricks-meta-llama-3-3-70b-instruct',
        CONCAT('Extract RCA from this inspection report: ', CAST(ai_parse_document(content) AS STRING)),
        responseFormat => '{"type":"json_schema","json_schema":{"name":"response","schema":{"type":"object","properties":{"failure_mode":{"type":"string"},"severity":{"type":"string"},"component_batch_id":{"type":"string"},"root_cause":{"type":"string"},"supplier_involved":{"type":"boolean"},"downtime_hours":{"type":"number"}}}}}'
    ), 'failure_mode STRING, severity STRING, component_batch_id STRING, root_cause STRING, supplier_involved BOOLEAN, downtime_hours DOUBLE') AS rca,
    current_timestamp() AS processed_at
FROM read_files('/Volumes/main/ai_functions_workshop_mfg/documents/', format => 'binaryFile', pathGlobFilter => '*.pdf');`,
  },
};

export default function ParseDocumentPage() {
  const { config, industry } = useIndustry();
  const schema = `main.ai_functions_workshop_${industry}`;
  const volumePath = `/Volumes/main/ai_functions_workshop_${industry}/documents`;
  const ex = DOWNSTREAM_EXAMPLES[industry];

  return (
    <div className="max-w-5xl mx-auto px-6 py-10">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <span className="text-4xl">📄</span>
          <div>
            <h1 className="text-3xl font-bold text-white">Document Parsing</h1>
            <div className="flex items-center gap-2">
              <p className="text-orange-400 font-mono text-sm">ai_parse_document</p>
              <span className="text-xs px-2 py-0.5 bg-green-500/20 text-green-400 border border-green-500/30 rounded font-semibold">
                NEW
              </span>
            </div>
          </div>
        </div>
        <p className="text-slate-400 text-base max-w-3xl">
          <code className="text-orange-300">ai_parse_document</code> bridges the gap between{" "}
          <strong className="text-white">file-based data</strong> in Unity Catalog Volumes and SQL analytics.
          It natively extracts text from PDFs, images, and Office documents — enabling all other AI Functions
          to work on content that was previously locked in files.
        </p>
        <div className="mt-3 text-sm text-slate-500">
          Industry: <span className="text-white font-semibold">{config.icon} {config.fullName}</span>
          {" "}| Documents: <span className="text-slate-300">{config.documentCount} {config.documents}</span>
        </div>
      </div>

      {/* Pipeline diagram */}
      <div
        className="rounded-xl border border-slate-700/50 p-6 mb-10"
        style={{ backgroundColor: "var(--color-navy-light)" }}
      >
        <h3 className="text-slate-300 font-semibold mb-4 text-sm">The document intelligence pipeline</h3>
        <div className="flex items-center gap-2 flex-wrap text-sm">
          {[
            { label: "Volume (PDFs)", color: "text-blue-400 bg-blue-500/10 border-blue-500/30" },
            { label: "→", color: "text-slate-500" },
            { label: "read_files(binaryFile)", color: "text-purple-400 bg-purple-500/10 border-purple-500/30" },
            { label: "→", color: "text-slate-500" },
            { label: "ai_parse_document()", color: "text-orange-400 bg-orange-500/10 border-orange-500/30" },
            { label: "→", color: "text-slate-500" },
            { label: "ai_query / ai_classify", color: "text-green-400 bg-green-500/10 border-green-500/30" },
            { label: "→", color: "text-slate-500" },
            { label: "Delta Table", color: "text-teal-400 bg-teal-500/10 border-teal-500/30" },
          ].map((step, i) =>
            step.label === "→" ? (
              <span key={i} className="text-slate-500 font-mono text-lg">{step.label}</span>
            ) : (
              <span key={i} className={`px-3 py-1.5 rounded-lg border font-mono text-xs ${step.color}`}>
                {step.label}
              </span>
            )
          )}
        </div>
      </div>

      <WorkshopStep number={1} title="Inspect documents in the volume">
        <p className="text-slate-400 text-sm mb-4">
          The setup job uploaded {config.documentCount} synthetic <strong className="text-white">{config.documents}</strong>{" "}
          to your volume. Let&apos;s verify they are accessible.
        </p>
        <CodeBlock
          language="sql"
          title="List PDF files in the volume"
          code={`SELECT
    path,
    REGEXP_EXTRACT(path, '[^/]+$', 0) AS filename,
    ROUND(length / 1024.0, 1)     AS size_kb,
    modificationTime
FROM read_files(
    '${volumePath}',
    format => 'binaryFile',
    pathGlobFilter => '*.pdf'
)
ORDER BY modificationTime DESC;`}
        />
        <InfoBox type="success" title={`Expected: ${config.documentCount} rows`}>
          You should see {config.documentCount} PDF files. If the volume is empty, return to the Setup tab
          and initialize the {config.name} dataset first.
        </InfoBox>
      </WorkshopStep>

      <WorkshopStep number={2} title="Parse document text with ai_parse_document">
        <InfoBox type="info" title="What ai_parse_document accepts">
          <ul className="list-disc list-inside space-y-1 text-xs">
            <li>PDFs — both text-based and scanned (OCR)</li>
            <li>Images — PNG, JPEG, TIFF</li>
            <li>Microsoft Office — Word (.docx), PowerPoint (.pptx)</li>
          </ul>
        </InfoBox>
        <CodeBlock
          language="sql"
          title="ai_parse_document — extract text from PDFs"
          code={`SELECT
    REGEXP_EXTRACT(path, '[^/]+$', 0) AS filename,
    CAST(ai_parse_document(content) AS STRING) AS parsed_text  -- content is the binary column from read_files
FROM read_files(
    '${volumePath}',
    format => 'binaryFile',
    pathGlobFilter => '*.pdf'
)
LIMIT 3;`}
        />
      </WorkshopStep>

      <WorkshopStep number={3} title="Chain with ai_classify — bulk document categorization">
        <p className="text-slate-400 text-sm mb-4">
          Pass the parsed text directly to <code className="text-orange-300">ai_classify</code> in a single SQL expression.
          The entire PDF catalog is classified in one query.
        </p>
        <CodeBlock
          language="sql"
          title={`Classify all ${config.name} PDFs`}
          code={`SELECT
    REGEXP_EXTRACT(path, '[^/]+$', 0) AS filename,
    ${ex.classify}
FROM read_files(
    '${volumePath}',
    format => 'binaryFile',
    pathGlobFilter => '*.pdf'
);`}
        />
      </WorkshopStep>

      <WorkshopStep number={4} title="Chain with ai_extract — pull structured fields">
        <CodeBlock
          language="sql"
          title={`Extract entities from ${config.name} PDFs`}
          code={`SELECT
    REGEXP_EXTRACT(path, '[^/]+$', 0) AS filename,
    ${ex.extract}
FROM read_files(
    '${volumePath}',
    format => 'binaryFile',
    pathGlobFilter => '*.pdf'
);`}
        />
      </WorkshopStep>

      <WorkshopStep number={5} title="Full pipeline — parse → classify → extract → save to Delta">
        <p className="text-slate-400 text-sm mb-4">
          Combine all three functions in a single <code>CREATE TABLE AS SELECT</code> to process the entire
          document catalog and persist results in Delta Lake.
        </p>
        <CodeBlock
          language="sql"
          title={`Full ${config.name} document intelligence pipeline`}
          code={ex.save}
        />
        <InfoBox type="tip" title="Performance tip">
          <code>ai_parse_document</code> is called once per row and the result is reused by both
          <code>ai_classify</code> and <code>ai_query</code> in the same SELECT. Databricks optimizes this
          automatically via common subexpression elimination.
        </InfoBox>
        <InfoBox type="info" title="Next step">
          In Lab 5 (Production Pipeline), you&apos;ll wrap this pattern in a Lakeflow Declarative Pipeline
          with Auto Loader so new PDFs added to the volume are processed automatically and incrementally.
        </InfoBox>
      </WorkshopStep>
    </div>
  );
}
