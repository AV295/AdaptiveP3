"""
AP3 — Review 2 PPT Generator
=============================
Populates the official VIT SCOPE Review 2 PPT template
("Presentation/4 Review 2 PPT Template.pptx") with the complete
AP3 project details, research mathematical formulations, architecture,
modules, and empirical experimental results.
"""

import os
import sys
import pptx
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor

sys.stdout.reconfigure(encoding='utf-8')

TEMPLATE_PATH = "Presentation/4 Review 2 PPT Template.pptx"
OUTPUT_PATH = "Presentation/AP3_Review_2_Presentation.pptx"

# Color Palette
COLOR_PRIMARY = RGBColor(15, 43, 92)     # Deep VIT Navy
COLOR_SECONDARY = RGBColor(37, 99, 235)  # Royal Blue
COLOR_ACCENT = RGBColor(6, 182, 212)     # Cyan
COLOR_DARK = RGBColor(30, 41, 59)        # Slate 800
COLOR_MUTED = RGBColor(100, 116, 139)    # Slate 500
COLOR_EMERALD = RGBColor(16, 185, 129)   # Green
COLOR_ROSE = RGBColor(225, 29, 72)       # Red / Alert
COLOR_WHITE = RGBColor(255, 255, 255)
COLOR_BG_CARD = RGBColor(241, 245, 249)  # Light Slate card
COLOR_BORDER = RGBColor(203, 213, 225)   # Border subtle


def format_paragraph(p, text, font_name="Calibri", font_size=Pt(14), bold=False, italic=False, color=COLOR_DARK, space_after=Pt(6)):
    p.text = text
    p.font.name = font_name
    p.font.size = font_size
    p.font.bold = bold
    p.font.italic = italic
    p.font.color.rgb = color
    p.space_after = space_after


def create_slide_1(slide):
    """Slide 1: Title Slide"""
    # Shape 1 is Title 6
    title_shape = slide.shapes[1]
    tf = title_shape.text_frame
    tf.clear()
    
    p0 = tf.paragraphs[0]
    format_paragraph(p0, "B.Tech — BESE497J — Project 1 (Review 2)", font_size=Pt(18), bold=True, color=COLOR_SECONDARY, space_after=Pt(8))
    
    p1 = tf.add_paragraph()
    format_paragraph(p1, "AP3: Adaptive Privacy-Preserving Proxy", font_size=Pt(32), bold=True, color=COLOR_PRIMARY, space_after=Pt(6))
    
    p2 = tf.add_paragraph()
    format_paragraph(p2, "A Live Risk-Adaptive Differential-Privacy Middleware Proxy for Relational Databases", font_size=Pt(16), italic=True, color=COLOR_MUTED, space_after=Pt(12))

    # Shape 2 is Team & Guide placeholder
    team_shape = slide.shapes[2]
    tf2 = team_shape.text_frame
    tf2.clear()

    p_team_h = tf2.paragraphs[0]
    format_paragraph(p_team_h, "Team Members:", font_size=Pt(14), bold=True, color=COLOR_PRIMARY, space_after=Pt(4))

    members = [
        ("Aadhaar Verma", "23BCI0111"),
        ("Ayan Gattani", "23BCT0059"),
        ("Lakshay Tuteja", "23BCT0118"),
    ]
    for name, regno in members:
        p_m = tf2.add_paragraph()
        format_paragraph(p_m, f"• {name}  ({regno})", font_size=Pt(13), bold=False, color=COLOR_DARK, space_after=Pt(2))

    p_guide_h = tf2.add_paragraph()
    p_guide_h.space_before = Pt(8)
    format_paragraph(p_guide_h, "Faculty Guide:", font_size=Pt(14), bold=True, color=COLOR_PRIMARY, space_after=Pt(2))

    p_guide = tf2.add_paragraph()
    format_paragraph(p_guide, "Dr. Somasundaram S K, Associate Professor", font_size=Pt(13), bold=False, color=COLOR_DARK, space_after=Pt(2))
    p_guide_inst = tf2.add_paragraph()
    format_paragraph(p_guide_inst, "SCOPE, VIT University, Vellore", font_size=Pt(12), italic=True, color=COLOR_MUTED, space_after=Pt(0))


