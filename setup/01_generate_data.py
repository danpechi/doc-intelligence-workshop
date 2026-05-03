# Databricks notebook source
# MAGIC %md
# MAGIC # Setup: Generate Synthetic Tables
# MAGIC
# MAGIC Creates industry-specific Delta tables with realistic synthetic data.
# MAGIC Each table is designed to showcase different AI Functions in the workshop.
# MAGIC
# MAGIC **Industries and their use cases:**
# MAGIC - `fins`   – Merchant extraction from receipts & fuzzy merchant matching
# MAGIC - `gaming` – Player safety / content moderation
# MAGIC - `dnb`    – Customer outreach email sequencing (prospect analysis)
# MAGIC - `telco`  – Call center feedback classification
# MAGIC - `mfg`    – Quality event & maintenance log analysis

# COMMAND ----------

dbutils.widgets.text("catalog", "main")
dbutils.widgets.text("schema_prefix", "ai_functions_workshop")
dbutils.widgets.text("industry", "fins")

catalog = dbutils.widgets.get("catalog")
schema_prefix = dbutils.widgets.get("schema_prefix")
industry = dbutils.widgets.get("industry").lower().strip()
schema = f"{schema_prefix}_{industry}"
full_schema = f"{catalog}.{schema}"

print(f"Writing tables to: {full_schema}")

# COMMAND ----------

# MAGIC %pip install faker --quiet

# COMMAND ----------

import random
import json
from datetime import datetime, timedelta
from faker import Faker
from pyspark.sql import Row
from pyspark.sql.types import *

fake = Faker()
random.seed(42)
Faker.seed(42)

spark.sql(f"USE CATALOG {catalog}")
spark.sql(f"USE SCHEMA {schema}")

# COMMAND ----------

# MAGIC %md ## Industry: FINS (Financial Services)
# MAGIC
# MAGIC **Tables:**
# MAGIC - `merchant_transactions` – raw bank transactions with messy merchant names
# MAGIC - `merchant_canonical`   – clean canonical merchant reference list
# MAGIC - `product_documents`    – loan and credit card product specs (markdown)

# COMMAND ----------

