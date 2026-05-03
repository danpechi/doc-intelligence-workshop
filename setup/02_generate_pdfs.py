# Databricks notebook source
# MAGIC %md
# MAGIC # Setup: Generate Synthetic PDFs
# MAGIC
# MAGIC Creates realistic industry-specific PDF documents and uploads them to the Unity Catalog Volume.
# MAGIC These documents are used in the **ai_parse_document** section of the workshop.
# MAGIC
# MAGIC **Volume path:** `/Volumes/{catalog}/{schema}/documents/`

# COMMAND ----------

dbutils.widgets.text("catalog", "main")
dbutils.widgets.text("schema_prefix", "ai_functions_workshop")
dbutils.widgets.text("industry", "fins")

catalog = dbutils.widgets.get("catalog")
schema_prefix = dbutils.widgets.get("schema_prefix")
industry = dbutils.widgets.get("industry").lower().strip()
schema = f"{schema_prefix}_{industry}"
volume_path = f"/Volumes/{catalog}/{schema}/documents"

print(f"Uploading PDFs to: {volume_path}")

# COMMAND ----------

# MAGIC %pip install reportlab faker --quiet

# COMMAND ----------

import os
import random
from io import BytesIO
from datetime import datetime, timedelta

from faker import Faker
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

fake = Faker()
random.seed(99)
Faker.seed(99)

styles = getSampleStyleSheet()

# ---------------------------------------------------------------------------
# Helper: build a PDF and write to volume
# ---------------------------------------------------------------------------

def make_doc(filename: str, content_fn) -> str:
    """Create a PDF using content_fn(doc, story) and save to volume."""
    path = os.path.join(volume_path, filename)
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter,
                             rightMargin=72, leftMargin=72,
                             topMargin=72, bottomMargin=72)
    story = []
    content_fn(doc, story)
    doc.build(story)
    with open(path, "wb") as f:
        f.write(buf.getvalue())
    return path

h1 = ParagraphStyle("h1", parent=styles["Heading1"], fontSize=16, spaceAfter=12)
h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=13, spaceAfter=8)
body = ParagraphStyle("body", parent=styles["Normal"], fontSize=10, leading=14, spaceAfter=6)
small = ParagraphStyle("small", parent=styles["Normal"], fontSize=8, leading=12, textColor=colors.grey)

# ===========================================================================
# FINS – Loan & Credit Card Product Sheets
# ===========================================================================

def make_fins_product_pdf(product_id, product_name, product_type, apr_low, apr_high,
                           min_income, max_amount, term_range, highlights):
    def build(doc, story):
        story.append(Paragraph("BCP Financial Services", h1))
        story.append(Paragraph(f"Product Sheet: {product_name}", h2))
        story.append(Paragraph(f"Product ID: {product_id}  |  Type: {product_type}  |  Effective: {datetime.today().strftime('%B %Y')}", small))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.navy))
        story.append(Spacer(1, 12))
        story.append(Paragraph("Key Terms & Conditions", h2))
        data = [
            ["Field", "Details"],
            ["Annual Percentage Rate (APR)", f"{apr_low}% – {apr_high}%"],
            ["Minimum Annual Income", f"${min_income:,}"],
            ["Maximum Amount", f"${max_amount:,}"],
            ["Loan / Credit Term", term_range],
            ["Application Processing", "24 – 48 business hours"],
            ["Early Repayment Penalty", "None"],
        ]
        t = Table(data, colWidths=[2.5*inch, 3.5*inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.navy),
            ("TEXTCOLOR",  (0,0), (-1,0), colors.white),
            ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
            ("GRID",       (0,0), (-1,-1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.whitesmoke, colors.white]),
        ]))
        story.append(t)
        story.append(Spacer(1, 18))
        story.append(Paragraph("Product Highlights", h2))
        for h in highlights:
            story.append(Paragraph(f"• {h}", body))
        story.append(Spacer(1, 18))
        story.append(Paragraph("Eligibility Requirements", h2))
        story.append(Paragraph(
            f"Applicants must be 18+ years of age, a legal resident, with a minimum credit score of 620. "
            f"Minimum annual income of ${min_income:,} required. Employment verification may be requested. "
            f"BCP reserves the right to request additional documentation.", body))
        story.append(Spacer(1, 12))
        story.append(Paragraph("Disclaimer", small))
        story.append(Paragraph(
            "Rates shown are representative and subject to creditworthiness assessment. "
            "This document is for informational purposes only and does not constitute a binding offer.", small))
    return build

