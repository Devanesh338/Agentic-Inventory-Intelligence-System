import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    """Sets background color of a table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Sets inner margins for a table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def add_callout(doc, text, title="NOTE"):
    """Adds a stylish callout box with a colored left border."""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.5)
    set_cell_background(cell, "F8FAFC")
    set_cell_margins(cell, top=140, bottom=140, left=200, right=160)
    
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(f'''
        <w:tcBorders {nsdecls("w")}>
            <w:top w:val="none"/>
            <w:left w:val="single" w:sz="24" w:space="0" w:color="2563EB"/>
            <w:bottom w:val="none"/>
            <w:right w:val="none"/>
        </w:tcBorders>
    ''')
    tcPr.append(borders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    run_title = p.add_run(f"[{title}] ")
    run_title.bold = True
    run_title.font.name = "Calibri"
    run_title.font.size = Pt(10)
    run_title.font.color.rgb = RGBColor(37, 99, 235)
    
    run_text = p.add_run(text)
    run_text.font.name = "Calibri"
    run_text.font.size = Pt(10)
    run_text.font.color.rgb = RGBColor(51, 65, 85)
    
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

def format_table(tbl, col_widths, headers, data):
    """Formats a table with a dark header, zebra rows, and explicit column widths."""
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    
    # Header Row
    hdr_row = tbl.rows[0]
    for idx, heading in enumerate(headers):
        cell = hdr_row.cells[idx]
        cell.width = Inches(col_widths[idx])
        set_cell_background(cell, "1E3A8A")
        set_cell_margins(cell, top=120, bottom=120, left=140, right=140)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = p.add_run(heading)
        run.bold = True
        run.font.name = "Calibri"
        run.font.size = Pt(10)
        run.font.color.rgb = RGBColor(255, 255, 255)
        
    # Data Rows
    for r_idx, row_data in enumerate(data):
        row = tbl.add_row()
        bg_color = "F8FAFC" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(row_data):
            cell = row.cells[c_idx]
            cell.width = Inches(col_widths[c_idx])
            set_cell_background(cell, bg_color)
            set_cell_margins(cell, top=100, bottom=100, left=140, right=140)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            run = p.add_run(str(val))
            run.font.name = "Calibri"
            run.font.size = Pt(9.5)
            run.font.color.rgb = RGBColor(30, 41, 59)
            if c_idx == 0:
                run.bold = True

def add_heading_1(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(18)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.bold = True
    run.font.name = "Calibri"
    run.font.size = Pt(16)
    run.font.color.rgb = RGBColor(30, 58, 138) # Navy #1E3A8A
    return p

def add_heading_2(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.bold = True
    run.font.name = "Calibri"
    run.font.size = Pt(13)
    run.font.color.rgb = RGBColor(37, 99, 235) # Blue #2563EB
    return p

def add_heading_3(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.bold = True
    run.font.name = "Calibri"
    run.font.size = Pt(11)
    run.font.color.rgb = RGBColor(71, 85, 105) # Slate #475569
    return p

def add_body(doc, text, bold_prefix=None, space_after=4):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.bold = True
        r_pre.font.name = "Calibri"
        r_pre.font.size = Pt(10.5)
        r_pre.font.color.rgb = RGBColor(15, 23, 42)
    r = p.add_run(text)
    r.font.name = "Calibri"
    r.font.size = Pt(10.5)
    r.font.color.rgb = RGBColor(51, 65, 85)
    return p

def add_bullet(doc, text, bold_prefix=None):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.bold = True
        r_pre.font.name = "Calibri"
        r_pre.font.size = Pt(10.5)
        r_pre.font.color.rgb = RGBColor(15, 23, 42)
    r = p.add_run(text)
    r.font.name = "Calibri"
    r.font.size = Pt(10.5)
    r.font.color.rgb = RGBColor(51, 65, 85)
    return p

def build_project_summary_docx(output_path):
    doc = docx.Document()
    
    # Page Setup: Standard 1 inch margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        
    # =========================================================================
    # DOCUMENT COVER / HEADER
    # =========================================================================
    p_pre = doc.add_paragraph()
    p_pre.paragraph_format.space_before = Pt(0)
    p_pre.paragraph_format.space_after = Pt(4)
    r_sub = p_pre.add_run("ACADEMIC FINAL YEAR PROJECT SPECIFICATION & SYSTEM MANUAL")
    r_sub.font.name = "Calibri"
    r_sub.font.size = Pt(9.5)
    r_sub.font.bold = True
    r_sub.font.color.rgb = RGBColor(100, 116, 139)
    
    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(4)
    r_title = p_title.add_run("AEMIIF: Agentic Explainable Multi-Agent Inventory Intelligence Framework")
    r_title.font.name = "Calibri"
    r_title.font.size = Pt(22)
    r_title.font.bold = True
    r_title.font.color.rgb = RGBColor(30, 58, 138) # Navy
    
    p_desc = doc.add_paragraph()
    p_desc.paragraph_format.space_before = Pt(0)
    p_desc.paragraph_format.space_after = Pt(14)
    r_desc = p_desc.add_run("Autonomous Multi-Echelon Inventory Optimization, Operations Research Solver Integration, Explainable AI (XAI), and Human-in-the-Loop Procurement Intelligence")
    r_desc.font.name = "Calibri"
    r_desc.font.size = Pt(11)
    r_desc.font.italic = True
    r_desc.font.color.rgb = RGBColor(71, 85, 105)
    
    # Metadata Table
    meta_tbl = doc.add_table(rows=1, cols=4)
    meta_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_headers = ["Project Version", "Architecture", "Primary Stack", "Database"]
    meta_data = [["v1.0.0 (Enterprise Production)", "Multi-Agent Directed Graph (LangGraph)", "FastAPI + React 19 + Streamlit + PuLP", "PostgreSQL (Neon Cloud / Local)"]]
    format_table(meta_tbl, [1.5, 1.8, 1.8, 1.4], meta_headers, meta_data)
    
    doc.add_paragraph().paragraph_format.space_after = Pt(8)
    
    # =========================================================================
    # 1. EXECUTIVE SUMMARY
    # =========================================================================
    add_heading_1(doc, "1. Executive Summary & Project Vision")
    add_body(doc, "Modern enterprise supply chain management faces significant complexities including volatile regional consumer demand, non-linear multi-echelon holding costs, fluctuating supplier lead times, and capacity limitations across suppliers. Traditional ERP and inventory management solutions rely either on simplistic rule-based min-max safety stock triggers or opaque 'black box' machine learning algorithms that lack auditability and human trust.")
    add_body(doc, "The Agentic Explainable Multi-Agent Inventory Intelligence Framework (AEMIIF) is a next-generation decision intelligence platform. It bridges the gap between state-of-the-art Generative AI / Large Language Models (LLMs) and mathematically provable Operations Research (OR) by combining LangGraph multi-agent orchestration with Mixed Integer Linear Programming (MILP).")
    
    add_callout(doc, 
        "AEMIIF operates under a strict 'AI Proposes, Operations Research Guarantees, Human Decides' paradigm. Natural language directives are translated into rigorous mathematical constraints, solved with provable optimality, statistically validated with paired hypothesis tests, and presented through transparent explanations for executive approval.",
        "CORE PARADIGM")
    
    add_heading_2(doc, "Key Business Objectives")
    add_bullet(doc, "Cost Minimization: Simultaneously reduces procurement costs, inventory holding fees, transit costs, and stockout penalties.", "1. Multi-Objective Optimization: ")
    add_bullet(doc, "Natural Language Interface: Enables supply chain directors to express complex procurement scenarios in conversational English (e.g., 'Optimize inventory for Chennai-North with budget of ₹200,000 within 5 days delivery').", "2. Conversational Accessibility: ")
    add_bullet(doc, "Provable Feasibility: Enforces strict mathematical limits on supplier capacity, working capital budgets, lead times, and service levels using MILP.", "3. Hard Constraint Verification: ")
    add_bullet(doc, "Explainable AI (XAI): Produces plain-language audit trails that explain why specific suppliers were chosen and why trade-offs were made.", "4. Transparent Provenance: ")
    add_bullet(doc, "Statistical Rigor: Benchmarks optimized procurement decisions against baseline supplier market averages via automated Paired T-Tests (p < 0.05).", "5. Empirical Validation: ")
    
    # =========================================================================
    # 2. END-TO-END ARCHITECTURE
    # =========================================================================
    add_heading_1(doc, "2. System Architecture & Component Interaction")
    add_body(doc, "The AEMIIF system is designed as an asynchronous, loosely coupled microservices architecture structured into five principal layers: Presentation, API Gateway, Multi-Agent Orchestration, Mathematical Optimization Engine, and Enterprise Persistence.")
    
    # Architecture Table
    arch_tbl = doc.add_table(rows=1, cols=4)
    arch_headers = ["Layer", "Key Technologies", "Primary Role", "Key Artifacts / Endpoints"]
    arch_data = [
        ["Presentation (Web)", "React 19, TypeScript, Vite, Tailwind CSS, Recharts", "Executive dashboard with 7 specialized pages for optimization, analytics, validation, and approvals.", "http://localhost:5173\nExecutive UI Suite"],
        ["Presentation (Demo)", "Streamlit, Plotly Express, Pandas", "Interactive demonstration and operational inspection dashboard with live data filtering.", "http://localhost:8501\nPhase 5 Dashboard"],
        ["API Gateway", "FastAPI, Uvicorn, Pydantic v2, CORS", "Asynchronous REST API routing, request validation, state serialization, and canonical responses.", "http://localhost:8000\n/api/v1/*, OpenAPI /docs"],
        ["Agent Orchestration", "LangGraph, LangChain Core, OpenAI GPT-4o-mini", "Deterministic state graph coordinating 7 specialized AI agents across a cyclic-free DAG pipeline.", "AEMIIFState, Graph Execution Engine"],
        ["Optimization Engine", "PuLP, COIN-OR CBC Solver, SciPy, NumPy", "Formulates Mixed Integer Linear Programming (MILP) models and executes paired hypothesis t-tests.", "MILP Formulation, Paired T-Test"],
        ["Persistence Tier", "PostgreSQL (Neon Cloud / Local), psycopg2 pool", "Relational persistence of 29,200+ historical sales records, inventory statuses, suppliers, and decisions.", "sales_history, inventory, suppliers, procurement_decisions"]
    ]
    format_table(arch_tbl, [1.3, 1.6, 2.1, 1.5], arch_headers, arch_data)
    
    doc.add_paragraph().paragraph_format.space_after = Pt(6)
    
    add_heading_2(doc, "Data Flow Lifecycle (End-to-End)")
    add_body(doc, "1. Ingestion / Data Sourcing: The platform queries the pre-seeded PostgreSQL database or ingests custom CSV files (sales history, store inventory, supplier catalogs) with automatic schema deduplication and validation.")
    add_body(doc, "2. Requirement Parsing: The executive enters an operational query. The RequirementParserAgent extracts budget limits, lead-time thresholds, service-level targets, and preference weights.")
    add_body(doc, "3. Multi-Agent Analysis: ForecastAgent computes regional demand forecasts; InventoryAgent analyzes safety stock gaps and stockout vulnerabilities; SupplierAgent filters candidate vendors and computes logistics costs.")
    add_body(doc, "4. Capacity Intelligence: Evaluates global and regional supplier capacity constraints to verify mathematical problem feasibility.")
    add_body(doc, "5. MILP Optimization: PuLP translates the state into a formal mathematical model and solves for the optimal purchase allocation vector.")
    add_body(doc, "6. Post-Validation & XAI: Enforces all constraint satisfaction tests, performs a paired t-test against baseline market averages, and synthesizes natural language executive explanations.")
    add_body(doc, "7. Executive Approval: The decision is presented on the React dashboard for human approval, logging the audit trail to PostgreSQL.")

    # =========================================================================
    # 3. COMPLETE TECHNOLOGY STACK & DEPENDENCIES
    # =========================================================================
    add_heading_1(doc, "3. Comprehensive Technology Stack & Dependencies")
    add_body(doc, "AEMIIF utilizes modern, production-grade enterprise software technologies across both the backend intelligence engine and the frontend presentation layers.")
    
    add_heading_2(doc, "Backend Python Ecosystem")
    py_tbl = doc.add_table(rows=1, cols=4)
    py_headers = ["Package Name", "Version", "Category", "Functional Role in Project"]
    py_data = [
        ["fastapi", "0.115+", "Web Framework", "High-performance asynchronous API engine with automatic OpenAPI documentation."],
        ["uvicorn", "0.34+", "ASGI Web Server", "Lightning-fast ASGI server for hosting FastAPI endpoints with hot-reloading."],
        ["pydantic", "2.10+", "Data Validation", "Type-safe schemas, request/response models, and environment settings parsing."],
        ["langgraph", "0.2+", "Agent Framework", "Stateful, multi-actor orchestration graph for cyclic-free agent execution."],
        ["langchain-core", "0.3+", "LLM Abstraction", "Core messaging abstractions, prompt templates, and agent tool execution."],
        ["langchain-openai", "0.3+", "LLM Integration", "Client integration with OpenAI models for natural language requirement parsing."],
        ["pulp", "2.8+", "Operations Research", "Mixed Integer Linear Programming modeling tool communicating with COIN-OR CBC."],
        ["scipy", "1.14+", "Scientific Computing", "Statistical hypothesis testing (paired t-test) to validate procurement savings."],
        ["numpy", "2.0+", "Numerical Analysis", "High-speed array processing, variance calculations, and vector operations."],
        ["pandas", "2.2+", "Data Engineering", "DataFrame transformations, CSV dataset ingestion, and demand aggregation."],
        ["psycopg2-binary", "2.9+", "Database Driver", "Threaded connection pool driver communicating with PostgreSQL database."],
        ["python-dotenv", "1.0+", "Configuration", "Loads sensitive credentials, API keys, and database URLs from .env."],
        ["streamlit", "1.40+", "Demonstration UI", "Interactive exploratory dashboard with real-time reactive charting."],
        ["plotly", "5.24+", "Visualization", "Interactive charts, histograms, and supply chain graphs for Streamlit."],
        ["pytest", "9.1+", "Quality Assurance", "Automated test runner executing 108 unit, integration, and E2E test cases."],
        ["python-docx", "1.2+", "Documentation", "Automated generation of enterprise executive reports and system documentation."]
    ]
    format_table(py_tbl, [1.4, 0.8, 1.4, 2.9], py_headers, py_data)
    
    doc.add_paragraph().paragraph_format.space_after = Pt(6)
    
    add_heading_2(doc, "Frontend React Ecosystem")
    fe_tbl = doc.add_table(rows=1, cols=4)
    fe_headers = ["Package Name", "Version", "Category", "Functional Role in Project"]
    fe_data = [
        ["react", "19.2+", "UI Framework", "Core reactive component architecture powering the executive UI."],
        ["react-dom", "19.2+", "DOM Renderer", "Virtual DOM rendering engine optimized for React 19."],
        ["typescript", "6.0+", "Type Safety", "Strict compile-time static typing across all components, API clients, and stores."],
        ["vite", "8.3+", "Build Tool", "Next-generation frontend tooling offering instant HMR and optimized bundling."],
        ["react-router-dom", "7.18+", "Client Routing", "Declarative SPA routing across all 7 executive dashboard pages."],
        ["recharts", "3.10+", "Data Visualization", "SVG-based interactive charts (Pie charts, Cost breakdown, KPIs, Progress)."],
        ["zustand", "5.0+", "State Management", "Lightweight, centralized reactive state store tracking optimization states and uploads."],
        ["lucide-react", "1.49+", "Icon Library", "Consistent, high-quality icon set across navigational and status components."],
        ["axios", "1.20+", "HTTP Client", "Promise-based HTTP client for backend REST API communication with interceptors."],
        ["oxlint", "1.81+", "Code Quality", "High-performance Rust-based linter ensuring zero static code defects."],
        ["vitest", "5.0+", "Unit Testing", "Vite-native unit and component test runner for frontend suites."],
        ["happy-dom", "20.14+", "DOM Simulation", "Lightweight web browser environment simulation for component tests."]
    ]
    format_table(fe_tbl, [1.4, 0.8, 1.4, 2.9], fe_headers, fe_data)

    # =========================================================================
    # 4. MULTI-AGENT PIPELINE (LANGGRAPH)
    # =========================================================================
    add_heading_1(doc, "4. Multi-Agent Pipeline & LangGraph Workflow")
    add_body(doc, "The intelligence core of AEMIIF is implemented as a deterministic Directed Acyclic Graph (DAG) using LangGraph. Each node represents a dedicated intelligent agent or algorithmic task that transforms the shared AEMIIFState.")
    
    agent_tbl = doc.add_table(rows=1, cols=4)
    agent_headers = ["Pipeline Node", "Executing Agent", "Inputs", "Outputs & Key Responsibilities"]
    agent_data = [
        ["Node 1: parse_requirements", "RequirementParserAgent", "User natural language query", "Extracts UserDecisionConfig: budget_limit, max_lead_time, min_service_level, requested_region, capacity_mode, objective weights."],
        ["Node 2: run_forecast", "ForecastAgent", "Historical sales data, Region", "Computes moving-average demand forecasts, trend growth, and expected consumption rates per store-product pair."],
        ["Node 3: run_inventory", "InventoryAgent", "Current stock, Safety stock", "Identifies safety stock shortfalls, reorder points, warehouse capacity limits, and urgent stockout vulnerabilities."],
        ["Node 4: run_supplier", "SupplierAgent", "Supplier catalog, Region", "Filters verified suppliers by regional eligibility, evaluates reliability scores, transit lead times, unit costs, and capacities."],
        ["Node 5: run_capacity_intel", "Capacity Intelligence", "Forecasts, Supplier capacities", "Aggregates total market capacity vs projected demand; flags potential supplier saturation or feasibility risks."],
        ["Node 6: run_milp", "MILP Optimization Agent", "OptimizationInput struct", "Builds PuLP mathematical model; solves multi-objective cost minimization problem; outputs optimal procurement plan."],
        ["Node 7: explain_result & finalize", "ExplanationAgent", "OptimizationResult, State", "Validates constraints, computes budget utilization, runs statistical paired t-test, generates executive explanation text."]
    ]
    format_table(agent_tbl, [1.5, 1.5, 1.5, 2.0], agent_headers, agent_data)
    
    doc.add_paragraph().paragraph_format.space_after = Pt(6)
    
    add_callout(doc, 
        "Deterministic Fallback Parser: When an OpenAI API key is not configured, AEMIIF automatically switches to an internal rule-based regex extraction engine. This ensures the platform functions flawlessly in air-gapped or offline demonstration environments without requiring external cloud LLM calls.",
        "RESILIENCE PATTERN")

    # =========================================================================
    # 5. MATHEMATICAL FORMULATION (OPERATIONS RESEARCH)
    # =========================================================================
    add_heading_1(doc, "5. Mathematical Formulation: Mixed Integer Linear Programming (MILP)")
    add_body(doc, "AEMIIF models multi-echelon procurement as a formal Mixed Integer Linear Program (MILP), guaranteeing optimal resource allocation while strictly respecting physical and fiscal constraints.")
    
    add_heading_2(doc, "Indices and Sets")
    add_bullet(doc, "Set of eligible suppliers.", "s in S: ")
    add_bullet(doc, "Set of inventory products.", "p in P: ")
    add_bullet(doc, "Set of retail stores or regional fulfillment hubs.", "k in K: ")
    
    add_heading_2(doc, "Decision Variables")
    add_bullet(doc, "Integer quantity of product p ordered from supplier s for store k.", "x_{s,p,k} >= 0: ")
    add_bullet(doc, "Binary indicator variable equal to 1 if supplier s is selected for product p at store k, and 0 otherwise.", "y_{s,p,k} in {0, 1}: ")
    
    add_heading_2(doc, "Multi-Factor Objective Function")
    add_body(doc, "The objective function minimizes the weighted linear combination of procurement cost, transportation cost, holding cost, and supplier unreliability penalty:")
    add_body(doc, "Minimize Z = w_1 * Cost_procurement + w_2 * Cost_transport + w_3 * Cost_holding + w_4 * Penalty_reliability")
    add_body(doc, "Where:")
    add_bullet(doc, "Cost_procurement = sum_{s,p,k} (unit_cost_{s,p} * x_{s,p,k})")
    add_bullet(doc, "Cost_transport = sum_{s,p,k} (distance_{s,k} * transit_rate * x_{s,p,k})")
    add_bullet(doc, "Cost_holding = sum_{s,p,k} (holding_rate * unit_cost_{s,p} * x_{s,p,k})")
    add_bullet(doc, "Penalty_reliability = sum_{s,p,k} ((1 - reliability_{s}) * penalty_weight * x_{s,p,k})")
    
    add_heading_2(doc, "Operational Constraints")
    add_bullet(doc, "For every product p and store k, total ordered units must satisfy forecasted demand plus safety stock requirements: sum_{s} x_{s,p,k} >= Net_Demand_{p,k}", "1. Demand Satisfaction: ")
    add_bullet(doc, "Total procurement expenditure must not exceed the executive budget limit: sum_{s,p,k} (unit_cost_{s,p} * x_{s,p,k}) <= Budget_Limit", "2. Fiscal Budget Constraint: ")
    add_bullet(doc, "Total units allocated to supplier s cannot exceed their declared manufacturing capacity: sum_{p,k} x_{s,p,k} <= Capacity_{s}", "3. Supplier Production Capacity: ")
    add_bullet(doc, "Selected suppliers must fulfill orders within the executive's maximum allowable delivery horizon: LeadTime_{s,p} <= Max_Lead_Time", "4. Maximum Lead Time Constraint: ")
    add_bullet(doc, "If supplier s is used (x_{s,p,k} > 0), orders must satisfy Minimum Order Quantity: MOQ_{s,p} * y_{s,p,k} <= x_{s,p,k} <= BigM * y_{s,p,k}", "5. Minimum Order Quantity (MOQ): ")

    # =========================================================================
    # 6. DATABASE ARCHITECTURE & SCHEMA
    # =========================================================================
    add_heading_1(doc, "6. Database Architecture & Data Model")
    add_body(doc, "The enterprise data tier is hosted on PostgreSQL (configured for Neon Cloud or local instances). It maintains four core relational tables populated with rich enterprise supply chain data.")
    
    db_tbl = doc.add_table(rows=1, cols=4)
    db_headers = ["Table Name", "Row Count", "Primary Key", "Key Attributes & Purpose"]
    db_data = [
        ["sales_history", "29,200 records", "transaction_id (SERIAL)", "date, store_id, product_id, units_sold, unit_price, total_revenue. Tracks historical multi-store daily sales over 365+ days."],
        ["inventory", "80 records", "inventory_id (SERIAL)", "region, store_id, product_id, current_stock, reserved_stock, incoming_quantity, safety_stock, storage_capacity. Real-time warehouse ledger."],
        ["suppliers", "200 records", "supplier_id (VARCHAR)", "supplier_name, product_id, region, unit_cost, lead_time_days, reliability_score, production_capacity, distance_km. Vendor performance index."],
        ["procurement_decisions", "Audit log", "plan_id (VARCHAR)", "request_id, region, total_cost, budget_limit, status, approval_status, approved_by, approved_at, decision_payload (JSONB). Audit log."]
    ]
    format_table(db_tbl, [1.4, 1.1, 1.4, 2.6], db_headers, db_data)
    
    doc.add_paragraph().paragraph_format.space_after = Pt(6)
    
    add_callout(doc, 
        "Pre-Seeded Regional Ledger: The database is pre-seeded with 4 distinct regional distribution zones: Chennai-North, Chennai-Central, Chennai-South, and Chennai-West. Each region includes distinct stores, products, and localized supplier options.",
        "DATABASE STATUS")

    # =========================================================================
    # 7. FRONTEND USER EXPERIENCE & PAGE-BY-PAGE GUIDE
    # =========================================================================
    add_heading_1(doc, "7. Frontend User Experience: 7-Page Executive Suite")
    add_body(doc, "The React 19 Single Page Application (SPA) provides an intuitive, executive-grade dashboard designed for supply chain officers and procurement directors.")
    
    page_tbl = doc.add_table(rows=1, cols=3)
    page_headers = ["Page & Route", "Interactive Features & Inputs", "Outputs & Key Visualizations"]
    page_data = [
        ["Page 1: Executive Overview\nRoute: /", "Region selector dropdown, optional CSV upload buttons, natural language prompt input, 'Run Optimization' trigger.", "Top KPI summary cards, budget utilization meter, dynamic procurement order table with quantities, suppliers, and unit costs."],
        ["Page 2: Optimization Analytics\nRoute: /analytics", "Automatic visualization of the current optimization plan.", "Clean interactive Recharts Pie/Donut chart breaking down Procurement (99%), Holding, Transport (1%), and Stockout costs formatted in Indian Rupees (₹)."],
        ["Page 3: Constraint Validation\nRoute: /constraints", "Automated real-time inspection of mathematical solver certificates.", "Global constraint verification table displaying green PASS badges for Budget, Lead Time, Service Level, and Capacity constraints."],
        ["Page 4: Capacity & Suppliers\nRoute: /capacity", "Supplier allocation viewer.", "Vendor-level production capacity utilization progress bars, total ordered units, and capacity safety margins."],
        ["Page 5: Hypothesis Testing\nRoute: /hypothesis", "Automated statistical testing trigger and Retry button.", "Displays Paired T-Test statistical metrics: Null Hypothesis (H0), Alternative Hypothesis (H1), Sample size (n), t-statistic, p-value (< 0.05), and savings verdict."],
        ["Page 6: Requirements & Provenance\nRoute: /requirements", "Inspection of parsed query.", "Natural language audit trail displaying original user text, parsed budget (e.g. ₹200,000), max lead time (5 days), service level (95%), and objective weights."],
        ["Page 7: Decision Approval\nRoute: /approval", "'Approve Plan' and 'Reject Plan' action buttons.", "Human-in-the-loop executive signoff interface that updates approval status from PENDING_APPROVAL to APPROVED and persists audit records to PostgreSQL."]
    ]
    format_table(page_tbl, [1.6, 2.2, 2.7], page_headers, page_data)
    
    doc.add_paragraph().paragraph_format.space_after = Pt(6)
    
    add_heading_2(doc, "Secondary Streamlit Dashboard (Port 8501)")
    add_body(doc, "In addition to the React executive application, the project includes an interactive Streamlit application (app.py) designed for operational supply chain engineers. It enables interactive parametric scenario exploration, real-time demand distribution histograms, and rapid CSV dataset testing.")

    # =========================================================================
    # 8. STATISTICAL HYPOTHESIS TESTING ENGINE
    # =========================================================================
    add_heading_1(doc, "8. Statistical Significance Engine: Paired T-Test")
    add_body(doc, "A critical differentiator of AEMIIF is that it does not simply assert cost savings—it mathematically and statistically proves them.")
    add_body(doc, "During the optimization pipeline execution, the hypothesis engine evaluates:")
    add_bullet(doc, "The optimized procurement plan does NOT significantly reduce unit procurement cost compared to baseline supplier market averages.", "Null Hypothesis (H0): ")
    add_bullet(doc, "The optimized procurement plan significantly reduces unit procurement cost compared to baseline supplier market averages.", "Alternative Hypothesis (H1): ")
    add_body(doc, "For every line item in the procurement plan, the engine computes:")
    add_bullet(doc, "C_{baseline} = Mean(Unit_Cost_{eligible_suppliers}) * Quantity")
    add_bullet(doc, "C_{optimized} = Unit_Cost_{selected_supplier} * Quantity")
    add_body(doc, "A paired two-sample t-test is performed via scipy.stats.ttest_rel(C_{baseline}, C_{optimized}). If the calculated p-value is strictly less than alpha = 0.05 and the t-statistic is positive, the system rejects H0, confirming statistically significant cost savings with 95% confidence.")

    # =========================================================================
    # 9. TESTING, QUALITY ASSURANCE & VERIFICATION
    # =========================================================================
    add_heading_1(doc, "9. Quality Assurance & Automated Test Coverage")
    add_body(doc, "The codebase has been verified with comprehensive end-to-end automated testing across all system layers.")
    
    test_tbl = doc.add_table(rows=1, cols=4)
    test_headers = ["Test Suite", "Test Engine", "Scope / Targets", "Current Status"]
    test_data = [
        ["Backend Unit Tests", "pytest (v9.1)", "Agent logic, parser regex, capacity intelligence, MILP formulation, validation.", "108 / 108 PASSED (100%)"],
        ["Backend API Tests", "pytest + httpx", "FastAPI routers (/optimization/run, /regions, /analytics, /health).", "ALL PASSED"],
        ["Database Tests", "pytest + psycopg2", "Connection pooling, schema migration, transaction rollbacks.", "ALL PASSED"],
        ["Frontend Unit Tests", "Vitest + Happy-DOM", "React component rendering, store state mutations, user events.", "ALL PASSED"],
        ["Frontend Linting", "Oxlint (Rust linter)", "Static analysis across 24 TypeScript and TSX component files.", "0 ERRORS, 0 WARNINGS"],
        ["Production Build", "Vite + Rollup", "TypeScript compilation and production bundle tree-shaking.", "BUILT CLEANLY (508ms)"]
    ]
    format_table(test_tbl, [1.5, 1.3, 2.3, 1.4], test_headers, test_data)

    # =========================================================================
    # 10. OPERATIONAL GUIDE: EXECUTION & LAUNCHERS
    # =========================================================================
    add_heading_1(doc, "10. Operational Guide & Launcher Scripts")
    add_body(doc, "AEMIIF includes robust, one-click Windows launcher scripts that handle environment discovery, dependency checks, port allocation, and browser redirection without terminal crashes.")
    
    add_heading_2(doc, "Available Launcher Scripts")
    add_bullet(doc, "Double-click this batch script to automatically check Python, check Node.js, install missing frontend packages, launch FastAPI on port 8000, launch React on port 5173, launch Streamlit on port 8501, and open both application interfaces in your default browser.", "start_project.bat (or run_all.bat): ")
    add_bullet(doc, "Gracefully terminates all active Python, Uvicorn, Streamlit, and Node.js Vite processes.", "stop_project.bat: ")
    
    add_heading_2(doc, "Network Port Allocations")
    add_bullet(doc, "FastAPI REST API & Swagger UI (http://localhost:8000/docs)", "Port 8000: ")
    add_bullet(doc, "React 19 Executive Optimization Dashboard", "Port 5173: ")
    add_bullet(doc, "Streamlit Decision Intelligence Demonstration Interface", "Port 8501: ")
    add_bullet(doc, "PostgreSQL Database Connection (Neon Cloud or Localhost)", "Port 5432: ")

    # =========================================================================
    # 11. PROJECT DIRECTORY TREE
    # =========================================================================
    add_heading_1(doc, "11. Project Codebase & Directory Structure")
    add_body(doc, "The repository is organized following clean architectural patterns separating agents, backend services, frontend presentation, datasets, and test suites:")
    
    dir_structure = """AI SMART INVENTORY/