if industry == "fins":

    # --- merchant_canonical -------------------------------------------------
    canonical_merchants = [
        ("MCDON001", "McDonald's", "Fast Food", "USA"),
        ("STBK001",  "Starbucks",  "Coffee & Cafe", "USA"),
        ("AMZN001",  "Amazon",     "E-commerce", "USA"),
        ("WALMART01","Walmart",    "Retail", "USA"),
        ("UBER001",  "Uber",       "Ride-sharing", "USA"),
        ("NETF001",  "Netflix",    "Streaming", "USA"),
        ("SPOT001",  "Spotify",    "Streaming", "USA"),
        ("TGIF001",  "TGI Fridays","Casual Dining", "USA"),
        ("WHLF001",  "Whole Foods","Grocery", "USA"),
        ("COST001",  "Costco",     "Wholesale Retail", "USA"),
        ("SHELL001", "Shell",      "Gas Station", "USA"),
        ("CVS001",   "CVS Pharmacy","Pharmacy", "USA"),
        ("APPL001",  "Apple Inc",  "Technology", "USA"),
        ("GOOGL001", "Google",     "Technology", "USA"),
        ("AIRB001",  "Airbnb",     "Travel & Lodging", "USA"),
        ("DELTA001", "Delta Air Lines","Airline", "USA"),
        ("HILTON01", "Hilton Hotels","Hotel", "USA"),
        ("TARGET01", "Target",     "Retail", "USA"),
        ("BESTB001", "Best Buy",   "Electronics", "USA"),
        ("HOME001",  "Home Depot", "Home Improvement", "USA"),
    ]

    canonical_rows = [
        Row(merchant_id=m[0], canonical_name=m[1], category=m[2], country=m[3])
        for m in canonical_merchants
    ]
    spark.createDataFrame(canonical_rows).write.mode("overwrite").saveAsTable("merchant_canonical")

    # --- messy merchant name variants ---------------------------------------
    name_variants = {
        "McDonald's": ["MCDONALD'S #3421", "Mc Donalds", "MCDONALDS CORP", "mcdonald s", "MC DONALDS 00312"],
        "Starbucks": ["STARBUCKS STORE #12", "STARBUCKS COFFEE", "starbucks", "Starbuks", "SBUX #9981"],
        "Amazon": ["AMAZON.COM*1X2Y3Z", "AMZN Mktp US", "Amazon Prime", "AMAZON WEB SVCS", "amazon mktplace"],
        "Walmart": ["WALMART SUPERCENTER", "WAL-MART #4512", "Walmart Neighborhood Mkt", "WALMART.COM", "WM SUPERCENTER #123"],
        "Uber": ["UBER *TRIP", "Uber Technologies", "UBER EATS", "uber trip help.uber.com", "UBER* PENDING"],
        "Netflix": ["NETFLIX.COM", "Netflix Inc", "NETFLIX", "netflix monthly", "NETFLIX*COM"],
        "Spotify": ["Spotify USA", "SPOTIFY AB", "SPOTIFY P1234", "spotify premium", "SPOTIFY*"],
        "TGI Fridays": ["T.G.I. FRIDAY'S", "TGI FRIDAYS #221", "TGI Friday's", "TGIF RESTAURANT", "TGI FRIDAYS CORP"],
        "Whole Foods": ["WHOLE FOODS MARKET", "WFM #10245", "Whole Foods Mkt", "WHOLE FOODS MKT", "wholefoods"],
        "Costco": ["COSTCO WHSE #0472", "COSTCO GAS", "Costco.com", "COSTCO WHOLESALE", "COSTCO WHSE"],
    }

    # Build transactions
    txn_rows = []
    all_variants = [(canonical, variant) for canonical, variants in name_variants.items() for variant in variants]
    for i in range(200):
        canonical, messy_name = random.choice(all_variants)
        amount = round(random.uniform(5.0, 850.0), 2)
        date = fake.date_between(start_date="-90d", end_date="today")
        txn_rows.append(Row(
            transaction_id=f"TXN{i+1:05d}",
            transaction_date=str(date),
            merchant_name_raw=messy_name,
            amount=amount,
            currency="USD",
            card_last4=str(random.randint(1000, 9999)),
            customer_id=f"CUST{random.randint(1000,9999)}",
        ))

    spark.createDataFrame(txn_rows).write.mode("overwrite").saveAsTable("merchant_transactions")

    # --- product_documents --------------------------------------------------
    products = [
        ("LOAN001", "Personal Loan – Standard",
         "Min income: $25,000/yr. APR: 8.99%–24.99%. Term: 12–60 months. Max: $50,000. "
         "No collateral required. Fast approval within 24 hours. Suitable for debt consolidation."),
        ("LOAN002", "Home Improvement Loan",
         "Min income: $40,000/yr. APR: 6.49%–18.99%. Term: 24–120 months. Max: $150,000. "
         "Secured against property. Ideal for renovations and repairs."),
        ("LOAN003", "Auto Loan",
         "Min income: $20,000/yr. APR: 4.99%–14.99%. Term: 24–84 months. Max: $75,000. "
         "New and used vehicles. No prepayment penalty."),
        ("LOAN004", "Student Loan Refinance",
         "Min income: $30,000/yr. APR: 3.99%–9.99%. Term: 5–20 years. Max: $250,000. "
         "Federal and private student loans eligible. Grace period available."),
        ("LOAN005", "Business Micro Loan",
         "Min income: $15,000/yr revenue. APR: 10.99%–29.99%. Term: 6–36 months. Max: $25,000. "
         "For small businesses under 2 years old. Minimal documentation required."),
        ("CC001", "Cashback Platinum Card",
         "2% cashback on all purchases. 5% on groceries and gas. $95 annual fee. "
         "APR: 17.99%–26.99%. $200 welcome bonus after $1,000 spend. No foreign transaction fees."),
        ("CC002", "Travel Rewards Elite",
         "3x points on travel and dining. 1x on all other purchases. $450 annual fee. "
         "APR: 19.99%–28.99%. $300 travel credit. Airport lounge access. Trip delay insurance."),
        ("CC003", "Student Starter Card",
         "1.5% cashback on all purchases. No annual fee. APR: 15.99%–22.99%. "
         "$50 bonus after $300 spend in first 3 months. Credit building tools included."),
        ("CC004", "Business Rewards Card",
         "4x points on office supplies and telecom. 2x on all business purchases. $250 annual fee. "
         "APR: 18.99%–27.99%. $500 welcome bonus. Employee cards at no extra cost."),
        ("CC005", "Secured Credit Builder",
         "No credit history required. Security deposit $200–$5,000. 1% cashback. No annual fee. "
         "APR: 22.99%. Automatic upgrade review after 12 months of on-time payments."),
    ]

    product_rows = [
        Row(product_id=p[0], product_name=p[1], document_text=p[2])
        for p in products
    ]
    spark.createDataFrame(product_rows).write.mode("overwrite").saveAsTable("product_documents")
    print("FINS tables created: merchant_transactions, merchant_canonical, product_documents")