fins_products = [
    ("LOAN001", "Personal Loan – Standard", "Unsecured Loan", 8.99, 24.99, 25000, 50000, "12–60 months",
     ["No collateral required", "Same-day pre-approval", "Flexible repayment schedule", "Suitable for debt consolidation"]),
    ("LOAN002", "Home Improvement Loan", "Secured Loan", 6.49, 18.99, 40000, 150000, "24–120 months",
     ["Secured against property", "Ideal for major renovations", "Interest may be tax deductible", "Fixed and variable rate options"]),
    ("LOAN003", "Auto Loan", "Secured Loan", 4.99, 14.99, 20000, 75000, "24–84 months",
     ["New and used vehicles", "No prepayment penalty", "GAP insurance option available", "Dealer partnership network"]),
    ("CC001", "Cashback Platinum Card", "Credit Card", 17.99, 26.99, 35000, 25000, "Revolving",
     ["2% cashback on all purchases", "5% on groceries and gas", "$200 sign-up bonus", "No foreign transaction fees"]),
    ("CC002", "Travel Rewards Elite", "Premium Credit Card", 19.99, 28.99, 60000, 50000, "Revolving",
     ["3x points on travel and dining", "$300 annual travel credit", "Airport lounge access", "Trip delay and cancellation insurance"]),
]

# ===========================================================================
# Gaming – Ban Appeal Letters
# ===========================================================================

appeal_reasons = [
    ("account sharing", "I lent my account to my younger brother over the weekend without realizing it violated the terms."),
    ("false positive", "I believe the anti-cheat system flagged me incorrectly. I only use approved peripherals and software."),
    ("VPN usage", "I was using a VPN to reduce latency while traveling abroad. I was unaware this triggers a ban."),
    ("heated moment", "I said something inappropriate in chat during a very frustrating match. I deeply regret it and it won't happen again."),
    ("unauthorized software", "I had a third-party overlay application that was flagged. I have since uninstalled it completely."),
]

def make_gaming_appeal(i):
    player_id = f"PLR{random.randint(10000,99999)}"
    reason_type, explanation = random.choice(appeal_reasons)
    ban_date = (datetime.today() - timedelta(days=random.randint(1,30))).strftime("%Y-%m-%d")
    account_age_years = random.randint(1, 8)
    rank = random.choice(["Bronze II", "Silver III", "Gold I", "Platinum IV", "Diamond II", "Master"])

    def build(doc, story):
        story.append(Paragraph("PLAYER BAN APPEAL", h1))
        story.append(Paragraph(f"Reference: APPEAL-{i+1:04d}  |  Submitted: {datetime.today().strftime('%Y-%m-%d')}", small))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.darkred))
        story.append(Spacer(1, 12))
        story.append(Paragraph("Account Information", h2))
        data = [
            ["Player ID", player_id],
            ["Current Rank", rank],
            ["Account Age", f"{account_age_years} years"],
            ["Ban Date", ban_date],
            ["Ban Reason on Record", reason_type.title()],
        ]
        t = Table(data, colWidths=[2.5*inch, 3.5*inch])
        t.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
            ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0,0), (-1,-1), [colors.lightyellow, colors.white]),
        ]))
        story.append(t)
        story.append(Spacer(1, 16))
        story.append(Paragraph("Statement of Appeal", h2))
        story.append(Paragraph(
            f"I am writing to formally appeal the ban applied to my account on {ban_date}. "
            f"I have been a member of this gaming community for {account_age_years} years and have always strived "
            f"to maintain a positive and fair play environment. {explanation} "
            f"I understand and respect the rules of the platform and I assure you this will not occur again. "
            f"I kindly request a review of my case and reinstatement of my account.", body))
        story.append(Spacer(1, 12))
        story.append(Paragraph("Supporting Evidence", h2))
        story.append(Paragraph("• No prior bans or warnings on this account.", body))
        story.append(Paragraph(f"• {random.randint(500,3000)} hours of gameplay on record.", body))
        story.append(Paragraph(f"• {random.randint(10,200)} positive commendations from other players.", body))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"Signed: {player_id}  |  Date: {datetime.today().strftime('%Y-%m-%d')}", small))
    return build

# ===========================================================================
# DNB – Company Prospect Profiles
# ===========================================================================

