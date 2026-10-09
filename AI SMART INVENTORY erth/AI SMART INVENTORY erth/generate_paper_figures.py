"""
Publication-Quality Figure Generator for AEMIIF Research Paper (IEEE Conference Format).
Generates:
1. architecture.png (Fig. 1: AEMIIF Overall Logical Architecture)
2. safety_boundary.png (Fig. 2: Safety Boundary and Post-Solver Validation)
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

# Matplotlib configuration for publication standard
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['mathtext.fontset'] = 'dejavusans'

def create_architecture_figure(output_paths):
    fig, ax = plt.subplots(figsize=(9.2, 15.6), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 185)
    ax.axis('off')

    # Semantic Colors
    c_user_bg = "#EFF6FF"
    c_user_border = "#2563EB"
    c_user_hdr = "#1D4ED8"
    
    c_agent_bg = "#F0FDF4"
    c_agent_border = "#16A34A"
    c_agent_hdr = "#15803D"
    
    c_cap_bg = "#FFFBEB"
    c_cap_border = "#D97706"
    c_cap_hdr = "#B45309"
    
    c_milp_bg = "#F5F3FF"
    c_milp_border = "#7C3AED"
    c_milp_hdr = "#6D28D9"
    
    c_valid_bg = "#ECFDF5"
    c_valid_border = "#059669"
    c_valid_hdr = "#047857"
    
    c_db_bg = "#F8FAFC"
    c_db_border = "#475569"
    c_db_hdr = "#334155"

    def draw_card(x, y, w, h, bg, border, hdr_bg, title, lines, title_size=9.4, text_size=7.6, align='center'):
        bbox = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.0,rounding_size=1.5",
                              facecolor=bg, edgecolor=border, linewidth=1.8, zorder=2)
        ax.add_patch(bbox)
        
        header_h = 4.2
        header_y = y + h - header_h
        rect_cover = patches.Rectangle((x, header_y), w, header_h,
                                       facecolor=hdr_bg, edgecolor="none", zorder=3)
        ax.add_patch(rect_cover)
        header_clip = FancyBboxPatch((x, y + h - header_h - 1.0), w, header_h + 1.0,
                                     boxstyle="round,pad=0.0,rounding_size=1.5",
                                     facecolor=hdr_bg, edgecolor="none", zorder=3)
        ax.add_patch(header_clip)
        rect_cover2 = patches.Rectangle((x, header_y), w, header_h,
                                        facecolor=hdr_bg, edgecolor="none", zorder=3)
        ax.add_patch(rect_cover2)

        ax.text(x + w / 2, y + h - 2.2, title, fontsize=title_size, fontweight='bold',
                color='white', ha='center', va='center', zorder=4)
        
        line_start_y = y + h - header_h - 2.8
        for i, line in enumerate(lines):
            cur_y = line_start_y - (i * 2.45)
            if align == 'center':
                ax.text(x + w / 2, cur_y, line, fontsize=text_size,
                        color="#0F172A", ha='center', va='center', zorder=4)
            else:
                ax.text(x + 3.0, cur_y, line, fontsize=text_size,
                        color="#0F172A", ha='left', va='center', zorder=4)

    def draw_arrow(x1, y1, x2, y2, color="#334155", style="-|>", lw=1.6, zorder=3, dashed=False):
        ls = '--' if dashed else '-'
        arrow = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style,
                                mutation_scale=13, linewidth=lw, color=color,
                                linestyle=ls, zorder=zorder)
        ax.add_patch(arrow)

    # ==================== MAIN HEADER ====================
    ax.text(50, 181.0, "AEMIIF Overall Logical Architecture",
            fontsize=14.0, fontweight='bold', color="#0F172A", ha='center', va='center')
    ax.text(50, 177.5, "Bounded Multi-Agent Orchestration Coupled with Deterministic Operations Research",
            fontsize=9.0, color="#475569", ha='center', va='center')

    # ==================== LAYER 1: USER / UI ====================
    draw_card(12, 155, 76, 17, c_user_bg, c_user_border, c_user_hdr,
              "1. Executive Directives & Client Interface Tier",
              ["• Unstructured Natural Language Directives (Budget, Region, Lead Time, Service Level)",
               "• Dual Frontend: Production 7-Page React 19 Executive Suite & Operational Streamlit UI",
               "• Human-in-the-Loop Governance: Executive Review, Parameter Steering & Approval"],
              align='left', text_size=7.8)

    draw_arrow(50, 155, 50, 147)

    # ==================== LAYER 2: REQUIREMENT PARSER ====================
    draw_card(12, 130, 76, 17, c_user_bg, c_user_border, c_user_hdr,
              "2. Requirement Parser Agent (LangGraph Root Node)",
              ["• Semantic Intent & Entity Extraction with Deterministic Regex Fallback Engine",
               "• Zero Cloud Lock-in: Converts Qualitative Priorities into Normalized Objective Weights",
               r"• Mathematical Mapping: $\sum_{k=1}^K w_k = 1.0, \quad w_k \geq 0$ (Procurement, Transport, Reliability)"],
              align='left', text_size=7.8)

    # Forking arrows from Parser to 3 Domain Agents
    draw_arrow(50, 130, 20, 121)
    draw_arrow(50, 130, 50, 121)
    draw_arrow(50, 130, 80, 121)

    # ==================== LAYER 3: PARALLEL OPERATIONAL AGENTS ====================
    # Forecast Agent
    draw_card(5, 93, 28, 27, c_agent_bg, c_agent_border, c_agent_hdr,
              "Forecast Agent",
              ["• MCP Data Access Layer",
               "• Historical Transaction Ledger",
               "• 7-Day Cyclical Demand Model:",
               r"   $\hat{D}_{pk}^{t+1} = \frac{1}{M}\sum_{m=0}^{M-1} D_{pk}^{t-m}$",
               "• Multi-Horizon Point Estimates",
               "• Outputs Demand Mean & Variance"],
              align='left', text_size=7.3)

    # Inventory Agent
    draw_card(36, 93, 28, 27, c_agent_bg, c_agent_border, c_agent_hdr,
              "Inventory Agent",
              [r"• On-Hand Stock Balances $I_{pk}$",
               r"• Incoming Pipeline Orders $I_{pk}^{\mathrm{in}}$",
               r"• Dynamic Safety Stock $SS_{pk}$",
               "• Net Replenishment Shortfall:",
               r"   $Q_{\mathrm{req}} = \max(0, \hat{D}+SS-I-I^{\mathrm{in}})$",
               "• Evaluates Stockout Vulnerability"],
              align='left', text_size=7.3)

    # Supplier Agent
    draw_card(67, 93, 28, 27, c_agent_bg, c_agent_border, c_agent_hdr,
              "Supplier Agent",
              ["• Catalog Retrieval (200 Vendors)",
               r"• Hard Filter: $\mathrm{LeadTime} \leq \mathrm{LT}_{\max}$",
               r"• Hard Filter: $\mathrm{Distance} \leq \mathrm{Dist}_{\max}$",
               r"• Vendor Unit Costs $c_{sp}$, Reliability $r_s$",
               r"• Minimum Order Quantities & Capacity $C_s$",
               "• Prunes Ineligible Candidate Suppliers"],
              align='left', text_size=7.3)

    # Converging arrows to Capacity Intelligence
    draw_arrow(19, 93, 44, 85)
    draw_arrow(50, 93, 50, 85)
    draw_arrow(81, 93, 56, 85)

    # ==================== LAYER 4: CAPACITY INTELLIGENCE ====================
    draw_card(10, 65, 80, 20, c_cap_bg, c_cap_border, c_cap_hdr,
              "3. Capacity Intelligence Pre-Solver Layer",
              [r"• STRICT_HARD_CAP Mode: Early Infeasibility Detection (If $\sum_{i=1}^N C_i < Q_{\mathrm{req}} \rightarrow$ INFEASIBLE)",
               r"• PROPORTIONAL Mode: Candidate Dimension Reduction ($C_i \geq Q_{\mathrm{req}}/N$ Proportional Gate)",
               "• Algorithmic Pre-Filter: Proactively Eliminates Unfeasible Search Subspaces Prior to Solver Invocation",
               "• Compute Latency Optimization: Prevents Solver Starvation without Altering Mathematical Optimality"],
              align='left', text_size=7.8)

    draw_arrow(50, 65, 50, 58)

    # ==================== LAYER 5: DETERMINISTIC MILP OPTIMIZER ====================
    draw_card(8, 36, 84, 22, c_milp_bg, c_milp_border, c_milp_hdr,
              "4. Deterministic Operations Research Engine (MILP Solver)",
              ["• Mixed-Integer Linear Program Formulated in PuLP; Solved via COIN-OR CBC Branch-and-Cut",
               r"• Objective Function: $\min Z = w_{\mathrm{proc}} C_{\mathrm{proc}} + w_{\mathrm{trans}} C_{\mathrm{trans}} + w_{\mathrm{hold}} C_{\mathrm{hold}} + w_{\mathrm{rel}} \Omega_{\mathrm{rel}}$",
               r"• Hard Operational Constraints: $\sum_s x_{spk} \geq Q_{\mathrm{req}}$ (Demand), $\mathrm{TotalCost} \leq B$ (Budget), $x \geq \mathrm{MOQ} \cdot y$, $\sum x \leq C_s$",
               r"• Strict Mathematical Integrality: $x_{spk} \in \mathbf{Z}_{\geq 0}$ (Procurement Allocation), $y_{spk} \in \{0, 1\}$ (Vendor Selection)",
               "• Formal Proof of Optimality: Proven Mathematical Minimum with Absolute Zero Arithmetic Hallucination"],
              align='left', text_size=7.6)

    draw_arrow(50, 36, 50, 29)

    # ==================== LAYER 6: POST-SOLVER VALIDATION & XAI ====================
    draw_card(8, 12, 84, 18, c_valid_bg, c_valid_border, c_valid_hdr,
              "5. Post-Solver Safety Boundary, Statistical Significance & XAI",
              ["• Independent Validation Safety Boundary: 100% Physical Constraint Cross-Verification across All Rules",
               r"• Automated Statistical Engine: Paired Two-Sample $t$-test ($t = -2.84, \quad p = 0.0102 < 0.05$ vs. Baseline Rates)",
               "• Explanation Agent (XAI): Grounded Multi-Objective Trade-Off Rationale for Enterprise Decision-Makers",
               "• Human Decision Signoff: Executive Approval / Rejection Logged to Immutable PostgreSQL JSONB Audit Trail"],
              align='left', text_size=7.6)

    # ==================== FOUNDATION: ENTERPRISE DATA TIER (MCP) ====================
    draw_card(6, 0.5, 88, 10, c_db_bg, c_db_border, c_db_hdr,
              "Enterprise Persistence Tier: PostgreSQL & Model Context Protocol (MCP)",
              ["29,200 Sales Transactions | 80 Multi-Echelon Stores across 4 Chennai Industrial Zones | 200 Suppliers | 20 SKUs",
               "Parameterized MCP Tool Layer: Strictly Decouples Agent Analytical Reasoning from Database Persistence"],
              align='center', title_size=8.8, text_size=7.4)

    # Bi-directional dashed data links from MCP/DB to agents
    draw_arrow(6.5, 10.5, 6.5, 98, color="#0284C7", style="<->", lw=1.8, dashed=True)
    ax.text(3.5, 55, "MCP Data Access Layer\n(Parameterized Secure Tool Calls)", fontsize=7.2, color="#0369A1",
            fontweight='bold', rotation=90, ha='center', va='center')

    for path in output_paths:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        fig.savefig(path, dpi=300, bbox_inches='tight')
        print(f"Saved: {path}")
    plt.close(fig)


def create_safety_boundary_figure(output_paths):
    fig, ax = plt.subplots(figsize=(9.2, 12.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 135)
    ax.axis('off')

    c_blue_bg = "#EFF6FF"
    c_blue_border = "#2563EB"
    c_blue_hdr = "#1D4ED8"
    
    c_audit_bg = "#F8FAFC"
    c_audit_border = "#475569"
    c_audit_hdr = "#334155"
    
    c_pass_bg = "#ECFDF5"
    c_pass_border = "#16A34A"
    c_pass_hdr = "#15803D"
    
    c_fail_bg = "#FEF2F2"
    c_fail_border = "#DC2626"
    c_fail_hdr = "#B91C1C"

    def draw_card(x, y, w, h, bg, border, hdr_bg, title, lines, title_size=9.4, text_size=7.8, align='center'):
        bbox = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.0,rounding_size=1.5",
                              facecolor=bg, edgecolor=border, linewidth=1.8, zorder=2)
        ax.add_patch(bbox)
        
        header_h = 4.2
        header_y = y + h - header_h
        rect_cover = patches.Rectangle((x, header_y), w, header_h,
                                       facecolor=hdr_bg, edgecolor="none", zorder=3)
        ax.add_patch(rect_cover)
        header_clip = FancyBboxPatch((x, y + h - header_h - 1.0), w, header_h + 1.0,
                                     boxstyle="round,pad=0.0,rounding_size=1.5",
                                     facecolor=hdr_bg, edgecolor="none", zorder=3)
        ax.add_patch(header_clip)
        rect_cover2 = patches.Rectangle((x, header_y), w, header_h,
                                        facecolor=hdr_bg, edgecolor="none", zorder=3)
        ax.add_patch(rect_cover2)

        ax.text(x + w / 2, y + h - 2.2, title, fontsize=title_size, fontweight='bold',
                color='white', ha='center', va='center', zorder=4)
        
        line_start_y = y + h - header_h - 2.8
        for i, line in enumerate(lines):
            cur_y = line_start_y - (i * 2.4)
            if align == 'center':
                ax.text(x + w / 2, cur_y, line, fontsize=text_size,
                        color="#0F172A", ha='center', va='center', zorder=4)
            else:
                ax.text(x + 3.0, cur_y, line, fontsize=text_size,
                        color="#0F172A", ha='left', va='center', zorder=4)

    def draw_arrow(x1, y1, x2, y2, color="#334155", style="-|>", lw=1.8, zorder=3, dashed=False):
        ls = '--' if dashed else '-'
        arrow = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style,
                                mutation_scale=13, linewidth=lw, color=color,
                                linestyle=ls, zorder=zorder)
        ax.add_patch(arrow)

    # Diagram Title
    ax.text(50, 131.5, "Independent Post-Solver Safety Boundary",
            fontsize=14.0, fontweight='bold', color="#0F172A", ha='center', va='center')
    ax.text(50, 128.0, "Autonomous Multi-Rule Verification Protocol Protecting Business Operations",
            fontsize=9.0, color="#475569", ha='center', va='center')

    # ==================== INPUT: MILP SOLUTION ====================
    draw_card(12, 111, 76, 14, c_blue_bg, c_blue_border, c_blue_hdr,
              "Input Candidate Procurement Plan (MILP Solver Result)",
              [r"• Primary Decision Variables: $x_{spk}^* \in \mathbf{Z}_{\geq 0}$ (Procurement Quantities), $y_{spk}^* \in \{0, 1\}$ (Contracted Vendors)",
               r"• Computed Outlay: $\mathrm{TotalCost} = C_{\mathrm{proc}} + C_{\mathrm{trans}} + C_{\mathrm{hold}}$ across All Fulfillment Zones"],
              align='left', text_size=7.8)

    draw_arrow(50, 111, 50, 104)

    # ==================== SAFETY BOUNDARY VALIDATOR ====================
    draw_card(8, 64, 84, 40, c_audit_bg, c_audit_border, c_audit_hdr,
              "Independent Constraint Validation Engine (Multi-Rule Audit Matrix)",
              ["Autonomous Multi-Rule Verification Matrix Executed Prior to Executive Commitment:",
               r"• Rule 1 [Capital Budget Ceiling]: $\mathrm{TotalCost} \leq B$ (Strict Fiscal Protection Guarantee)",
               r"• Rule 2 [Customer Demand Guarantee]: $\sum_s x_{spk} \geq Q_{\mathrm{req}}(p, k)$ (100% Minimum Service Level Guarantee)",
               r"• Rule 3 [Supplier Capacity Ceilings]: $\sum_{p,k} x_{spk} \leq C_s \quad \forall s \in S$ (Vendor Production Limits)",
               r"• Rule 4 [Minimum Order Quantities]: $x_{spk} \geq \mathrm{MOQ}_{sp} \cdot y_{spk}$ (Contractual Batch Size Adherence)",
               r"• Rule 5 [Lead Time Threshold]: $\mathrm{LeadTime}_{sp} \cdot y_{spk} \leq \mathrm{LeadTime}_{\max}$ (Temporal Delivery SLA)",
               r"• Rule 6 [Fulfillment Distance]: $d_{sk} \cdot y_{spk} \leq \mathrm{Distance}_{\max}$ (Regional Transportation Radius)",
               r"• Rule 7 [Integer Feasibility]: $x_{spk} \in \mathbf{Z}_{\geq 0}, \quad y_{spk} \in \{0, 1\}$ (Exact Discreteness Check)"],
              align='left', title_size=9.8, text_size=8.0)

    draw_arrow(50, 64, 50, 56)

    # ==================== DECISION DIAMOND ====================
    diamond = patches.Polygon([[50, 56], [68, 46.5], [50, 37], [32, 46.5]],
                              closed=True, facecolor="#FEF3C7", edgecolor="#D97706",
                              linewidth=2.0, zorder=3)
    ax.add_patch(diamond)
    ax.text(50, 48.0, "Are All Constraints", fontsize=8.8, fontweight='bold', color="#92400E", ha='center', va='center', zorder=4)
    ax.text(50, 44.8, "100% Satisfied?", fontsize=8.8, fontweight='bold', color="#92400E", ha='center', va='center', zorder=4)

    # PASS Branch (Left)
    draw_arrow(32, 46.5, 23, 46.5, color="#16A34A", lw=2.2)
    draw_arrow(23, 46.5, 23, 36, color="#16A34A", lw=2.2)
    ax.text(27, 49.0, "PASS", fontsize=9.5, fontweight='bold', color="#16A34A", ha='center', zorder=5)

    # FAIL Branch (Right)
    draw_arrow(68, 46.5, 77, 46.5, color="#DC2626", lw=2.2)
    draw_arrow(77, 46.5, 77, 36, color="#DC2626", lw=2.2)
    ax.text(73, 49.0, "FAIL", fontsize=9.5, fontweight='bold', color="#DC2626", ha='center', zorder=5)

    # ==================== PASS BRANCH ====================
    draw_card(4, 2, 43, 34, c_pass_bg, c_pass_border, c_pass_hdr,
              "Verified Plan Authorization & Governance",
              ["Audit Status: VERIFIED & COMPLIANT",
               "────────────────────────────────────────",
               "1. Statistical Significance Engine:",
               r"   Paired $t$-test: $t = -2.84, \quad p = 0.0102 < 0.05$",
               "   Statistically Significant Procurement Savings",
               "2. Explanation Agent (Grounded XAI):",
               "   Synthesizes Mathematical Trade-Off Rationale",
               "3. Human Executive Signoff:",
               "   Interactive Approval via 7-Page React 19 UI",
               "4. Enterprise Ledger Commitment:",
               "   Recorded to PostgreSQL JSONB Audit Trail"],
              align='left', title_size=8.6, text_size=7.2)

    # ==================== FAIL BRANCH ====================
    draw_card(53, 2, 43, 34, c_fail_bg, c_fail_border, c_fail_hdr,
              "Execution Rejection & Diagnostic Alert",
              ["Audit Status: CONSTRAINT BREACH DETECTED",
               "────────────────────────────────────────",
               "1. Anti-Hallucination Safe State:",
               "   Immediate Procurement Dispatch Halt",
               "2. Structured Diagnostic Certificate:",
               "   Pinpoints Specific Mathematical Violation",
               "   (e.g., BUDGET_OVERRUN, CAPACITY_BREACH)",
               "3. Executive Failure Report:",
               "   Flagged with Actionable Warnings in UI",
               "4. Root-Cause Remediation:",
               "   Prompts Adjustment of Budget / Lead-Time"],
              align='left', title_size=8.6, text_size=7.2)

    for path in output_paths:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        fig.savefig(path, dpi=300, bbox_inches='tight')
        print(f"Saved: {path}")
    plt.close(fig)


if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sub_dir = os.path.join(base_dir, "AI SMART INVENTORY")

    arch_targets = [
        os.path.join(base_dir, "architecture.png"),
        os.path.join(sub_dir, "architecture.png")
    ]
    
    safety_targets = [
        os.path.join(base_dir, "safety_boundary.png"),
        os.path.join(sub_dir, "safety_boundary.png")
    ]

    print("Regenerating Figure 1: Architecture Diagram with enhanced vertical spacing...")
    create_architecture_figure(arch_targets)

    print("Regenerating Figure 2: Safety Boundary Diagram with enhanced vertical spacing...")
    create_safety_boundary_figure(safety_targets)

    print("Done! Both diagrams rendered at 300 DPI.")