# COMMAND ----------

# MAGIC %md ## Industry: Gaming (Safety & Content Moderation)

# COMMAND ----------

if industry == "gaming":

    # --- chat_logs ----------------------------------------------------------
    safe_messages = [
        "GG everyone, great match!",
        "Anyone want to party up for ranked?",
        "What's the best build for the new patch?",
        "Nice shot! How did you aim so fast?",
        "I need to improve my map awareness.",
        "Thanks for the carry guys!",
        "This map is so fun, let's play another round.",
        "Can someone explain the new mechanics?",
        "I love this game's new update.",
        "wp all, see you next game",
    ]
    warning_messages = [
        "You're trash at this game, bro.",
        "Uninstall the game you noob.",
        "This team is absolutely useless.",
        "Why are you so bad?! It's just a game.",
        "You're ruining the match for everyone.",
        "Learn to play before queuing ranked.",
        "What a terrible player, holy moly.",
        "Stop feeding you absolute clown.",
    ]
    violation_messages = [
        "I'm going to find out where you live.",
        "People like you deserve to be banned forever.",
        "You are the worst human being.",
        "I'm telling everyone to report you.",
        "Racial slur: [REDACTED FOR TRAINING DATA]",
        "You make me want to quit gaming entirely.",
        "I'll grief every single game you're in.",
        "Stay off the internet you pathetic loser.",
    ]

    chat_rows = []
    for i in range(300):
        roll = random.random()
        if roll < 0.6:
            msg = random.choice(safe_messages)
            expected = "safe"
        elif roll < 0.85:
            msg = random.choice(warning_messages)
            expected = "warning"
        else:
            msg = random.choice(violation_messages)
            expected = "violation"

        chat_rows.append(Row(
            message_id=f"MSG{i+1:05d}",
            timestamp=str(fake.date_time_this_year()),
            player_id=f"PLR{random.randint(10000, 99999)}",
            game_id=f"GAME{random.randint(1000, 9999)}",
            message_text=msg,
            expected_label=expected,
        ))
    spark.createDataFrame(chat_rows).write.mode("overwrite").saveAsTable("chat_logs")

    # --- player_reports -----------------------------------------------------
    incidents = [
        ("Harassment", "Player used offensive language repeatedly throughout the match targeting a specific teammate."),
        ("Griefing", "Player intentionally fed the enemy team by walking into their base without fighting."),
        ("Cheating", "Player demonstrated impossible aim accuracy and map awareness. Suspected wall-hack or aimbot."),
        ("Hate Speech", "Player used slurs in voice chat directed at other players based on their apparent nationality."),
        ("Boosting", "Account appears to be piloted by a higher-skilled player to artificially inflate rank."),
        ("AFK Farming", "Player joined match but went AFK immediately, letting bots play to farm rewards."),
        ("Bug Abuse", "Player repeatedly exploited an out-of-bounds area to gain an unfair positional advantage."),
        ("Impersonation", "Player changed name to closely resemble a well-known streamer to deceive teammates."),
    ]

    report_rows = []
    for i in range(100):
        incident = random.choice(incidents)
        report_rows.append(Row(
            report_id=f"RPT{i+1:05d}",
            reported_player_id=f"PLR{random.randint(10000, 99999)}",
            reporting_player_id=f"PLR{random.randint(10000, 99999)}",
            game_id=f"GAME{random.randint(1000, 9999)}",
            incident_type=incident[0],
            description=incident[1],
            submitted_at=str(fake.date_time_this_month()),
            status="pending_review",
        ))
    spark.createDataFrame(report_rows).write.mode("overwrite").saveAsTable("player_reports")

    print("Gaming tables created: chat_logs, player_reports")