def make_dnb_prospect(i):
    company = fake.company()
    employees = random.choice([30, 75, 200, 500, 1200, 3000])
    funding = random.choice(["Seed", "Series A", "Series B", "Series C", "Public"])
    tech = random.choice(["AWS + Redshift", "GCP + BigQuery", "Azure + Synapse", "Snowflake + dbt", "On-prem SQL Server"])
    pain = random.choice([
        "Data scattered across 12 disconnected tools",
        "Manual weekly reporting takes 3 analysts 2 full days",
        "Cannot predict customer churn in real time",
        "ML models take 6+ months from idea to production",
        "No unified customer 360 view across channels",
    ])
    yoy_growth = random.randint(15, 120)
    industry_sector = random.choice(["FinTech", "HealthTech", "E-commerce", "Logistics", "SaaS", "EdTech"])

    def build(doc, story):
        story.append(Paragraph(f"COMPANY PROFILE: {company.upper()}", h1))
        story.append(Paragraph(f"Prospect ID: PROS{i+1:04d}  |  Generated: {datetime.today().strftime('%Y-%m-%d')}", small))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.darkblue))
        story.append(Spacer(1, 12))
        story.append(Paragraph("Company Overview", h2))
        story.append(Paragraph(
            f"{company} is a {industry_sector} company headquartered in {fake.city()}, {fake.country()}. "
            f"Founded in {random.randint(2012,2021)}, the company has grown to {employees} employees "
            f"with year-over-year revenue growth of {yoy_growth}%. Currently at {funding} stage.", body))
        story.append(Spacer(1, 10))
        story.append(Paragraph("Technology Stack", h2))
        story.append(Paragraph(f"Current infrastructure: {tech}. The data team consists of {random.randint(2,20)} engineers "
                               f"and {random.randint(1,8)} analysts.", body))
        story.append(Spacer(1, 10))
        story.append(Paragraph("Primary Business Challenge", h2))
        story.append(Paragraph(pain, body))
        story.append(Spacer(1, 10))
        story.append(Paragraph("Engagement Signals", h2))
        story.append(Paragraph(f"• Attended Databricks Summit in {random.choice([2023,2024,2025])}", body))
        story.append(Paragraph(f"• Downloaded {random.randint(1,5)} whitepapers on data lakehouse architecture", body))
        story.append(Paragraph(f"• {fake.name()}, Head of Data, active on LinkedIn discussing modern data stack", body))
        story.append(Spacer(1, 12))
        story.append(Paragraph("Recommended Outreach", h2))
        story.append(Paragraph(
            f"Lead with the data lakehouse value proposition. Reference their {tech.split('+')[0].strip()} investment. "
            f"Focus on time-to-insight reduction and ML deployment velocity.", body))
    return build

# ===========================================================================
# Telco – Customer Satisfaction Surveys
# ===========================================================================

def make_telco_survey(i):
    customer_id = f"CUST{random.randint(100000,999999)}"
    call_date = (datetime.today() - timedelta(days=random.randint(1,14))).strftime("%Y-%m-%d")
    issue = random.choice(["billing dispute", "network outage", "plan upgrade", "roaming charges", "device support"])
    nps = random.randint(0, 10)
    sentiment = "promoter" if nps >= 9 else ("passive" if nps >= 7 else "detractor")
    agent = f"AGT{random.randint(100,999)}"

    def build(doc, story):
        story.append(Paragraph("CUSTOMER SATISFACTION SURVEY", h1))
        story.append(Paragraph(f"Survey ID: SURV-{i+1:04d}  |  Date: {call_date}", small))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.darkgreen))
        story.append(Spacer(1, 12))
        story.append(Paragraph("Contact Details", h2))
        data = [
            ["Customer ID", customer_id],
            ["Contact Date", call_date],
            ["Issue Type", issue.title()],
            ["Assigned Agent", agent],
            ["NPS Score (0-10)", str(nps)],
            ["NPS Category", sentiment.title()],
        ]
        t = Table(data, colWidths=[2.5*inch, 3.5*inch])
        t.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
            ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
        ]))
        story.append(t)
        story.append(Spacer(1, 16))
        story.append(Paragraph("Customer Verbatim Feedback", h2))
        if sentiment == "promoter":
            feedback = (f"Absolutely thrilled with the support I received today. The agent was knowledgeable, "
                        f"empathetic and resolved my {issue} within minutes. Will definitely recommend this service to friends.")
        elif sentiment == "passive":
            feedback = (f"The agent was helpful enough and my {issue} was resolved, but it took longer than expected. "
                        f"The hold times need improvement. Overall a decent experience.")
        else:
            feedback = (f"Very disappointed. My {issue} has been unresolved for over a week despite multiple contacts. "
                        f"I was transferred 3 times and no one took ownership. Considering switching providers.")
        story.append(Paragraph(feedback, body))
        story.append(Spacer(1, 12))
        story.append(Paragraph("Resolution Summary", h2))
        resolved = nps >= 7
        story.append(Paragraph(f"Issue Status: {'Resolved' if resolved else 'Escalated – Pending'}.", body))
        story.append(Paragraph(f"Follow-up Required: {'No' if resolved else 'Yes – within 24 hours'}.", body))
    return build

# ===========================================================================
# MFG – Inspection & Maintenance Reports
# ===========================================================================