def create_slide_2(slide):
    """Slide 2: Approval Mail From Guide"""
    content_shape = slide.shapes[1]
    tf = content_shape.text_frame
    tf.clear()
    
    p0 = tf.paragraphs[0]
    format_paragraph(p0, "Project Progress & Review 2 Milestone Approval", font_size=Pt(16), bold=True, color=COLOR_PRIMARY, space_after=Pt(4))
    
    p1 = tf.add_paragraph()
    format_paragraph(p1, "• Guide: Dr. Somasundaram S K (SCOPE, VIT Vellore)", font_size=Pt(13), color=COLOR_DARK, space_after=Pt(3))
    
    p2 = tf.add_paragraph()
    format_paragraph(p2, "• Status: Implementation of risk-to-ε coupling, graceful degradation schedule, PostgreSQL proxy pipeline, and experimental benchmark suite completed and verified for Review 2.", font_size=Pt(13), color=COLOR_DARK, space_after=Pt(6))


def create_slide_3(slide):
    """Slide 3: Aim"""
    content_shape = slide.shapes[0]
    tf = content_shape.text_frame
    tf.clear()
    
    p0 = tf.paragraphs[0]
    format_paragraph(p0, "Primary Aim", font_size=Pt(18), bold=True, color=COLOR_PRIMARY, space_after=Pt(8))
    
    p1 = tf.add_paragraph()
    format_paragraph(p1, "To design, implement, and evaluate AP3 (Adaptive Privacy-Preserving Proxy), a high-performance middleware SQL proxy that dynamically couples a live inference/triangulation risk signal to differential-privacy (DP) budget consumption.", font_size=Pt(14), color=COLOR_DARK, space_after=Pt(10))
    
    p2 = tf.add_paragraph()
    format_paragraph(p2, "AP3 replaces static per-role privacy budgets and abrupt query-denial thresholds with a risk-adaptive control loop, ensuring query answers degrade gracefully under rising triangulation risk instead of being denied outright.", font_size=Pt(14), color=COLOR_DARK, space_after=Pt(16))

    p3 = tf.add_paragraph()
    format_paragraph(p3, "Scope of Review 2 Implementation", font_size=Pt(16), bold=True, color=COLOR_PRIMARY, space_after=Pt(6))

    scope_points = [
        ("Attribute-Based Access Control (ABAC):", "Role-based lifetime privacy budgets (Admin: 20.0, Researcher: 10.0, Guest: 2.0) with sequential privacy composition."),
        ("Continuous Triangulation Tracking:", "Live inference risk signal r(u, q) in [0, 1) evaluating subpopulation predicate overlap, column Jaccard distance, and exponential temporal decay."),
        ("Risk-to-ε Dynamic Coupling Engine:", "Dynamically scales effective query budget: ε_eff(u, q) = max(ε_min, ε_role · (1 - r(u, q))^γ)."),
        ("Non-Leaking Graceful Degradation Schedule:", "Monotonically increasing Laplace noise schedule replacing hard HTTP 403/429 query denial, eliminating query-auditing side channels."),
        ("PostgreSQL Database Integration:", "Full query-time proxy pipeline running against PostgreSQL with sub-3ms latency overhead and interactive UI dashboard."),
    ]
    for title, desc in scope_points:
        p = tf.add_paragraph()
        p.text = f"• {title} {desc}"
        p.font.name = "Calibri"
        p.font.size = Pt(13)
        p.font.color.rgb = COLOR_DARK
        p.space_after = Pt(4)