# COMMAND ----------

# MAGIC %md ## Industry: DNB (Digital Native Business – Prospect Analysis)

# COMMAND ----------

if industry == "dnb":

    tech_stacks = ["AWS + Kubernetes", "GCP + BigQuery", "Azure + Databricks", "Snowflake + dbt", "On-prem Oracle"]
    pain_points = [
        "Struggling with data silos across departments",
        "Manual reporting taking too much analyst time",
        "Need real-time inventory visibility",
        "Customer churn prediction is manual and slow",
        "Regulatory reporting is error-prone and delayed",
        "Data quality issues slowing down product decisions",
        "Cannot monetize data assets effectively",
        "Machine learning models take months to deploy",
    ]
    company_types = ["SaaS startup", "E-commerce brand", "FinTech scaleup", "HealthTech company",
                     "Logistics platform", "MarTech agency", "InsurTech firm", "EdTech provider"]

    prospect_rows = []
    for i in range(150):
        employees = random.choice([15, 50, 120, 300, 800, 2000, 5000])
        funding = random.choice(["Seed ($2M)", "Series A ($15M)", "Series B ($45M)", "Series C ($120M)", "Public", "Bootstrapped"])
        tech = random.choice(tech_stacks)
        pain = random.choice(pain_points)
        ctype = random.choice(company_types)
        company_name = fake.company()
        domain = company_name.lower().replace(",", "").replace(" ", "") + ".com"
        description = (
            f"{company_name} is a {ctype} with {employees} employees and {funding} in funding. "
            f"They run on {tech}. Current challenge: {pain}. "
            f"The data team is growing and looking for modern solutions to scale analytics and ML."
        )
        prospect_rows.append(Row(
            prospect_id=f"PROS{i+1:04d}",
            company_name=company_name,
            website=f"https://www.{domain}",
            description=description,
            employees=employees,
            funding_stage=funding,
            tech_stack=tech,
            primary_pain_point=pain,
            company_type=ctype,
            created_at=str(fake.date_this_year()),
        ))

    spark.createDataFrame(prospect_rows).write.mode("overwrite").saveAsTable("prospect_companies")

    # ICP profiles
    icp_rows = [
        Row(icp_id="ICP001", name="Data-Driven SaaS", description="SaaS company 50-500 employees, cloud-native, struggling with ML deployment cycles", weight=1.0),
        Row(icp_id="ICP002", name="FinTech Scaleup", description="FinTech 100-2000 employees with regulatory reporting pain and real-time data needs", weight=0.9),
        Row(icp_id="ICP003", name="E-commerce Growth", description="E-commerce brand with real-time personalization needs and fragmented analytics stack", weight=0.8),
        Row(icp_id="ICP004", name="HealthTech Platform", description="HealthTech company with compliance requirements and ML-driven clinical decision support needs", weight=0.85),
        Row(icp_id="ICP005", name="Logistics Intelligence", description="Logistics firm with high-volume operational data needing predictive maintenance and routing", weight=0.75),
    ]
    spark.createDataFrame(icp_rows).write.mode("overwrite").saveAsTable("icp_profiles")

    print("DNB tables created: prospect_companies, icp_profiles")

# COMMAND ----------

# MAGIC %md ## Industry: Telco (Call Center Feedback Classification)

# COMMAND ----------