failure_data = [
    ("Bearing Failure", "Mechanical", "CRITICAL", "Motor assembly B-07", "BCH-2024-089",
     "Metal shavings in lubricant, vibration at 12.4 mm/s (limit: 7 mm/s). Immediate shutdown required."),
    ("Coolant Leak", "Hydraulic", "MAJOR", "CNC Machine #14", "SL-400-LOT22",
     "Hydraulic line fracture at 8-bar joint. ~2L coolant lost. Production halted 4h. Line quarantined."),
    ("Sensor Drift", "Electrical", "MINOR", "Pressure Line 3", "QC-2025-012",
     "PS-200X reading 8.3% above calibrated value. Affects batch weight measurement. Recalibration completed."),
    ("Belt Tear", "Mechanical", "MAJOR", "Conveyor Line 1", "CVB-8800-B14",
     "40cm longitudinal tear from overload event. Belt #CVB-8800 installed 14 months ago. Replaced."),
    ("Weld Porosity", "Quality", "MAJOR", "Welding Station 3", "WLD-2025-0441",
     "Ultrasonic scan shows subsurface porosity >2mm. Argon purity 97.2% vs spec 99.5%. Batch quarantined."),
]

def make_mfg_inspection(i):
    fm = random.choice(failure_data)
    failure_mode, category, severity, location, batch, finding = fm
    inspector = fake.name()
    event_date = (datetime.today() - timedelta(days=random.randint(1,60))).strftime("%Y-%m-%d")
    downtime = round(random.uniform(0.5, 12.0), 1)

    def build(doc, story):
        story.append(Paragraph("QUALITY INSPECTION REPORT", h1))
        story.append(Paragraph(f"Report ID: QIR-{i+1:04d}  |  Date: {event_date}  |  Inspector: {inspector}", small))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.darkorange))
        story.append(Spacer(1, 12))
        severity_color = colors.red if severity == "CRITICAL" else (colors.orange if severity == "MAJOR" else colors.green)
        story.append(Paragraph(f"<font color='{'red' if severity=='CRITICAL' else 'orange' if severity=='MAJOR' else 'green'}'>"
                               f"SEVERITY: {severity}</font>", h2))
        story.append(Spacer(1, 8))
        story.append(Paragraph("Incident Details", h2))
        data = [
            ["Failure Mode", failure_mode],
            ["Category", category],
            ["Location / Asset", location],
            ["Component Batch", batch],
            ["Downtime (hours)", str(downtime)],
            ["Root Cause Category", category],
        ]
        t = Table(data, colWidths=[2.5*inch, 3.5*inch])
        t.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
            ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0,0), (-1,-1), [colors.lightyellow, colors.white]),
        ]))
        story.append(t)
        story.append(Spacer(1, 16))
        story.append(Paragraph("Inspection Findings", h2))
        story.append(Paragraph(finding, body))
        story.append(Spacer(1, 10))
        story.append(Paragraph("Corrective Action", h2))
        action = random.choice([
            f"Component from batch {batch} replaced. PM schedule updated to quarterly.",
            f"Batch {batch} quarantined pending supplier quality review. Replacement ordered.",
            f"Recalibration completed. Monitoring frequency increased to daily.",
            f"Root cause escalated to engineering team. Redesign under review.",
        ])
        story.append(Paragraph(action, body))
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"Signed off by: {inspector}  |  Date: {event_date}", small))
    return build

# ===========================================================================
# Generate all PDFs for selected industry
# ===========================================================================

generated = []

if industry == "fins":
    for pid, pname, ptype, apr_lo, apr_hi, min_inc, max_amt, term, highlights in fins_products:
        fn = f"{pid}_product_sheet.pdf"
        path = make_doc(fn, make_fins_product_pdf(pid, pname, ptype, apr_lo, apr_hi, min_inc, max_amt, term, highlights))
        generated.append(path)

elif industry == "gaming":
    for i in range(20):
        fn = f"appeal_{i+1:03d}.pdf"
        path = make_doc(fn, make_gaming_appeal(i))
        generated.append(path)

elif industry == "dnb":
    for i in range(15):
        fn = f"prospect_profile_{i+1:03d}.pdf"
        path = make_doc(fn, make_dnb_prospect(i))
        generated.append(path)

elif industry == "telco":
    for i in range(25):
        fn = f"survey_{i+1:03d}.pdf"
        path = make_doc(fn, make_telco_survey(i))
        generated.append(path)

elif industry == "mfg":
    for i in range(30):
        fn = f"inspection_report_{i+1:03d}.pdf"
        path = make_doc(fn, make_mfg_inspection(i))
        generated.append(path)

print(f"Generated {len(generated)} PDFs in {volume_path}")
for p in generated[:5]:
    print(" ", p)
if len(generated) > 5:
    print(f"  ... and {len(generated)-5} more")

# COMMAND ----------

# MAGIC %md ## Verify volume contents

# COMMAND ----------

import subprocess
result = subprocess.run(["ls", "-la", volume_path], capture_output=True, text=True)
print(result.stdout)