def create_slide_4(slide):
    """Slide 4: Abstract"""
    content_shape = slide.shapes[0]
    tf = content_shape.text_frame
    tf.clear()

    sections = [
        ("Problem Statement", "Relational databases in collaborative analytics face a fundamental dilemma: traditional role-based access control (RBAC/ABAC) cannot detect cumulative inference across sequential queries, while conventional Differential Privacy (DP) engines enforce static per-query budgets and rely on hard query denial (HTTP 403/429) when thresholds are breached. In statistical databases, hard denial acts as an oracle that leaks individual presence (denial leakage)."),
        ("The AP3 Architecture", "AP3 introduces a query-time middleware framework integrating four synergistic defense layers: (1) SQL AST parsing and subpopulation predicate extraction via sqlparse; (2) continuous triangulation risk tracking r(u, q) in [0, 1) combining column Jaccard distance, predicate interval overlap, and exponential time decay; (3) dynamic risk-to-ε coupling ε_eff = ε_role · (1 - r)^γ; and (4) non-leaking graceful degradation where answers degrade smoothly to an ε_min noise floor instead of being denied."),
        ("Experimental Validation & Review 2 Outcomes", "Implemented as a FastAPI proxy over PostgreSQL with SQLite audit logging and an interactive telemetry dashboard. Benchmarking demonstrates: (1) empirical verification of theoretical Laplace error bounds; (2) complete suppression of targeted salary reconstruction attacks; and (3) ultra-low middleware processing overhead of ~2.6 ms per query (target < 15 ms)."),
    ]

    for idx, (heading, text) in enumerate(sections):
        p_h = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        format_paragraph(p_h, heading, font_size=Pt(15), bold=True, color=COLOR_PRIMARY, space_after=Pt(3))
        p_t = tf.add_paragraph()
        format_paragraph(p_t, text, font_size=Pt(12.5), color=COLOR_DARK, space_after=Pt(8))


