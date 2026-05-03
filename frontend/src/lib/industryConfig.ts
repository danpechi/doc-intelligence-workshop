export type IndustryKey = "fins" | "gaming" | "dnb" | "telco" | "mfg";

export interface IndustryConfig {
  key: IndustryKey;
  name: string;
  fullName: string;
  icon: string;
  tagline: string;
  color: string;
  useCase: string;
  tables: string[];
  documents: string;
  documentCount: number;
  primaryTable: string;
  primaryTextColumn: string;
  extractionSchema: string;
  classifyLabels: string[];
  extractEntities: string[];
  matchSource: string;
  matchTarget: string;
}

export const INDUSTRIES: Record<IndustryKey, IndustryConfig> = {
  fins: {
    key: "fins",
    name: "FINS",
    fullName: "Financial Services",
    icon: "🏦",
    tagline: "Merchant extraction from receipts & fuzzy merchant matching",
    color: "#1C7ED6",
    useCase:
      "Extract merchant names and transaction details from messy bank receipts, then fuzzy-match them against a canonical merchant registry — even when merchant names are abbreviated, misspelled, or truncated.",
    tables: ["merchant_transactions", "merchant_canonical", "product_documents"],
    documents: "Loan and credit card product specification sheets",
    documentCount: 5,
    primaryTable: "merchant_transactions",
    primaryTextColumn: "merchant_name_raw",
    extractionSchema:
      '{"merchant_name": "string", "merchant_category": "string", "transaction_type": "string", "is_subscription": false}',
    classifyLabels: ["low_risk", "medium_risk", "high_risk", "potential_fraud"],
    extractEntities: ["merchant_name", "transaction_amount", "currency", "merchant_category"],
    matchSource: "merchant_name_raw (transactions)",
    matchTarget: "canonical_name (merchant registry)",
  },

  gaming: {
    key: "gaming",
    name: "Gaming",
    fullName: "Gaming — Player Safety",
    icon: "🎮",
    tagline: "Safety & content moderation at scale",
    color: "#7B2FBE",
    useCase:
      "Automatically moderate player chat messages, classify ban appeal PDFs, and extract incident details from conduct reports — enabling trust & safety teams to prioritize the highest-severity cases.",
    tables: ["chat_logs", "player_reports"],
    documents: "Player ban appeal letters",
    documentCount: 20,
    primaryTable: "chat_logs",
    primaryTextColumn: "message_text",
    extractionSchema:
      '{"incident_category": "string", "severity_level": "string", "involves_threat": false, "recommended_action": "string"}',
    classifyLabels: ["safe", "offensive_language", "harassment", "hate_speech", "threat"],
    extractEntities: ["reported_player_action", "location_in_game", "evidence_type", "threat_target"],
    matchSource: "incident description (player_reports)",
    matchTarget: "policy violation definitions",
  },

  dnb: {
    key: "dnb",
    name: "DNB",
    fullName: "Digital Native Business — Prospect Analysis",
    icon: "📊",
    tagline: "AI-powered B2B prospect scoring & outreach sequencing",
    color: "#2F9E44",
    useCase:
      "Score incoming prospect company profiles against your Ideal Customer Profile (ICP), extract key firmographic signals, and generate personalized multi-touch email sequences — all from unstructured company descriptions and PDF profiles.",
    tables: ["prospect_companies", "icp_profiles"],
    documents: "Company prospect profile documents",
    documentCount: 15,
    primaryTable: "prospect_companies",
    primaryTextColumn: "description",
    extractionSchema:
      '{"company_type": "string", "employee_range": "string", "funding_stage": "string", "primary_pain_point": "string", "databricks_fit_score": 0}',
    classifyLabels: ["hot_lead", "warm_lead", "cold_lead", "not_qualified"],
    extractEntities: ["company_size", "funding_amount", "technology_platform", "pain_point", "growth_rate"],
    matchSource: "company descriptions (prospect_companies)",
    matchTarget: "ICP definitions (icp_profiles)",
  },

  telco: {
    key: "telco",
    name: "Telco",
    fullName: "Telecommunications — Call Center",
    icon: "📞",
    tagline: "Call center feedback classification & churn prediction",
    color: "#E67700",
    useCase:
      "Automatically classify call center transcripts by issue type and churn risk, extract key complaint details from customer satisfaction survey PDFs, and match calls to the right resolution playbook — reducing handle time and improving first-call resolution.",
    tables: ["customer_calls", "resolution_playbooks"],
    documents: "Customer satisfaction survey forms",
    documentCount: 25,
    primaryTable: "customer_calls",
    primaryTextColumn: "transcript",
    extractionSchema:
      '{"issue_type": "string", "customer_sentiment": "string", "churn_risk": "string", "resolution_achieved": false, "key_complaint": "string"}',
    classifyLabels: ["billing_issue", "technical_problem", "plan_change_request", "churn_risk", "positive_feedback"],
    extractEntities: ["issue_description", "customer_request", "amount_disputed", "resolution_offered"],
    matchSource: "call transcripts (customer_calls)",
    matchTarget: "resolution playbooks",
  },

  mfg: {
    key: "mfg",
    name: "MFG",
    fullName: "Manufacturing — Quality & Maintenance",
    icon: "🏭",
    tagline: "Failure mode classification & root cause extraction from inspection reports",
    color: "#C92A2A",
    useCase:
      "Process the entire backlog of historical maintenance logs and weekly inspection report PDFs to automatically classify failure modes, extract root causes, link findings back to specific component batches and suppliers — enabling proactive quality management at scale.",
    tables: ["maintenance_logs", "components"],
    documents: "Quality inspection reports & maintenance logs",
    documentCount: 30,
    primaryTable: "maintenance_logs",
    primaryTextColumn: "technician_notes",
    extractionSchema:
      '{"failure_mode": "string", "failure_category": "string", "severity": "string", "component_batch_id": "string", "root_cause": "string", "supplier_involved": false}',
    classifyLabels: ["mechanical_failure", "electrical_fault", "hydraulic_issue", "quality_defect", "operator_error"],
    extractEntities: ["component_batch_id", "supplier_name", "failure_symptom", "measurement_value", "corrective_action"],
    matchSource: "technician notes (maintenance_logs)",
    matchTarget: "failure mode definitions",
  },
};

export const INDUSTRY_KEYS = Object.keys(INDUSTRIES) as IndustryKey[];

export function getSchema(catalog: string, schemaPrefix: string, industry: IndustryKey) {
  return `${catalog}.${schemaPrefix}_${industry}`;
}

export function getVolumePath(catalog: string, schemaPrefix: string, industry: IndustryKey) {
  return `/Volumes/${catalog}/${schemaPrefix}_${industry}/documents`;
}