if industry == "telco":

    issue_types = ["billing", "technical", "coverage", "plan_change", "device", "roaming", "churn"]
    sentiments = ["positive", "neutral", "negative", "very_negative"]

    transcripts = [
        ("billing", "negative",
         "I've been charged twice for my plan this month. I called last week and nobody fixed it. "
         "This is completely unacceptable. I expect a full refund immediately."),
        ("technical", "neutral",
         "My internet speed has been dropping every evening around 7 PM. It's been happening for 2 weeks. "
         "Is there maintenance in my area? My plan says 200 Mbps but I'm getting 15."),
        ("churn", "very_negative",
         "I am cancelling my service. I've been a customer for 8 years and the network quality has gotten worse "
         "while my bill keeps going up. Please connect me to the cancellation department."),
        ("plan_change", "positive",
         "I'd like to upgrade to the unlimited data plan. My family uses a lot of data now that we all work from home. "
         "Can you tell me about the best option for a family of 4?"),
        ("coverage", "negative",
         "I have zero signal at my new office. It's in the downtown area so I don't understand why there's no coverage. "
         "My colleagues with other carriers have full bars."),
        ("device", "neutral",
         "My phone stopped making calls after the last software update. I can receive texts but cannot place calls. "
         "I've tried restarting multiple times. Is this a known issue?"),
        ("roaming", "negative",
         "I was charged $200 in roaming fees during my Canada trip even though I have the international add-on. "
         "The rep told me it was included. I need this reversed."),
        ("billing", "positive",
         "I just want to say thank you to the agent who helped me last week. She was incredibly patient "
         "and resolved my billing dispute completely. Best customer service experience I've had."),
    ]

    call_rows = []
    for i in range(200):
        transcript_template = random.choice(transcripts)
        customer_id = f"CUST{random.randint(100000, 999999)}"
        call_rows.append(Row(
            call_id=f"CALL{i+1:05d}",
            customer_id=customer_id,
            call_date=str(fake.date_this_year()),
            duration_seconds=random.randint(90, 1800),
            transcript=transcript_template[2] + " " + fake.sentence(),
            issue_type=transcript_template[0],
            sentiment=transcript_template[1],
            agent_id=f"AGT{random.randint(100, 999)}",
            resolved=random.choice([True, False, True, True]),
        ))

    spark.createDataFrame(call_rows).write.mode("overwrite").saveAsTable("customer_calls")

    # Resolution playbooks
    playbook_rows = [
        Row(playbook_id="PB001", issue_type="billing", title="Duplicate Charge Resolution",
            steps="1. Verify charge in billing system. 2. Check payment history. 3. Issue credit if confirmed duplicate. 4. Send confirmation email."),
        Row(playbook_id="PB002", issue_type="technical", title="Speed Degradation Troubleshooting",
            steps="1. Run speed test remotely. 2. Check for area outages. 3. Reboot modem remotely. 4. Schedule technician if unresolved."),
        Row(playbook_id="PB003", issue_type="churn", title="Retention Offer Protocol",
            steps="1. Identify customer tenure and value. 2. Offer loyalty discount (10-30%). 3. Propose plan upgrade at same price. 4. Escalate to retention specialist if needed."),
        Row(playbook_id="PB004", issue_type="roaming", title="Roaming Charge Dispute",
            steps="1. Review roaming charges and plan add-ons. 2. Check if add-on was active during travel dates. 3. Credit charges if add-on was sold incorrectly. 4. Document for quality review."),
        Row(playbook_id="PB005", issue_type="coverage", title="Coverage Complaint Handling",
            steps="1. Check coverage map for reported location. 2. Log as coverage gap if confirmed. 3. Offer Wi-Fi calling as workaround. 4. Notify network team for area review."),
    ]
    spark.createDataFrame(playbook_rows).write.mode("overwrite").saveAsTable("resolution_playbooks")

    print("Telco tables created: customer_calls, resolution_playbooks")

# COMMAND ----------

# MAGIC %md ## Industry: MFG (Manufacturing – Quality & Maintenance)