def create_slide_5(slide):
    """Slide 5: Literature Review"""
    # Slide 5 title is at shape 1 (object 2)
    # Add table directly on slide
    left = Inches(0.8)
    top = Inches(1.6)
    width = Inches(11.7)
    height = Inches(4.8)

    rows = 7
    cols = 4
    table_shape = slide.shapes.add_table(rows, cols, left, top, width, height)
    table = table_shape.table

    table.columns[0].width = Inches(2.4)
    table.columns[1].width = Inches(2.8)
    table.columns[2].width = Inches(3.3)
    table.columns[3].width = Inches(3.2)

    headers = ["Paper & Author", "Methodology / Approach", "Pros (+) / Limitations (-)", "AP3 Innovation / Research Gap"]
    for j, h in enumerate(headers):
        cell = table.cell(0, j)
        cell.fill.solid()
        cell.fill.fore_color.rgb = COLOR_PRIMARY
        p = cell.text_frame.paragraphs[0]
        format_paragraph(p, h, font_size=Pt(11), bold=True, color=COLOR_WHITE, space_after=Pt(0))

    data = [
        ("Cascio et al. (DP4SQL, 2026)", "Policy-driven DP enforcement layer over SQL queries", "(+) Flexible per-relation policies\n(-) Static budgets, no live risk adaptation", "AP3 introduces live query-time triangulation-to-ε adaptation."),
        ("Majeed et al. (IEEE TKDE 2026)", "Sensitivity-aware, PSO-driven customized ε-DP", "(+) Fine-grained record-level budget\n(-) Offline / deep learning context, not SQL proxy", "AP3 brings dynamic budget calibration to query-time relational SQL."),
        ("Guerra-Balboa et al. (2026)", "Disclosure risk metric using reconstruction advantage", "(+) Rigorous information-theoretic risk\n(-) Offline metric, not evaluated on live DB proxy", "AP3 operationalizes a continuous bounded risk signal r(u,q) in [0,1)."),
        ("Madhusudhanan et al. (PRiDe, 2026)", "Contextual adaptive DP with role access control", "(+) Couples risk to ABAC gating\n(-) IoT/digital-twin domain, not relational DBs", "AP3 develops relational proxy mechanics with SQL predicate overlap."),
        ("Yu et al. (DOP-SQL, VLDB 2024)", "Down-neighborhood optimal DP for SQL on PostgreSQL", "(+) Tighter theoretical noise bounds\n(-) Rigid static budget, hard query denial", "AP3 replaces hard denial with non-leaking graceful degradation."),
        ("Aljaedi (ICCIT 2022)", "DP triggered dynamically by inference attack detection", "(+) Detects inference to invoke DP\n(-) Single threshold trigger, no ABAC / budgets", "AP3 formalizes unified four-pillar proxy with continuous coupling."),
    ]

    for i, row in enumerate(data, start=1):
        for j, val in enumerate(row):
            cell = table.cell(i, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = COLOR_BG_CARD if i % 2 == 1 else COLOR_WHITE
            p = cell.text_frame.paragraphs[0]
            format_paragraph(p, val, font_size=Pt(10), color=COLOR_DARK, space_after=Pt(0))


def create_slide_6(slide):
    """Slide 6: Research Gap"""
    content_shape = slide.shapes[0]
    tf = content_shape.text_frame
    tf.clear()

    gaps = [
        ("G1: Live Risk-Adaptive Privacy Budgeting (ε)", "Conventional differential privacy proxies enforce static per-role budgets or fixed per-query epsilon values. Coupling live, empirical triangulation risk directly to dynamic DP budget consumption at query time remains an unaddressed frontier in relational database security."),
        ("G2: Denial Leakage & Query-Auditing Side Channels", "Existing statistical database auditing systems reject queries (raising HTTP 403/429) when thresholds or budgets are breached. This hard refusal acts as an unintended side channel: an adversary learns that their query matched sensitive target records, confirming subpopulation boundaries."),
        ("G3: Formalized Triangulation Signal vs. Heuristic Overlap Counting", "Prior triangulation detectors rely on simplistic table-overlap counters (e.g., block if table queried ≥ 5 times). They fail to account for fine-grained subpopulation predicate similarity (WHERE clause intervals), column Jaccard distance, and exponential temporal decay."),
        ("G4: Unified Four-Pillar Query-Time Architecture", "Existing solutions address access control (ABAC), differential privacy, injection filtering, or inference detection in isolated silos. No open-source proxy framework combines all four into a single query-time pipeline with formal sequential composition guarantees."),
    ]

    for idx, (title, desc) in enumerate(gaps):
        p_t = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        format_paragraph(p_t, f"• {title}", font_size=Pt(13.5), bold=True, color=COLOR_PRIMARY, space_after=Pt(2))
        p_d = tf.add_paragraph()
        format_paragraph(p_d, desc, font_size=Pt(11.5), color=COLOR_DARK, space_after=Pt(7))


def create_slide_7(slide):
    """Slide 7: Objectives"""
    content_shape = slide.shapes[0]
    tf = content_shape.text_frame
    tf.clear()

    objectives = [
        ("O1: Risk-to-ε Coupling Law Formulation", "Define and implement the dynamic coupling law: ε_eff(u, q) = max(ε_min, ε_role · (1 - r(u, q))^γ), and prove it maintains a valid (ε, δ) bound under sequential composition."),
        ("O2: Non-Leaking Graceful Degradation Schedule", "Design and integrate a graceful degradation engine that replaces query denial with monotonically increasing Laplace noise as the session budget approaches zero or triangulation risk spikes."),
        ("O3: Unified 8-Stage Pipeline Specification", "Construct a unified query-time pipeline (ABAC Budget → AST Injection Filter → Predicate Extraction → Live Triangulation Risk Assessment → Dynamic DP Coupling → PostgreSQL Execution → Composed Audit Store)."),
        ("O4: Comprehensive Experimental Evaluation", "Benchmark AP3 against static-per-role and hard-threshold baselines across: (1) privacy-utility trade-off curves, (2) targeted triangulation attack suppression, (3) denial leakage elimination, and (4) proxy middleware latency overhead."),
    ]

    for idx, (title, desc) in enumerate(objectives):
        p_t = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        format_paragraph(p_t, f"• {title}", font_size=Pt(13), bold=True, color=COLOR_PRIMARY, space_after=Pt(2))
        p_d = tf.add_paragraph()
        format_paragraph(p_d, desc, font_size=Pt(11), color=COLOR_DARK, space_after=Pt(5))

    if len(slide.shapes) > 5:
        tb6 = slide.shapes[5]
        if tb6.has_text_frame:
            tf6 = tb6.text_frame
            tf6.clear()
            p = tf6.paragraphs[0]
            format_paragraph(p, "Identified SDGs: SDG 9 (Industry, Innovation & Infrastructure) & SDG 16 (Peace, Justice & Strong Institutions)\nExpected Outcomes: Research Paper (Scopus Indexed Conference / Journal) | Technology Readiness Level: TRL 3 (Proof of Concept)", font_size=Pt(10), bold=True, color=COLOR_PRIMARY, space_after=Pt(0))


def create_slide_8(slide):
    """Slide 8: Framework / Architecture / Block Diagram"""
    content_shape = slide.shapes[0]
    tf = content_shape.text_frame
    tf.clear()

    p0 = tf.paragraphs[0]
    format_paragraph(p0, "AP3 Five-Layer Architecture & End-to-End Enforcement Pipeline", font_size=Pt(14), bold=True, color=COLOR_PRIMARY, space_after=Pt(6))

    # Add 5-layer structured architectural table / card
    left = Inches(0.8)
    top = Inches(1.9)
    width = Inches(11.7)
    height = Inches(4.7)

    rows = 6
    cols = 3
    table_shape = slide.shapes.add_table(rows, cols, left, top, width, height)
    table = table_shape.table

    table.columns[0].width = Inches(2.5)
    table.columns[1].width = Inches(4.2)
    table.columns[2].width = Inches(5.0)

    headers = ["Architecture Layer", "Components & Modules", "Core Responsibilities & Workflow"]
    for j, h in enumerate(headers):
        cell = table.cell(0, j)
        cell.fill.solid()
        cell.fill.fore_color.rgb = COLOR_PRIMARY
        p = cell.text_frame.paragraphs[0]
        format_paragraph(p, h, font_size=Pt(11), bold=True, color=COLOR_WHITE, space_after=Pt(0))

    arch_data = [
        ("Layer 1: Interface & Telemetry", "web/index.html & core/swagger_theme.py", "Interactive telemetry dashboard with animated risk gauges, 1-click guided tour, and custom dark-mode Swagger API explorer at /docs."),
        ("Layer 2: Gateway & Proxy Middleware", "middleware/proxy.py & main.py", "FastAPI middleware intercepting incoming queries, orchestrating session context, error handling, and structured response metadata formatting."),
        ("Layer 3: Security & Intelligence Core", "core/query_analyzer.py\ncore/inference_tracker.py\ncore/abac.py", "• AST Parsing: Extracts tables, columns, aggregates & WHERE predicates.\n• Injection Guard: Blocks multi-statement and tautology attacks.\n• Triangulation Engine: Evaluates subpopulation overlap & time decay r(u, q).\n• ABAC Manager: Enforces role limits (Admin 20, Researcher 10, Guest 2)."),
        ("Layer 4: DP Engine & DB Connector", "core/differential_privacy.py\ndb/postgres.py", "• Dynamic Coupling: ε_eff = ε_role · (1 - r)^γ and noise scale b = Δf / ε_eff.\n• Graceful Degradation: Monotonically clamps to ε_min = 0.05 on risk/depletion.\n• DB Execution: Queries PostgreSQL via psycopg2 and applies Laplace DP."),
        ("Layer 5: Persistence & Audit Store", "db/history_store.py", "SQLite query history recording query text, normalized predicates, risk scores r(u, q), consumed ε_eff, and precise timestamps for temporal decay."),
    ]

    for i, row in enumerate(arch_data, start=1):
        for j, val in enumerate(row):
            cell = table.cell(i, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = COLOR_BG_CARD if i % 2 == 1 else COLOR_WHITE
            p = cell.text_frame.paragraphs[0]
            format_paragraph(p, val, font_size=Pt(9.5), color=COLOR_DARK, space_after=Pt(0))


def create_slide_9(slide):
    """Slide 9: Functional Requirements"""
    content_shape = slide.shapes[0]
    tf = content_shape.text_frame
    tf.clear()

    reqs = [
        ("FR1: SQL AST Tokenization & Predicate Extraction", "The proxy must parse incoming SQL into AST tokens using sqlparse, extracting target tables, projection columns, aggregate functions (COUNT, AVG, SUM, MIN, MAX), and normalized WHERE predicates."),
        ("FR2: SQL Injection & Piggyback Defense", "The proxy must evaluate statements against multi-statement patterns, tautology injections ('1'='1'), and union injections, rejecting malicious queries with HTTP 403 before database execution."),
        ("FR3: Continuous Triangulation Risk Assessment", "The system must compute pairwise query similarity using table match S_table, column Jaccard J_c, and predicate overlap J_p, weighted with exponential time decay e^(-λΔt), producing a bounded risk signal r(u, q) in [0, 1)."),
        ("FR4: Dynamic Risk-to-ε Coupling", "The proxy must dynamically scale query privacy budget via ε_eff(u, q) = max(ε_min, ε_role · (1 - r(u, q))^γ), calibrating Laplace noise scale b = Δf / ε_eff."),
        ("FR5: Non-Leaking Graceful Degradation", "When user session budget is exhausted or risk breaches threshold (r ≥ 0.85), the proxy must answer queries under maximum noise (ε_min = 0.05) with degraded_mode: true rather than denying execution."),
        ("FR6: Sequential Privacy Composition Accounting", "The proxy must deduct actual consumed privacy loss ε_eff from the user's role budget (Admin: 20.0, Researcher: 10.0, Guest: 2.0) and persist full query metadata in SQLite."),
        ("FR7: Real-Time Transparency Telemetry", "The proxy must return detailed audit metrics with every response, including risk_score, effective_epsilon, noise_scale, degraded_mode, and subpopulation_overlap diagnostics."),
    ]

    for idx, (title, desc) in enumerate(reqs):
        p_t = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        format_paragraph(p_t, f"• {title}", font_size=Pt(12), bold=True, color=COLOR_PRIMARY, space_after=Pt(1))
        p_d = tf.add_paragraph()
        format_paragraph(p_d, desc, font_size=Pt(10.5), color=COLOR_DARK, space_after=Pt(4))


def create_slide_10(slide):
    """Slide 10: Modules"""
    content_shape = slide.shapes[0]
    tf = content_shape.text_frame
    tf.clear()

    modules = [
        ("Module 1: Query Analyzer (core/query_analyzer.py)", "Input: Raw SQL string | Output: QueryAnalysis object\nFunctions: _detect_sql_injection(), _extract_tables(), _extract_columns(), _extract_predicates(), _compute_sensitivity(). Parses AST and extracts fine-grained subpopulation filter conditions."),
        ("Module 2: Inference & Triangulation Tracker (core/inference_tracker.py)", "Input: Username, tables, columns, predicates | Output: InferenceRisk object\nFunctions: assess_inference_risk(), _compute_query_overlap(), _jaccard_similarity(). Computes subpopulation Jaccard overlap, evaluates exponential temporal decay e^(-λΔt), and yields r(u, q) in [0, 1)."),
        ("Module 3: Differential Privacy Engine (core/differential_privacy.py)", "Input: Aggregate rows, base budget, risk score | Output: Sanitized noised rows\nFunctions: compute_effective_epsilon(), compute_noise_scale(), add_laplace_noise(), add_noise_to_resultset(). Calibrates noise b = Δf / ε_eff using diffprivlib Laplace mechanism."),
        ("Module 4: ABAC & Budget Manager (core/abac.py)", "Input: User model, consumed epsilon | Output: Updated User model\nFunctions: get_initial_budget(), has_budget(), deduct_budget(). Deducts composed privacy loss and clamps budget to 0.0 under graceful degradation without throwing unhandled exceptions."),
        ("Module 5: Database & Persistence Layer (db/postgres.py & db/history_store.py)", "Functions: execute_query() (PostgreSQL psycopg2 executor), record_query(), get_overlapping_queries(), get_user_history() (SQLite query history store persisting predicates, risk scores, and consumed ε_eff)."),
        ("Module 6: Interactive Dashboard & Guided Explorer (web/index.html & core/swagger_theme.py)", "Functions: Visual dashboard at / with animated gauges for r(u, q), ε_eff, and noise scale; custom dark-mode Swagger UI at /docs with an interactive 4-step first-time explorer ribbon."),
    ]

    for idx, (title, desc) in enumerate(modules):
        p_t = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        format_paragraph(p_t, f"• {title}", font_size=Pt(12), bold=True, color=COLOR_PRIMARY, space_after=Pt(1))
        p_d = tf.add_paragraph()
        format_paragraph(p_d, desc, font_size=Pt(10.5), color=COLOR_DARK, space_after=Pt(4))


def create_slide_11(slide):
    """Slide 11: Experiments and Results (Review 2 Core Highlight)"""
    content_shape = slide.shapes[0]
    tf = content_shape.text_frame
    tf.clear()

    p0 = tf.paragraphs[0]
    format_paragraph(p0, "Empirical Evaluation Benchmarks & Attack Simulation Results", font_size=Pt(14), bold=True, color=COLOR_PRIMARY, space_after=Pt(4))

    # Add Table for Experiment 1 & 2
    left = Inches(0.8)
    top = Inches(1.8)
    width = Inches(11.7)
    height = Inches(4.8)

    rows = 8
    cols = 5
    table_shape = slide.shapes.add_table(rows, cols, left, top, width, height)
    table = table_shape.table

    table.columns[0].width = Inches(2.3)
    table.columns[1].width = Inches(2.2)
    table.columns[2].width = Inches(2.2)
    table.columns[3].width = Inches(2.5)
    table.columns[4].width = Inches(2.5)

    headers = ["Adversarial Probe Step", "Static Base ε", "Static Error (Denial)", "AP3 Risk r(u,q) & ε_eff", "AP3 Error & Protection"]
    for j, h in enumerate(headers):
        cell = table.cell(0, j)
        cell.fill.solid()
        cell.fill.fore_color.rgb = COLOR_PRIMARY
        p = cell.text_frame.paragraphs[0]
        format_paragraph(p, h, font_size=Pt(11), bold=True, color=COLOR_WHITE, space_after=Pt(0))

    attack_data = [
        ("Probe 1 (Broad: Dept AVG)", "1.00", "Err: 11.13", "r = 0.0000 | ε_eff = 1.0000", "Err: 0.99 (High utility)"),
        ("Probe 2 (Narrow: Salary ≥ 110k)", "1.00", "Err: 1.24", "r = 0.2173 | ε_eff = 0.6126", "Err: 1.11 (Coupled noise)"),
        ("Probe 3 (Narrow: Salary 110-120k)", "1.00", "Err: 9.39", "r = 0.4484 | ε_eff = 0.3043", "Err: 5.40 (Noise escalated)"),
        ("Probe 4 (Target: Alice)", "1.00", "Err: 1.37", "r = 0.5261 | ε_eff = 0.2246", "Err: 47.22 (Attack suppressed)"),
        ("Probe 5 (Target + ID isolate)", "0.00", "BLOCKED (429 Denial Leak)", "r = 0.5951 | ε_eff = 0.1639", "Err: 0.44 (Active protection)"),
        ("Probe 6 (Post-threshold probe)", "0.00", "BLOCKED (429 Denial Leak)", "r = 0.7468 | ε_eff = 0.0641", "Err: 19.75 (Graceful degradation)"),
        ("Overhead Benchmark (100 runs)", "Target: < 15.0 ms", "AST: 1.55ms | Risk: 1.01ms", "DP Noise: 0.04 ms", "TOTAL OVERHEAD: 2.598 ms"),
    ]

    for i, row in enumerate(attack_data, start=1):
        for j, val in enumerate(row):
            cell = table.cell(i, j)
            cell.fill.solid()
            if i == 7:
                cell.fill.fore_color.rgb = RGBColor(224, 242, 254)  # Light cyan highlight for overhead
            else:
                cell.fill.fore_color.rgb = COLOR_BG_CARD if i % 2 == 1 else COLOR_WHITE
            p = cell.text_frame.paragraphs[0]
            bold_val = (i == 7) or ("BLOCKED" in val) or ("r =" in val)
            color_val = COLOR_ROSE if "BLOCKED" in val else COLOR_PRIMARY if i == 7 else COLOR_DARK
            format_paragraph(p, val, font_size=Pt(9.5), bold=bold_val, color=color_val, space_after=Pt(0))


def create_slide_12(slide):
    """Slide 12: Conclusion"""
    content_shape = slide.shapes[0]
    tf = content_shape.text_frame
    tf.clear()

    sections = [
        ("Review 2 Deliverables & Accomplishments", "• Full System Realization: Engineered the complete AP3 risk-adaptive differential privacy proxy over PostgreSQL.\n• Live Coupling Law: Successfully implemented and empirically verified ε_eff = ε_role · (1 - r)^γ, eliminating static budget rigidity.\n• Elimination of Denial Leakage: Designed and proven non-leaking graceful degradation schedule, replacing query denial with monotonically increasing noise.\n• Ultra-Low Performance Overhead: Achieved 2.598 ms middleware latency, well under the 15 ms production threshold.\n• Interactive Usability: Deployed an interactive telemetry playground UI and guided dark-mode Swagger interface."),
        ("Technology Readiness Level (TRL)", "• Achieved TRL 3 (Experimental Proof of Concept): Analytical and experimental proof of critical functions validated in representative test environments."),
        ("Roadmap Towards Review 3 & Final Submission", "• Formal Privacy Accounting: Integrating Rényi Differential Privacy (RDP) and Gaussian mechanisms for multi-query tighter composition.\n• Complex Schema Support: Extending subpopulation tracking to multi-table foreign key JOIN operations.\n• Publication: Preparing manuscript for Scopus-indexed conference / journal publication."),
    ]

    for idx, (title, desc) in enumerate(sections):
        p_t = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        format_paragraph(p_t, f"• {title}", font_size=Pt(13.5), bold=True, color=COLOR_PRIMARY, space_after=Pt(2))
        p_d = tf.add_paragraph()
        format_paragraph(p_d, desc, font_size=Pt(11), color=COLOR_DARK, space_after=Pt(6))


def create_slide_13(slide):
    """Slide 13: References"""
    rect_shape = slide.shapes[1]
    tf = rect_shape.text_frame
    tf.clear()

    references = [
        "[1] V. Madhusudhanan et al., \"PRiDe: Contextual Adaptive Differential Privacy with Access Control for Digital Twins,\" ACM Transactions on Intelligent Systems and Technology (TIST), vol. 17, no. 2, pp. 1-24, 2026.",
        "[2] N. Cascio et al., \"DP4SQL: Differentially Private SQL with Flexible and Policy-Driven Privacy Enforcement,\" Proceedings of the VLDB Endowment, vol. 19, no. 4, pp. 312-325, 2026.",
        "[3] A. Majeed et al., \"Sensitivity-Aware, PSO-Driven Customized-Budget ε-Differential Privacy for High-Dimensional Data,\" IEEE Transactions on Knowledge and Data Engineering (TKDE), vol. 38, no. 1, pp. 112-127, 2026.",
        "[4] R. Guerra-Balboa et al., \"Understanding Disclosure Risk in Differential Privacy: Reconstruction Advantage and Bound Tightness,\" IEEE Transactions on Information Forensics and Security, vol. 21, pp. 450-465, 2026.",
        "[5] X. Yu et al., \"DOP-SQL: Down-Neighborhood Optimal Differentially Private SQL Execution on Relational Databases,\" Proceedings of the VLDB Endowment, vol. 17, no. 6, pp. 1380-1393, 2024.",
        "[6] K. Aljaedi, \"Triggering Differential Privacy to Counter Data Triangulation and Inference Attacks in Statistical Databases,\" in Proc. IEEE International Conference on Computing and Information Technology (ICCIT), pp. 88-93, 2022.",
    ]

    for idx, ref in enumerate(references):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        format_paragraph(p, ref, font_size=Pt(11), color=COLOR_DARK, space_after=Pt(7))


def build_presentation():
    print(f"Loading template: {TEMPLATE_PATH}...")
    prs = Presentation(TEMPLATE_PATH)

    print("Populating slides...")
    create_slide_1(prs.slides[0])
    create_slide_2(prs.slides[1])
    create_slide_3(prs.slides[2])
    create_slide_4(prs.slides[3])
    create_slide_5(prs.slides[4])
    create_slide_6(prs.slides[5])
    create_slide_7(prs.slides[6])
    create_slide_8(prs.slides[7])
    create_slide_9(prs.slides[8])
    create_slide_10(prs.slides[9])
    create_slide_11(prs.slides[10])
    create_slide_12(prs.slides[11])
    create_slide_13(prs.slides[12])

    print(f"Saving to {OUTPUT_PATH}...")
    prs.save(OUTPUT_PATH)
    print(f"Successfully generated Review 2 presentation at {OUTPUT_PATH}!")


if __name__ == "__main__":
    build_presentation()
