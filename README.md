# Databricks AI Functions Workshop

Learn to apply AI at scale directly in SQL — no Python, no MLflow, no cluster setup. Pick your industry, initialize the dataset, then work through each lab.

---

## What You'll Learn

| Function | Description |
|---|---|
| `ai_query` | Extract typed structs from any unstructured text using LLMs with `responseFormat` |
| `ai_classify` / `ai_extract` | Zero-shot classification and named entity extraction without prompt engineering |
| `ai_parse_document` | Parse PDFs, images, and Office files from UC Volumes directly in SQL |
| `ai_similarity` | Score pairwise semantic similarity for fuzzy matching and deduplication |
| `vector_search()` | Find top-K semantically similar records from large Delta tables at millisecond latency |
| Lakeflow Pipelines | Productionize all of the above with Auto Loader, quality gates, and incremental processing |

---

## Industry Verticals

Each industry uses a different dataset and real-world use case. The same AI Functions apply across all of them.

### Financial Services (FINS)
**Merchant extraction from receipts & fuzzy merchant matching**

Extract merchant names and transaction details from messy bank receipts, then fuzzy-match them against a canonical merchant registry — even when merchant names are abbreviated, misspelled, or truncated.

- Tables: `merchant_transactions`, `merchant_canonical`, `product_documents`
- Documents: Loan and credit card product specification sheets (5 PDFs)

### Gaming — Player Safety
**Safety & content moderation at scale**

Automatically moderate player chat messages, classify ban appeal PDFs, and extract incident details from conduct reports — enabling trust & safety teams to prioritize the highest-severity cases.

- Tables: `chat_logs`, `player_reports`
- Documents: Player ban appeal letters (20 PDFs)

### Digital Native Business — Prospect Analysis (DNB)
**AI-powered B2B prospect scoring & outreach sequencing**

Score incoming prospect company profiles against your Ideal Customer Profile (ICP), extract key firmographic signals, and generate personalized multi-touch email sequences — all from unstructured company descriptions and PDF profiles.

- Tables: `prospect_companies`, `icp_profiles`
- Documents: Company prospect profile documents (15 PDFs)

### Telecommunications — Call Center (Telco)
**Call center feedback classification & churn prediction**

Automatically classify call center transcripts by issue type and churn risk, extract key complaint details from customer satisfaction survey PDFs, and match calls to the right resolution playbook — reducing handle time and improving first-call resolution.

- Tables: `customer_calls`, `resolution_playbooks`
- Documents: Customer satisfaction survey forms (25 PDFs)

### Manufacturing — Quality & Maintenance (MFG)
**Failure mode classification & root cause extraction from inspection reports**

Process the entire backlog of historical maintenance logs and weekly inspection report PDFs to automatically classify failure modes, extract root causes, link findings back to specific component batches and suppliers — enabling proactive quality management at scale.

- Tables: `maintenance_logs`, `components`
- Documents: Quality inspection reports & maintenance logs (30 PDFs)

---

## Workshop Labs

| Lab | Topic | Key Functions |
|-----|-------|---------------|
| 1 | Structured Extraction | `ai_query` with `responseFormat` |
| 2 | Classification & Entity Extraction | `ai_classify`, `ai_extract` |
| 3 | Document Parsing | `ai_parse_document` |
| 4 | Fuzzy Matching & Similarity | `ai_similarity`, `vector_search()` |
| 5 | Production Pipelines | Lakeflow Declarative Pipelines |

---

## Prerequisites

- Databricks workspace with Unity Catalog enabled
- Serverless SQL warehouse
- `CREATE SCHEMA`, `CREATE TABLE`, `CREATE VOLUME` privileges on the target catalog

---

## Setup

### Option 1 — App UI (recommended)

Deploy the Databricks App, select your industry, and click **Initialize Dataset** from the Setup tab. The app triggers the DAB job and polls for completion.

### Option 2 — CLI

```bash
# One-time: deploy the bundle
databricks bundle deploy -e dev

# Initialize a specific industry dataset
databricks bundle run setup_job --var industry=fins -e dev
```

Replace `fins` with `gaming`, `dnb`, `telco`, or `mfg`.

What gets created per industry:

- Schema: `main.ai_functions_workshop_{industry}`
- Tables with synthetic data (varies by industry)
- Volume: `/Volumes/main/ai_functions_workshop_{industry}/documents/`
- Synthetic PDFs for `ai_parse_document` labs

---

## Project Structure

```
.
├── databricks.yml              # DAB config: setup job + cleanup job + app resource
├── app.py                      # FastAPI backend (serves frontend + /api/setup endpoints)
├── requirements.txt            # App dependencies
├── setup/
│   ├── 00_setup_catalog.py    # Creates catalog, schema, volume
│   ├── 01_generate_data.py    # Generates synthetic Delta tables per industry
│   ├── 02_generate_pdfs.py    # Generates synthetic PDFs and uploads to volume
│   └── 99_cleanup.py          # Drops schema and volume
├── notebooks/
│   ├── 01_structured_extraction.py
│   ├── 02_classification.py
│   ├── 03_parse_document.py
│   ├── 04_fuzzy_matching.py
│   └── 05_lakeflow_pipeline.py
└── frontend/                   # Next.js 15 static app (Tailwind CSS)
    └── src/app/
        ├── page.tsx                        # Setup tab (industry selector + job trigger)
        ├── structured-extraction/page.tsx  # Lab 1
        ├── classification/page.tsx         # Lab 2
        ├── parse-document/page.tsx         # Lab 3
        ├── fuzzy-matching/page.tsx         # Lab 4
        └── lakeflow/page.tsx               # Lab 5
```

---

## Deploying the App

```bash
# Build the frontend (requires node_modules symlink if npm registry is blocked)
ln -sf /path/to/another-project/frontend/node_modules frontend/node_modules
cd frontend && ./node_modules/.bin/next build
cd ..

# Deploy everything
databricks bundle deploy -e dev
```

The app is served at the URL shown in the Databricks Apps UI after deployment.

---

## Cleanup

```bash
databricks bundle run cleanup_job -e dev
```

This drops the schema and all associated tables and volumes for the workshop.