# COMMAND ----------

if industry == "mfg":

    failure_modes = [
        ("Bearing Failure", "Mechanical", "critical",
         "High vibration detected on motor assembly unit B-07. Bearing temperature exceeded threshold. "
         "Component batch #MFG-2024-089 suspected. Technician report: metal shavings found in lubricant."),
        ("Coolant Leak", "Hydraulic", "major",
         "Coolant leak on CNC machine #14 from hydraulic line. Production halted for 4 hours. "
         "Supplier component SL-400 from vendor Hydro-Parts Inc. Last PM was 6 months ago."),
        ("Sensor Calibration Drift", "Electrical", "minor",
         "Pressure sensor on line 3 reading 8% above calibrated value. Affects batch quality measurement. "
         "Sensor model PS-200X, batch QC-2025-012. Recalibration scheduled."),
        ("Conveyor Belt Tear", "Mechanical", "major",
         "Main conveyor belt on line 1 suffered a 40cm longitudinal tear. Root cause: excessive load from batch "
         "overweight event on 2025-03-12. Belt part #CVB-8800, installed 14 months ago."),
        ("PLC Software Fault", "Electrical", "critical",
         "Programmable logic controller on packaging station threw error code E-4421. "
         "Line stopped for 6 hours. Firmware version 3.2.1 suspected. Vendor contacted for patch."),
        ("Weld Quality Defect", "Quality", "major",
         "Ultrasonic inspection revealed subsurface porosity in weld seam on batch WLD-2025-0441. "
         "Root cause: argon gas purity below spec (97.2% vs required 99.5%). Supplier: GasSupply Co."),
        ("Pump Cavitation", "Hydraulic", "minor",
         "Pump P-12 showing cavitation symptoms at low flow rates. Affects chemical dosing accuracy. "
         "Component from vendor FluidTech, installed batch FT-2024-321. Monitoring in place."),
        ("Overheating Motor", "Electrical", "critical",
         "Drive motor on extruder line 5 overheated and tripped thermal protection. "
         "Ambient temperature in factory was 38°C. Cooling system inadequate for summer loads. "
         "Motor model EM-750, batch EM-2024-044."),
    ]

    components = [
        Row(component_id=f"COMP{i+1:04d}",
            part_number=f"PT-{random.randint(1000,9999)}",
            description=random.choice(["Hydraulic Pump", "Conveyor Motor", "PLC Controller", "Pressure Sensor",
                                        "Bearing Assembly", "Coolant Valve", "Weld Nozzle", "Drive Belt"]),
            batch_id=f"BCH-{2024 + random.randint(0,1)}-{random.randint(100,999)}",
            supplier=random.choice(["Hydro-Parts Inc", "FluidTech", "GasSupply Co", "MotorTech", "SensorMax"]),
            installed_date=str(fake.date_between(start_date="-2y", end_date="today")),
        )
        for i in range(100)
    ]
    spark.createDataFrame(components).write.mode("overwrite").saveAsTable("components")

    maint_rows = []
    for i in range(300):
        fm = random.choice(failure_modes)
        maint_rows.append(Row(
            log_id=f"MNT{i+1:05d}",
            event_date=str(fake.date_this_year()),
            line_id=f"LINE-{random.randint(1,8)}",
            failure_mode=fm[0],
            category=fm[1],
            severity=fm[2],
            technician_notes=fm[3] + " " + fake.sentence(),
            component_id=f"COMP{random.randint(1,100):04d}",
            downtime_hours=round(random.uniform(0.5, 12.0), 1),
            corrective_action=random.choice([
                "Part replaced", "Recalibrated", "Firmware updated", "PM completed",
                "Supplier contacted", "Monitoring increased", "Line redesigned"
            ]),
        ))
    spark.createDataFrame(maint_rows).write.mode("overwrite").saveAsTable("maintenance_logs")

    print("MFG tables created: components, maintenance_logs")

# COMMAND ----------

# MAGIC %md ## Verify all tables

# COMMAND ----------

display(spark.sql(f"SHOW TABLES IN {full_schema}"))