|-- aemiif/                          # Agentic Explainable Multi-Agent Intelligence Core
|   |-- agents.py                    # ForecastAgent, InventoryAgent, SupplierAgent implementations
|   |-- capacity_intelligence.py     # Supplier capacity evaluation and bottleneck detection
|   |-- explanation_agent.py         # Natural language XAI rationale and summary generator
|   |-- graph.py                     # LangGraph StateGraph pipeline, DAG nodes, and fallback parser
|   |-- mcp_tools.py                 # Tool integrations and data access adapters
|   |-- optimization.py              # PuLP Mixed Integer Linear Programming (MILP) solver model
|   |-- parser_agent.py              # Natural language requirement parser (OpenAI / Regex)
|   |-- schemas.py                   # Pydantic state models (AEMIIFState, UserParameters, etc.)
|   `-- validation.py                # Post-optimization constraint verification certificates
|-- backend/                         # FastAPI Microservices Backend
|   |-- routers/                     # REST API routers (optimization, analytics, regions, approval)
|   |-- schemas/                     # Canonical API response and request DTO schemas
|   |-- services/                    # Business logic (aemiif_runner, mapper, hypothesis, database)
|   `-- main.py                      # FastAPI application entry point, middleware, CORS
|-- frontend/                        # React 19 + TypeScript Executive Dashboard
|   |-- src/
|   |   |-- api/                     # Axios API client functions and backend endpoints
|   |   |-- components/              # Reusable UI components (OptimizationPanel, Layout, Nav)
|   |   |-- pages/                   # 7 Specialized Page Components:
|   |   |   |-- ExecutiveOverview/   # Main optimizer, data ingestion, KPI cards, plan table
|   |   |   |-- OptimizationAnalytics/# Cost breakdown Recharts pie chart and metrics
|   |   |   |-- ConstraintValidation/# Budget, lead time, service level, capacity check table
|   |   |   |-- CapacitySuppliers/   # Vendor production capacity and utilization bars
|   |   |   |-- HypothesisTesting/   # Statistical Paired T-Test results and p-value display
|   |   |   |-- RequirementsProvenance/# Query audit, parsed parameters, objective weights
|   |   |   `-- DecisionApproval/    # Executive sign-off interface (Approve/Reject)
|   |   |-- store/                   # Zustand centralized reactive state store (useStore.ts)
|   |   `-- utils/                   # Currency formatters, calculation helpers
|   |-- package.json                 # Frontend dependencies (React 19, Vite, Recharts, etc.)
|   `-- vite.config.ts               # Vite configuration and build settings
|-- data/                            # Enterprise Datasets
|   |-- sales_history.csv            # 29,200 historical sales transactions across retail stores
|   |-- inventory.csv                # 80 store inventory ledger records across 4 regions
|   `-- suppliers.csv                # 200 supplier catalog options with costs and reliability
|-- tests/                           # Automated Test Suites (108 Pytest Tests)
|   |-- test_agents.py               # Unit tests for multi-agent logic
|   |-- test_optimization.py         # PuLP MILP solver constraint verification
|   |-- test_capacity.py             # Capacity intelligence bottleneck tests
|   `-- backend/test_api.py          # FastAPI endpoint integration tests
|-- app.py                           # Streamlit Phase 5 Demonstration Dashboard
|-- database.py                      # PostgreSQL connection pool and migration scripts
|-- requirements.txt                 # Backend Python package requirements
|-- start_project.bat                # One-click launcher for FastAPI, React, and Streamlit
|-- run_all.bat                      # Mirror launcher script
`-- stop_project.bat                 # Process termination script"""
    
    p_code = doc.add_paragraph()
    p_code.paragraph_format.space_before = Pt(4)
    p_code.paragraph_format.space_after = Pt(12)
    r_code = p_code.add_run(dir_structure)
    r_code.font.name = "Consolas"
    r_code.font.size = Pt(8.5)
    r_code.font.color.rgb = RGBColor(30, 41, 59)

    # =========================================================================
    # SAVE DOCUMENT
    # =========================================================================
    doc.save(output_path)
    print(f"Document successfully created at: {output_path}")

if __name__ == "__main__":
    out_1 = r"c:\Final Year project\AI SMART INVENTORY erth\AI SMART INVENTORY erth\AI SMART INVENTORY\project summary.docx"
    out_2 = r"c:\Final Year project\AI SMART INVENTORY erth\AI SMART INVENTORY erth\project summary.docx"
    
    build_project_summary_docx(out_1)
    build_project_summary_docx(out_2)
