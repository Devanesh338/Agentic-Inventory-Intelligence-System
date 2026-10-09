"""
AEMIIF — Agentic Explainable Multi-Agent Inventory Intelligence Framework
Decision Intelligence & Demonstration Dashboard (Phase 5)

Run with:
    streamlit run app.py
    (or: streamlit run app.py --server.port 8502)
"""

import sys
import os
import time
from typing import Dict, Any, Optional, Tuple

import streamlit as st
import pandas as pd
import plotly.express as px
from scipy import stats
from database import save_procurement_decision, get_procurement_decision
from aemiif.schemas import ApprovalStatus

from backend.services.ingestion_service import clean_duplicate_columns as backend_clean
from backend.services.ingestion_service import preprocess_dataframe as backend_preprocess

def clean_duplicate_columns(df: pd.DataFrame) -> bool:
    success, warnings, errors = backend_clean(df)
    for w in warnings:
        st.warning(w)
    for e in errors:
        st.error(e)
    return success

def preprocess_dataframe(df: pd.DataFrame, dataset_name: str = "Dataset") -> pd.DataFrame:
    cleaned, successes, warnings = backend_preprocess(df, dataset_name)
    for w in warnings:
        st.warning(w)
    for s in successes:
        st.success(s)
    return cleaned

# Add project root to sys.path
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from aemiif.graph import build_aemiif_graph
from aemiif.schemas import (
    FinalAEMIIFResponse,
    CapacityMode,
    CapacityStatus,
    UserParameters,
    ObjectiveWeights,
    UserDecisionConfig,
    InventoryOutput,
    SupplierOption
)
from aemiif.parser_agent import LLMParsedResult, ParsedPreferences, PreferenceLevel


# ============================================================
# CORE WORKFLOW RUNNER (Single Source of Truth)
# ============================================================

def run_aemiif_pipeline(
    query: str,
    region: str,
    product_id: Optional[str] = None,
    store_id: Optional[str] = None,
    preset_name: Optional[str] = None
) -> Tuple[FinalAEMIIFResponse, Dict[str, Any]]:
    """
    Executes the AEMIIF LangGraph workflow and returns the structured
    FinalAEMIIFResponse along with the full workflow state dictionary.
    """
    # Build compiled LangGraph workflow
    graph = build_aemiif_graph()

    # Initial state: pass explicit region and optional filters
    initial_state: Dict[str, Any] = {
        "user_query": query,
        "region": region,
        "region_source": "user_selected" if region else "Prototype default",
        "dataset_source": "user_uploaded" if region else "Prototype default",
    }
    if product_id:
        initial_state["product_id"] = product_id
        initial_state["product_source"] = "User specified"
    if store_id:
        initial_state["store_id"] = store_id
        initial_state["store_source"] = "User specified"

    # Handle preset-specific deterministic setups
    if preset_name == "Preset 1: Standard Optimal Replenishment":
        if not os.getenv("OPENAI_API_KEY"):
            initial_state["mock_llm_result"] = LLMParsedResult(
                parameters=UserParameters(
                    budget=100000.0,
                    max_lead_time_days=5,
                    min_service_level=0.95
                ),
                preferences=ParsedPreferences(
                    purchase_cost=PreferenceLevel.VERY_HIGH,
                    supplier_reliability=PreferenceLevel.HIGH
                )
            )

    elif preset_name == "Preset 2: Strict Capacity Infeasible":
        config = UserDecisionConfig(
            parameters=UserParameters(
                capacity_mode=CapacityMode.STRICT_HARD_CAP,
                budget=500000.0,
                max_lead_time_days=10
            ),
            weights=ObjectiveWeights(),
            original_user_request=query
        )
        inv = InventoryOutput(
            region=region,
            product_id=product_id or "P006",
            store_id=store_id or "ST002",
            current_stock=0,
            incoming_quantity=0,
            forecast_demand=360,
            projected_stock=-360,
            safety_stock=0,
            inventory_position=0,
            replenishment_requirement=360,
            risk_level="HIGH"
        )
        suppliers = [
            SupplierOption(
                supplier_id=f"SUP_CAP_{i}",
                region=region,
                product_id=product_id or "P006",
                unit_cost=50.0,
                moq=10,
                lead_time_days=2,
                reliability=0.99,
                capacity=40,
                feasibility_status="feasible"
            )
            for i in range(1, 5)
        ]
        initial_state["user_config"] = config
        initial_state["inventory_outputs"] = [inv]
        initial_state["supplier_outputs"] = suppliers

    elif preset_name == "Preset 3: Proportional Capacity Mode":
        config = UserDecisionConfig(
            parameters=UserParameters(
                capacity_mode=CapacityMode.PROPORTIONAL,
                budget=500000.0,
                max_lead_time_days=10
            ),
            weights=ObjectiveWeights(),
            original_user_request=query
        )
        inv = InventoryOutput(
            region=region,
            product_id=product_id or "P006",
            store_id=store_id or "ST002",
            current_stock=0,
            incoming_quantity=0,
            forecast_demand=360,
            projected_stock=-360,
            safety_stock=0,
            inventory_position=0,
            replenishment_requirement=360,
            risk_level="HIGH"
        )
        suppliers = [
            SupplierOption(supplier_id="SUP_A", region=region, product_id=product_id or "P006", unit_cost=45.0, moq=20, lead_time_days=2, reliability=0.99, capacity=40, feasibility_status="feasible"),
            SupplierOption(supplier_id="SUP_B", region=region, product_id=product_id or "P006", unit_cost=50.0, moq=20, lead_time_days=3, reliability=0.98, capacity=100, feasibility_status="feasible"),
            SupplierOption(supplier_id="SUP_C", region=region, product_id=product_id or "P006", unit_cost=52.0, moq=20, lead_time_days=2, reliability=0.99, capacity=120, feasibility_status="feasible"),
            SupplierOption(supplier_id="SUP_D", region=region, product_id=product_id or "P006", unit_cost=48.0, moq=20, lead_time_days=4, reliability=0.95, capacity=200, feasibility_status="feasible"),
        ]
        initial_state["user_config"] = config
        initial_state["inventory_outputs"] = [inv]
        initial_state["supplier_outputs"] = suppliers

    elif preset_name == "Preset 4: Infeasible Budget Constraint":
        if not os.getenv("OPENAI_API_KEY"):
            initial_state["mock_llm_result"] = LLMParsedResult(
                parameters=UserParameters(
                    budget=500.0,
                    max_lead_time_days=5,
                    min_service_level=0.95
                ),
                preferences=ParsedPreferences()
            )

    elif preset_name == "Preset 5: Lead Time Infeasible":
        if not os.getenv("OPENAI_API_KEY"):
            initial_state["mock_llm_result"] = LLMParsedResult(
                parameters=UserParameters(
                    budget=100000.0,
                    max_lead_time_days=1,
                    min_service_level=0.95
                ),
                preferences=ParsedPreferences()
            )

    # Invoke the LangGraph workflow
    result_state = graph.invoke(initial_state)
    final_response = result_state.get("final_response")

    if not final_response:
        final_response = FinalAEMIIFResponse(
            request_id=result_state.get("request_id", "req_err"),
            status=result_state.get("status", "ERROR"),
            summary="Workflow halted before finalization.",
            explanation=result_state.get("explanation", "An unexpected workflow halt occurred."),
            errors=result_state.get("errors", ["Pipeline did not produce FinalAEMIIFResponse."])
        )

    return final_response, result_state


# ============================================================
# STREAMLIT UI CONFIGURATION & STYLING
# ============================================================

def setup_page():
    st.set_page_config(
        page_title="AEMIIF — Decision Intelligence Platform",
        page_icon="📦",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.markdown("""
        <style>
        .main-header {
            font-size: 2.1rem;
            font-weight: 800;
            margin-bottom: 0.2rem;
            color: #1E293B;
        }
        .sub-header {
            font-size: 1.05rem;
            color: #64748B;
            margin-bottom: 1rem;
        }
        .badge-bar {
            display: flex;
            gap: 0.6rem;
            flex-wrap: wrap;
            margin-bottom: 1.2rem;
        }
        .status-badge {
            background-color: #F1F5F9;
            border: 1px solid #CBD5E1;
            padding: 0.25rem 0.65rem;
            border-radius: 6px;
            font-size: 0.82rem;
            font-weight: 600;
            color: #334155;
        }
        .status-badge-green {
            background-color: #ECFDF5;
            border: 1px solid #A7F3D0;
            color: #065F46;
        }
        .status-badge-amber {
            background-color: #FFFBEB;
            border: 1px solid #FDE68A;
            color: #92400E;
        }
        .status-badge-red {
            background-color: #FEF2F2;
            border: 1px solid #FECACA;
            color: #991B1B;
        }
        .provenance-chip {
            display: inline-block;
            padding: 0.15rem 0.5rem;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        .prov-user {
            background-color: #EFF6FF;
            color: #1D4ED8;
            border: 1px solid #BFDBFE;
        }
        .prov-default {
            background-color: #F3F4F6;
            color: #4B5563;
            border: 1px solid #E5E7EB;
        }
        </style>
    """, unsafe_allow_html=True)


# ============================================================
# PHASE 2: REUSABLE DATA STRUCTURES & CALCULATIONS
# ============================================================

def calculate_before_after_metrics(state_dict, resp):
    """Calculates determinisitic before/after metrics for the Dashboard."""
    metrics = {
        "current_inventory": 0,
        "forecast_demand": 0,
        "current_stockout_risk_qty": 0,
        "num_at_risk_products": 0,
        "optimized_procurement_quantity": 0,
        "optimized_cost": 0.0,
        "expected_service_level": 0.0,
        "suppliers_selected": 0,
        "average_lead_time": 0.0,
        "capacity_utilization": 0.0,
        "num_capacity_constrained_suppliers": 0
    }
    
    # Current State KPIs
    inv_outputs = state_dict.get("inventory_outputs", [])
    for inv in inv_outputs:
        try:
            metrics["current_inventory"] += getattr(inv, "current_stock", 0) + getattr(inv, "incoming_quantity", 0)
            metrics["forecast_demand"] += getattr(inv, "forecast_demand", 0)
            if getattr(inv, "projected_stock", 0) < 0:
                metrics["current_stockout_risk_qty"] += abs(getattr(inv, "projected_stock", 0))
                metrics["num_at_risk_products"] += 1
        except Exception:
            if isinstance(inv, dict):
                metrics["current_inventory"] += inv.get("current_stock", 0) + inv.get("incoming_quantity", 0)
                metrics["forecast_demand"] += inv.get("forecast_demand", 0)
                if inv.get("projected_stock", 0) < 0:
                    metrics["current_stockout_risk_qty"] += abs(inv.get("projected_stock", 0))
                    metrics["num_at_risk_products"] += 1

    # Capacity bottlenecks
    cap_summary = resp.capacity_summary or {}
    metrics["num_capacity_constrained_suppliers"] = len(cap_summary.get("filtered_suppliers", []))

    # Optimized KPIs
    if resp.status in ["OPTIMAL", "FEASIBLE"] and resp.procurement_plan:
        plan = resp.procurement_plan
        metrics["optimized_procurement_quantity"] = sum(p.get("order_quantity", 0) for p in plan)
        metrics["optimized_cost"] = resp.cost_summary.get("total_cost", 0) if resp.cost_summary else 0
        
        suppliers = set(p.get("supplier_id") for p in plan if p.get("order_quantity", 0) > 0)
        metrics["suppliers_selected"] = len(suppliers)
        
        if len(plan) > 0:
            metrics["average_lead_time"] = sum(p.get("lead_time_days", 0) for p in plan) / len(plan)
            
        cap_util = sum(p.get("order_quantity", 0) for p in plan)
        total_cap = sum(p.get("capacity", 1) for p in plan)  # Avoid division by zero
        metrics["capacity_utilization"] = (cap_util / total_cap) * 100 if total_cap > 0 else 0.0

        sl = getattr(resp, "achieved_service_level", None)
        if sl is None:
            sl = state_dict.get("achieved_service_level")
        if sl is not None:
            metrics["expected_service_level"] = float(sl) * 100

    return metrics

def generate_decision_summary(metrics):
    """Generates a human-readable summary of the optimization impact."""
    lines = []
    
    if metrics["optimized_procurement_quantity"] > 0:
        lines.append(f"📦 **Procurement:** Recommends ordering {metrics['optimized_procurement_quantity']:,} units across {metrics['suppliers_selected']} supplier(s).")
    else:
        lines.append("📦 **Procurement:** No units recommended for order.")
        
    if metrics["current_stockout_risk_qty"] > 0:
        lines.append(f"⚠️ **Risk:** Addressed a forecasted stockout risk of {metrics['current_stockout_risk_qty']:,} units.")
    else:
        lines.append("✅ **Risk:** Inventory levels were healthy; optimizing for cost and safety stock.")
        
    if metrics["optimized_cost"] > 0:
        lines.append(f"💰 **Cost:** Total optimized landed cost is INR {metrics['optimized_cost']:,.2f}.")
        
    if metrics["expected_service_level"] > 0:
        lines.append(f"📈 **Service:** Expected service level is {metrics['expected_service_level']:.1f}%.")
        
    if metrics["capacity_utilization"] > 0:
        lines.append(f"🏭 **Capacity:** Average supplier capacity utilization is {metrics['capacity_utilization']:.1f}%.")
        
    return lines


# ============================================================
# MAIN STREAMLIT APP
# ============================================================

def main():
    setup_page()

    PRESET_QUERIES = {
        "Preset 1: Standard Optimal Replenishment": (
            "Replenish the inventory under a budget of 100000. "
            "Suppliers should deliver within 5 days. "
            "Maintain at least 95 percent service level. "
            "Cost is very important and supplier reliability is also important."
        ),
        "Preset 2: Strict Capacity Infeasible": (
            "Replenish inventory with strict_hard_cap capacity mode under a budget of 500000. "
            "Demand requirement exceeds individual supplier capacity. "
            "Suppliers should deliver within 10 days."
        ),
        "Preset 3: Proportional Capacity Mode": (
            "Replenish inventory with proportional capacity mode under a budget of 500000. "
            "Maintain at least 95 percent service level. "
            "Suppliers should deliver within 10 days."
        ),
        "Preset 4: Infeasible Budget Constraint": (
            "Replenish the inventory under a budget of 500. "
            "Suppliers should deliver within 5 days. "
            "Maintain at least 95 percent service level."
        ),
        "Preset 5: Lead Time Infeasible": (
            "Replenish the inventory under a budget of 100000. "
            "Suppliers must deliver within 1 day. "
            "Maintain at least 95 percent service level."
        ),
        "Custom Interactive Request": ""
    }

    # Session State Initialization & Synchronization
    if "current_preset" not in st.session_state:
        st.session_state["current_preset"] = "Preset 1: Standard Optimal Replenishment"
        st.session_state["user_query_input"] = PRESET_QUERIES[st.session_state["current_preset"]]
    if "aemiif_result" not in st.session_state:
        st.session_state["aemiif_result"] = None
    if "aemiif_state" not in st.session_state:
        st.session_state["aemiif_state"] = None

    if "plan_id" not in st.session_state:
        st.session_state["plan_id"] = None
    if "plan_approval_status" not in st.session_state:
        st.session_state["plan_approval_status"] = "NOT_GENERATED" # NOT_GENERATED, PENDING, APPROVED, REJECTED
    if "plan_rejection_reason" not in st.session_state:
        st.session_state["plan_rejection_reason"] = None


    def on_preset_change():
        selected = st.session_state.get("preset_selector")
        if selected in PRESET_QUERIES:
            st.session_state["user_query_input"] = PRESET_QUERIES[selected]
            st.session_state["aemiif_result"] = None
            st.session_state["aemiif_state"] = None
            st.session_state["plan_id"] = None
            st.session_state["plan_approval_status"] = "NOT_GENERATED"
            st.session_state["plan_rejection_reason"] = None

    # ============================================================
    # SIDEBAR CONTROLS
    # ============================================================
    with st.sidebar:
        st.markdown("### 📤 Dataset Ingestion")
        
        uploaded_sales = st.file_uploader("Upload sales_history.csv", type=["csv"])
        uploaded_inv = st.file_uploader("Upload inventory.csv", type=["csv"])
        uploaded_sup = st.file_uploader("Upload suppliers.csv", type=["csv"])
        
        from aemiif.validation_ingestion import validate_sales, validate_inventory, validate_suppliers, validate_cross_dataset
        
        all_valid = False
        df_sales = df_inv = df_sup = None
        
        if uploaded_sales and uploaded_inv and uploaded_sup:
            try:
                uploaded_sales.seek(0)
                uploaded_inv.seek(0)
                uploaded_sup.seek(0)
                df_sales = pd.read_csv(uploaded_sales)
                df_inv = pd.read_csv(uploaded_inv)
                df_sup = pd.read_csv(uploaded_sup)

                # ============================================================
                # PREPROCESSING LAYER
                # ============================================================

                with st.expander("🧹 Dataset Preprocessing", expanded=True):

                    st.write("Cleaning uploaded datasets before validation...")

                    df_sales = preprocess_dataframe(
                        df_sales,
                        "Sales History"
                    )

                    df_inv = preprocess_dataframe(
                        df_inv,
                        "Inventory"
                    )

                    df_sup = preprocess_dataframe(
                        df_sup,
                        "Suppliers"
                    )

                    st.success(
                        "✅ Dataset preprocessing completed successfully."
                    )

                # ============================================================
                # VALIDATION AFTER PREPROCESSING
                # ============================================================

                sales_ok, sales_errs = validate_sales(df_sales)

                inv_ok, inv_errs = validate_inventory(df_inv)

                sup_ok, sup_errs = validate_suppliers(df_sup)
                st.markdown("#### Validation Status")
                
                def render_status(name, df, ok, errs):
                    if ok:
                        st.success(f"**{name}**: ✓ {len(df)} rows, {len(df.columns)} cols")
                    else:
                        st.error(f"**{name}**: ✗ {errs[0] if errs else 'Invalid'}")
                        if len(errs) > 1:
                            st.caption(f"+ {len(errs)-1} more errors")
                
                render_status("Sales History", df_sales, sales_ok, sales_errs)
                render_status("Inventory", df_inv, inv_ok, inv_errs)
                render_status("Suppliers", df_sup, sup_ok, sup_errs)
                
                if sales_ok and inv_ok and sup_ok:
                    cross_ok, cross_errs = validate_cross_dataset(df_sales, df_inv, df_sup)
                    if cross_ok:
                        st.success("✓ Cross-dataset validation passed.")
                        all_valid = True
                    else:
                        st.error(f"✗ Cross-dataset error: {cross_errs[0]}")
                        if len(cross_errs) > 1:
                            st.caption(f"+ {len(cross_errs)-1} more errors")
            except Exception as e:
                st.error(f"Error parsing CSVs: {e}")
                
        if st.button(
            "Ingest Datasets",
            width="stretch",
            disabled=not all_valid
        ):
        
            if all_valid:
        
                with st.spinner(
                    "Ingesting cleaned datasets to PostgreSQL..."
                ):
        
                    try:
        
                        from scripts.seed_database import (
                            initialize_schema,
                            ingest_dataframe
                        )
        
                        # --------------------------------------------
                        # Initialize PostgreSQL schema
                        # --------------------------------------------
                        initialize_schema()
        
                        # --------------------------------------------
                        # Insert CLEANED datasets
                        # --------------------------------------------
                        ingest_dataframe(
                            "sales_history",
                            df_sales
                        )
        
                        ingest_dataframe(
                            "inventory",
                            df_inv
                        )
        
                        ingest_dataframe(
                            "suppliers",
                            df_sup
                        )
        
                        # --------------------------------------------
                        # Store available regions
                        # --------------------------------------------
                        if "region" in df_inv.columns:
        
                            st.session_state["available_regions"] = (
                                sorted(
                                    df_inv["region"]
                                    .dropna()
                                    .unique()
                                    .tolist()
                                )
                            )
        
                        else:
        
                            st.session_state["available_regions"] = []
        
                        st.success(
                            "✅ Cleaned datasets ingested successfully!"
                        )
        
                    except Exception as e:
        
                        st.error(
                            f"❌ Ingestion failed: {str(e)}"
                        )
        
                        st.exception(e)

        st.markdown("---")
        st.markdown("### 🎛️ Control Panel")
        
        selected_preset = st.selectbox(
            "Select Demonstration Preset",
            options=list(PRESET_QUERIES.keys()),
            key="preset_selector",
            on_change=on_preset_change,
            help="Choose a pre-configured evaluation scenario or enter your own custom query."
        )

        st.markdown("---")
        st.markdown("#### 🎯 Target Entities")

        regions = st.session_state.get("available_regions", [])
        if regions:
            selected_region = st.selectbox("Select Region to Optimize", options=regions, key="region_selector")
        else:
            selected_region = st.text_input("Region", value="", help="Target region (requires ingestion first)")

        # Render region statistics
        if selected_region:
            try:
                from aemiif.mcp_tools import get_region_statistics
                region_stats = get_region_statistics(selected_region)
                if region_stats:
                    st.caption("📊 **Region Statistics**")
                    col1, col2 = st.columns(2)
                    col1.metric("Stores", region_stats.get("num_stores", 0))
                    col2.metric("Products", region_stats.get("num_products", 0))
                    col1.metric("Sales Recs", region_stats.get("num_sales_records", 0))
                    col2.metric("Inv Recs", region_stats.get("num_inventory_records", 0))
                    st.metric("Suppliers", region_stats.get("num_suppliers", 0))
            except Exception as e:
                st.caption(f"Could not load stats: {e}")

        st.markdown("---")
        st.markdown("##### Optional Overrides")
        product_id_input = st.text_input(
            "Product ID",
            value="",
            help="Leave blank to run for all products in the region."
        ).strip().upper()

        store_id_input = st.text_input(
            "Store ID",
            value="",
            help="Leave blank to run for all stores in the region."
        ).strip().upper()

        p_prov = "User specified" if product_id_input else "Dynamic (All Products)"
        s_prov = "User specified" if store_id_input else "Dynamic (All Stores)"
        r_prov = "User selected" if regions else "Manual entry"
        d_prov = "User uploaded" if regions else "Prototype default"
        
        st.caption(f"Dataset Source: **{d_prov}**")
        st.caption(f"Region Source: **{r_prov}**")
        st.caption(f"Product Source: **{p_prov}**")
        st.caption(f"Store Source: **{s_prov}**")

        st.markdown("---")
        if st.button("🔄 Reset Results", width="stretch"):
            st.session_state["aemiif_result"] = None
            st.session_state["aemiif_state"] = None
            st.session_state["plan_id"] = None
            st.session_state["plan_approval_status"] = "NOT_GENERATED"
            st.session_state["plan_rejection_reason"] = None
            st.rerun()

        st.markdown("---")
        with st.expander("ℹ️ About AEMIIF"):
            st.markdown("""
            **AEMIIF Architecture**:
            - **Parser Agent**: LLM natural language parameter extraction
            - **Forecast Agent**: 7-day demand moving average
            - **Inventory Agent**: Deterministic stock position & net requirements
            - **Supplier Agent**: Candidate retrieval & hard filtering
            - **Capacity Intelligence**: Pre-solver strict / proportional gating
            - **MILP Optimizer**: PuLP mixed-integer linear programming
            - **Post-Validator**: Hard constraint verification
            - **Explanation Agent**: Grounded natural language justification
            """)

    # ============================================================
    # MAIN HEADER & STATUS BADGES
    # ============================================================
    st.markdown('<div class="main-header">📦 AEMIIF Decision Intelligence</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Agentic Explainable Multi-Agent Inventory Intelligence Framework</div>', unsafe_allow_html=True)

    st.markdown("""
        <div class="badge-bar">
            <span class="status-badge status-badge-green">🟢 PostgreSQL: Connected</span>
            <span class="status-badge status-badge-green">🟢 Solver: PuLP Deterministic MILP</span>
            <span class="status-badge status-badge-green">🟢 Orchestration: LangGraph (10 Nodes)</span>
            <span class="status-badge status-badge-amber">🛡️ Governance: Human-in-the-Loop (Zero Auto-Orders)</span>
        </div>
    """, unsafe_allow_html=True)

    # User Query Text Area (Synchronized with Preset selection)
    user_query = st.text_area(
        "Natural Language Inventory Request:",
        key="user_query_input",
        height=90,
        placeholder="Enter your replenishment requirements (e.g. budget, lead time, service level, priorities)..."
    )

    col_btn, col_info = st.columns([1, 4])
    with col_btn:
        run_clicked = st.button("🚀 Run AEMIIF", type="primary", width="stretch")
    with col_info:
        st.markdown("*Executes full deterministic multi-agent pipeline via LangGraph.*")

    # Workflow Execution Trigger
    if run_clicked:
        if not user_query.strip():
            st.error("Please enter a valid procurement request or select a preset.")
        else:
            with st.spinner("Executing AEMIIF Multi-Agent Orchestration (LangGraph)..."):
                try:
                    resp, state_dict = run_aemiif_pipeline(
                        query=user_query,
                        region=selected_region,
                        product_id=product_id_input if product_id_input else None,
                        store_id=store_id_input if store_id_input else None,
                        preset_name=selected_preset if selected_preset != "Custom Interactive Request" else None
                    )
                    st.session_state["aemiif_result"] = resp
                    st.session_state["aemiif_state"] = state_dict
                except Exception as e:
                    st.error(f"Pipeline execution failed: {str(e)}")

    # ============================================================
    # RENDER RESULTS
    # ============================================================
    resp: Optional[FinalAEMIIFResponse] = st.session_state.get("aemiif_result")
    state_dict: Optional[Dict[str, Any]] = st.session_state.get("aemiif_state")

    if resp and state_dict:
        st.markdown("---")

        # 1. Pipeline Execution Timeline
        times = resp.execution_times or {}
        total_time = times.get("total_pipeline_time", 0.0)

        st.markdown("##### ⏱️ Multi-Agent Pipeline Timeline")
        cols = st.columns(8)
        stages = [
            ("1. Parser", times.get("parse_requirements", 0)),
            ("2. Forecast", times.get("run_forecast", 0)),
            ("3. Inventory", times.get("run_inventory", 0)),
            ("4. Supplier", times.get("run_supplier", 0)),
            ("5. Capacity", times.get("run_capacity_intelligence", 0)),
            ("6. MILP Solver", times.get("run_milp", 0)),
            ("7. Validator", times.get("validate_optimization", 0)),
            ("8. Explainer", times.get("explain_result", 0)),
        ]
        for i, (label, t_val) in enumerate(stages):
            with cols[i]:
                st.markdown(f"**{label}**")
                st.caption(f"✓ {t_val*1000:.1f} ms" if t_val else "✓ Skipped / 0ms")

        # 2. Executive Status Banner
        status_color = {
            "OPTIMAL": "status-badge-green",
            "FEASIBLE": "status-badge-green",
            "INFEASIBLE": "status-badge-amber",
            "CAPACITY_INSUFFICIENT": "status-badge-amber",
            "NO_ELIGIBLE_SUPPLIERS": "status-badge-amber",
            "VALIDATION_FAILED": "status-badge-red",
            "ERROR": "status-badge-red"
        }.get(resp.status, "status-badge-amber")

        st.markdown(f"""
            <div style="background: white; border: 1px solid #E2E8F0; border-radius: 8px; padding: 1.2rem; margin-top: 1rem; margin-bottom: 1.5rem;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span class="status-badge {status_color}" style="font-size: 1rem; padding: 0.35rem 0.8rem;">
                            Status: {resp.status}
                        </span>
                        <span style="font-size: 0.88rem; color: #64748B; margin-left: 0.8rem;">
                            Request ID: <code>{resp.request_id}</code>
                        </span>
                    </div>
                    <div style="font-size: 0.88rem; font-weight: 600; color: #475569;">
                        Total Execution Latency: {total_time:.3f}s
                    </div>
                </div>
                <div style="margin-top: 0.8rem; font-size: 1.05rem; font-weight: 500; color: #1E293B;">
                    {resp.summary}
                </div>
            </div>
        """, unsafe_allow_html=True)

        # 3. Structured Decision Intelligence Tabs
        tab_exec, tab_plan, tab_demand, tab_sup, tab_cap, tab_req, tab_val, tab_opt, tab_hyp, tab_exp = st.tabs([
            "1️⃣ Executive Overview",
            "2️⃣ Procurement Plan",
            "3️⃣ Demand & Inventory",
            "4️⃣ Supplier Analysis",
            "5️⃣ Capacity Intelligence",
            "6️⃣ Requirements & Provenance",
            "7️⃣ Constraint Validation",
            "8️⃣ Optimization Analytics",
            "9️⃣ Hypothesis Testing",
            "🔟 Grounded Explanation"
        ])

        # Extract commonly used structures
        plan_items = resp.procurement_plan or []
        costs = resp.cost_summary or {}
        d_sum_list = resp.demand_summary or []
        i_sum_list = resp.inventory_summary or []
        c_sum = resp.capacity_summary or {}
        reqs = resp.user_requirements or {}
        weights = resp.objective_weights or {}
        c_stat = resp.constraint_summary or {}
        val_stat = state_dict.get("validation_result") or {}

        total_qty = sum(item.get("order_quantity", 0) for item in plan_items)
        selected_sups = [str(s) for s in set(item.get("supplier_id") for item in plan_items if item.get("supplier_id"))]

        # TAB 1: EXECUTIVE OVERVIEW
        with tab_exec:
            st.markdown("##### Executive Status")
            if resp.status in ["OPTIMAL", "FEASIBLE"] and resp.procurement_plan:
                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    st.metric("Total Order Quantity", f"{total_qty:,} units")
                with m2:
                    st.metric("Selected Supplier(s)", ", ".join(selected_sups))
                with m3:
                    st.metric("Total Optimal Cost", f"INR {costs.get('total_cost', 0):,.2f}")
                with m4:
                    rem = costs.get("budget_remaining")
                    st.metric("Budget Remaining", f"INR {rem:,.2f}" if rem is not None else "N/A")
                    
                st.markdown("---")
                # Summarize region and products
                p_src = resp.product_source or "Prototype default"
                prod_disp = state_dict.get("product_id") or "Multiple"
                store_disp = state_dict.get("store_id") or "Multiple"
                st.write(f"**Region Optimized**: {state_dict.get('region') or 'N/A'}")
                st.write(f"**Products Optimized**: {prod_disp}")
                st.write(f"**Stores Optimized**: {store_disp}")
                achieved_service_level = getattr(
                    resp,
                    "achieved_service_level",
                    None
                )
                
                if achieved_service_level is None:
                    achieved_service_level = state_dict.get(
                        "achieved_service_level"
                    )
                
                if achieved_service_level is not None:
                    st.write(
                        f"**Overall Achieved Service Level**: "
                        f"{float(achieved_service_level) * 100:.1f}%"
                    )
                    
                st.markdown("---")
                st.markdown("##### Optimization Impact")
                st.write(f"- **Recommended Order Quantity**: {total_qty:,} units")
                st.write(f"- **Number of Suppliers Selected**: {len(selected_sups)}")
                st.write(f"- **Total Procurement Cost**: INR {costs.get('total_cost', 0):,.2f}")
                st.write(f"- **Service Level**: {float(achieved_service_level) * 100:.1f}%" if achieved_service_level else "- **Service Level**: N/A")
                cap_util = sum(item.get("order_quantity", 0) for item in plan_items) / sum(item.get("capacity", 1) for item in plan_items) * 100 if sum(item.get("capacity", 1) for item in plan_items) > 0 else 0
                st.write(f"- **Capacity Utilization**: {cap_util:.1f}%")
                satisfied = len([v for v in c_stat.values() if v == "PASS"]) if c_stat else 0
                st.write(f"- **Constraints Satisfied**: {satisfied} / {len(c_stat) if c_stat else 0}")
                
                st.markdown("---")
                st.markdown("##### Decision Status")
                app_status = state_dict.get("approval_status", "NOT_GENERATED")
                if app_status == "PENDING_APPROVAL":
                    st.info("Status: PENDING APPROVAL")
                elif app_status == "APPROVED":
                    st.success("Status: APPROVED")
                elif app_status == "REJECTED":
                    st.error("Status: REJECTED")
                else:
                    st.write(f"Status: {app_status}")
                    
            else:
                # Infeasible or Ineligibility State
                st.info(f"ℹ️ **Constraint Gating Result**: `{resp.status}`")
                st.markdown(f"**Decision Summary**: {resp.summary}")
                
                if resp.errors:
                    st.markdown("##### 📌 Detected Constraint Violation(s)")
                    for err in resp.errors:
                        st.markdown(f"- ⚠️ **{err}**")

                diag = resp.relevant_diagnostics or {}
                if diag:
                    st.markdown("##### 🔍 Mathematical Diagnostics")
                    st.json(diag)

                st.markdown("""
                ---
                **Decision Intelligence Guidance**:
                - The optimization engine prevented ordering because one or more hard business rules (lead time, capacity, or budget) would be violated.
                - To achieve feasibility, consider relaxing the conflicting constraint in the request.
                """)

        # TAB 2: PROCUREMENT PLAN
        with tab_plan:
            if resp.status in ["OPTIMAL", "FEASIBLE"] and plan_items:
                st.markdown("---")
                st.markdown("#### RECOMMENDED PROCUREMENT PLAN")
                st.markdown("---")
                
                c1, c2, c3, c4 = st.columns(4)
                plan_id = resp.plan_id or "N/A"
                plan_obj = state_dict.get("plan")
                approval_status = state_dict.get("approval_status", "NOT_GENERATED")
                region = state_dict.get("region") or "Unknown"
                
                with c1:
                    st.write(f"**Plan ID:** {plan_id}")
                with c2:
                    st.write(f"**Region:** {region}")
                with c3:
                    st.write(f"**Optimization Status:** {resp.status}")
                with c4:
                    st.write(f"**Approval Status:** {approval_status}")
                
                st.markdown("##### Optimized Procurement Table")
                df_plan = pd.DataFrame(plan_items)
                rename_map = {
                    "product_id": "Product",
                    "store_id": "Store",
                    "supplier_id": "Supplier",
                    "order_quantity": "Order Qty",
                    "unit_cost": "Unit Cost (INR)",
                    "purchase_cost": "Purchase Cost (INR)",
                    "transport_cost": "Transport Cost (INR)",
                    "lead_time_days": "Lead Time (Days)",
                    "reliability": "Reliability"
                }
                df_plan_disp = df_plan[[c for c in rename_map.keys() if c in df_plan.columns]].rename(columns=rename_map)
                st.dataframe(df_plan_disp, width="stretch", hide_index=True)

                st.markdown("##### Cost Component Breakdown")
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.caption("Purchase Cost")
                    st.write(f"**INR {costs.get('purchase_cost', 0):,.2f}**")
                with c2:
                    st.caption("Transport Cost")
                    st.write(f"**INR {costs.get('transport_cost', 0):,.2f}**")
                with c3:
                    st.caption("Holding Cost Proxy")
                    st.write(f"**INR {costs.get('holding_cost', 0):,.2f}**")
                with c4:
                    st.caption("Stockout Penalty")
                    st.write(f"**INR {costs.get('stockout_cost', 0):,.2f}**")
                    
                    fig = px.pie(
                        values=[costs.get('purchase_cost', 0), costs.get('transport_cost', 0), costs.get('holding_cost', 0), costs.get('stockout_cost', 0)], 
                        names=['Purchase', 'Transport', 'Holding', 'Stockout'], 
                        title="Cost Distribution"
                    )
                    st.plotly_chart(fig, width="stretch")
                    
                st.markdown("---")
                st.markdown("#### CONSTRAINT STATUS")
                st.markdown("---")
                if c_stat:
                    for k, v in c_stat.items():
                        icon = "✅" if v == "PASS" else "❌"
                        st.write(f"{icon} **{k}**: {v}")
                
                st.markdown("---")
                st.markdown("#### APPROVAL CONTROLS")
                
                if approval_status == "PENDING_APPROVAL":
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("✅ APPROVE PROCUREMENT PLAN", width="stretch"):
                            st.session_state["confirm_approve"] = True
                    with col2:
                        if st.button("❌ REJECT PLAN", width="stretch"):
                            st.session_state["confirm_reject"] = True
                    with col3:
                        if st.button("🔄 REQUEST REVISION", width="stretch"):
                            st.session_state["aemiif_result"] = None
                            st.session_state["aemiif_state"] = None
                            st.session_state["plan_id"] = None
                            st.session_state["plan_approval_status"] = "REVISION_REQUIRED"
                            st.session_state["confirm_approve"] = False
                            st.session_state["confirm_reject"] = False
                            st.rerun()
                            
                    if st.session_state.get("confirm_approve"):
                        st.warning(f"You are approving Plan {plan_id} for region {region}. This action records the current optimized plan as the approved decision.")
                        if st.button("CONFIRM APPROVAL"):
                            st.session_state["aemiif_state"]["approval_status"] = "APPROVED"
                            if plan_obj:
                                plan_obj.approval_status = ApprovalStatus.APPROVED
                                save_procurement_decision(plan_id, region, "APPROVED", plan_obj.model_dump(), approved_by="Human User")
                            st.session_state["confirm_approve"] = False
                            st.rerun()
                            
                    if st.session_state.get("confirm_reject"):
                        reason = st.text_input("Please provide the reason for rejecting this procurement plan:")
                        if st.button("CONFIRM REJECTION"):
                            st.session_state["aemiif_state"]["approval_status"] = "REJECTED"
                            st.session_state["aemiif_state"]["plan_rejection_reason"] = reason
                            if plan_obj:
                                plan_obj.approval_status = ApprovalStatus.REJECTED
                                plan_obj.rejection_reason = reason
                                save_procurement_decision(plan_id, region, "REJECTED", plan_obj.model_dump(), decision_reason=reason, approved_by="Human User")
                            st.session_state["confirm_reject"] = False
                            st.rerun()
                elif approval_status == "APPROVED":
                    st.success(f"✓ Procurement Plan {plan_id} Approved")
                elif approval_status == "REJECTED":
                    st.error(f"Plan Rejected. Reason: {state_dict.get('plan_rejection_reason')}")
                    
            else:
                st.write("No procurement plan available.")

        # TAB 3: DEMAND & INVENTORY
        with tab_demand:
            st.markdown("##### 📈 Demand Forecasting & Inventory Health")
            tot_forecast = sum(d.get("forecast_demand", 0) for d in d_sum_list)
            tot_stock = sum(i.get("current_stock", 0) for i in i_sum_list)
            tot_incoming = sum(i.get("incoming_quantity", 0) for i in i_sum_list)
            tot_safety = sum(i.get("safety_stock", 0) for i in i_sum_list)
            tot_req = sum(i.get("replenishment_requirement", 0) for i in i_sum_list)
            
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Total Forecast Demand", f"{tot_forecast} units")
            with c2:
                st.metric("Total Current Stock", f"{tot_stock} units")
                st.caption(f"Incoming: {tot_incoming} units")
            with c3:
                st.metric("Total Safety Stock", f"{tot_safety} units")
            with c4:
                st.metric("Total Replenishment Req.", f"{tot_req} units")
                
            st.markdown("###### Regional Breakdown")
            if i_sum_list:
                df_inv = pd.DataFrame(i_sum_list)
                st.dataframe(df_inv, width="stretch", hide_index=True)
                
                # Visualizations
                if 'product_id' in df_inv.columns and 'replenishment_requirement' in df_inv.columns:
                    fig = px.bar(df_inv, x='product_id', y='replenishment_requirement', color='risk_level', title="Replenishment Requirement by Product")
                    st.plotly_chart(fig, width="stretch")

        # TAB 4: SUPPLIER ANALYSIS
        with tab_sup:
            st.markdown("##### 🏭 Evaluated Supplier Candidate Pool")
            sups = state_dict.get("supplier_outputs", [])
            if sups:
                sup_records = []
                for s in sups:
                    s_id = getattr(s, "supplier_id", None) or (s.get("supplier_id") if isinstance(s, dict) else "N/A")
                    pid = getattr(s, "product_id", None) or (s.get("product_id") if isinstance(s, dict) else "N/A")
                    u_cost = getattr(s, "unit_cost", None) or (s.get("unit_cost") if isinstance(s, dict) else 0.0)
                    moq = getattr(s, "moq", None) or (s.get("moq") if isinstance(s, dict) else 0)
                    lead_time = getattr(s, "lead_time_days", None) or (s.get("lead_time_days") if isinstance(s, dict) else 0)
                    rel = getattr(s, "reliability", None) or (s.get("reliability") if isinstance(s, dict) else 0.0)
                    cap = getattr(s, "capacity", None) or (s.get("capacity") if isinstance(s, dict) else 0)
                    status_f = getattr(s, "feasibility_status", None) or (s.get("feasibility_status") if isinstance(s, dict) else "unknown")
                    reason = getattr(s, "infeasibility_reason", None) or (s.get("infeasibility_reason") if isinstance(s, dict) else None)

                    sup_records.append({
                        "Supplier ID": s_id,
                        "Product": pid,
                        "Unit Cost (INR)": f"₹{u_cost:.2f}",
                        "MOQ": moq,
                        "Lead Time (Days)": lead_time,
                        "Reliability": f"{rel*100:.1f}%",
                        "Capacity": cap,
                        "Feasibility Status": "✅ Feasible" if status_f == "feasible" else f"❌ {reason or 'Infeasible'}",
                        "_raw_unit_cost": u_cost
                    })
                df_sups = pd.DataFrame(sup_records)
                st.dataframe(df_sups.drop(columns=["_raw_unit_cost"]), width="stretch", hide_index=True)
                
                # Plot
                if len(df_sups) > 0:
                    fig2 = px.scatter(df_sups, x="Lead Time (Days)", y="_raw_unit_cost", color="Supplier ID", size="Capacity", title="Supplier Tradeoffs (Lead Time vs Unit Cost)")
                    fig2.update_layout(yaxis_title="Unit Cost (INR)")
                    st.plotly_chart(fig2, width="stretch")
            else:
                st.write("No supplier candidates evaluated.")

        # TAB 5: CAPACITY INTELLIGENCE
        with tab_cap:
            mode_val = c_sum.get("mode") or "UNSPECIFIED"
            st.markdown(f"##### ⚡ Pre-Solver Capacity Gate (Mode: `{mode_val}`)")

            k1, k2, k3, k4 = st.columns(4)
            with k1:
                st.metric("Initial Candidates", c_sum.get("initial_candidate_count") or 0)
            with k2:
                st.metric("Eligible Candidates", c_sum.get("eligible_candidate_count") or 0)
            with k3:
                st.metric("Candidates Passed to MILP", c_sum.get("final_candidate_count") or 0)
            with k4:
                st.metric("Total Feasible Capacity", f"{c_sum.get('total_feasible_capacity') or 0} units")

            filtered = c_sum.get("filtered_suppliers", [])
            if filtered:
                st.warning(f"Suppliers filtered out by capacity pre-check: **{', '.join(filtered)}**")
            else:
                st.success("All evaluated suppliers met the capacity eligibility threshold.")

            if c_sum.get("proportional_target") is not None:
                st.info(f"Proportional Target Allocation: **{c_sum.get('proportional_target'):.2f} units / supplier**")
                
            fig = px.funnel(
                x=[c_sum.get("initial_candidate_count") or 0, c_sum.get("eligible_candidate_count") or 0, c_sum.get("final_candidate_count") or 0],
                y=["Initial Candidates", "Eligible Candidates", "MILP Candidates"],
                title="Candidate Reduction Funnel"
            )
            st.plotly_chart(fig, width="stretch")

        # TAB 6: REQUIREMENTS & PROVENANCE
        with tab_req:
            st.markdown("##### 🎯 Interpreted Constraints & Provenance")
            p_src = resp.product_source or "Prototype default"
            s_src = resp.store_source or "Prototype default"
            prod_disp = state_dict.get("product_id") or "Multiple / All"
            store_disp = state_dict.get("store_id") or "Multiple / All"

            col_p, col_s = st.columns(2)
            with col_p:
                p_cls = "prov-user" if p_src == "User specified" else "prov-default"
                st.markdown(f"Product ID: **{prod_disp}** <span class='provenance-chip {p_cls}'>{p_src}</span>", unsafe_allow_html=True)
            with col_s:
                s_cls = "prov-user" if s_src == "User specified" else "prov-default"
                st.markdown(f"Store ID: **{store_disp}** <span class='provenance-chip {s_cls}'>{s_src}</span>", unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("###### Objective Function Weights (Normalized to 1.0)")
            w_df = pd.DataFrame([
                {"Objective": "Purchase Cost", "Weight": weights.get("purchase_cost", 0.2), "Source": "Agent Derived"},
                {"Objective": "Transport Cost", "Weight": weights.get("transport_cost", 0.2), "Source": "Agent Derived"},
                {"Objective": "Holding Cost", "Weight": weights.get("holding_cost", 0.2), "Source": "Agent Derived"},
                {"Objective": "Stockout Cost", "Weight": weights.get("stockout_cost", 0.2), "Source": "Agent Derived"},
                {"Objective": "Supplier Reliability", "Weight": weights.get("supplier_reliability", 0.2), "Source": "Agent Derived"},
            ])
            st.dataframe(w_df, width="stretch", hide_index=True)

            st.markdown("###### Hard Constraints Configured")
            h1, h2, h3, h4 = st.columns(4)
            with h1:
                b = reqs.get("budget")
                st.write(f"**Budget**: {f'INR {b:,.2f}' if b else 'None'}")
            with h2:
                lt = reqs.get("max_lead_time_days")
                st.write(f"**Max Lead Time**: {f'{lt} days' if lt else 'None'}")
            with h3:
                sl = reqs.get("min_service_level")
                st.write(f"**Min Service Level**: {f'{sl*100:.1f}%' if sl else 'None'}")
            with h4:
                cm = reqs.get("capacity_mode")
                st.write(f"**Capacity Mode**: {cm or 'Default'}")

        # TAB 7: CONSTRAINT VALIDATION
        with tab_val:
            st.markdown("##### 🛡️ Mathematical Hard Constraint Post-Validation")
            checks = [
                ("Budget Constraint (Cost <= Budget)", c_stat.get("Budget") == "PASS"),
                ("Demand Satisfaction (Requirement Fulfilled)", c_stat.get("Demand") == "PASS"),
                ("Service Level Constraint (SL >= Target)", c_stat.get("Service Level") == "PASS"),
                ("Post-Solver Validation (Capacity & MOQ Hard Rules)", val_stat.get("status") == "PASSED"),
            ]
            check_rows = []
            for name, passed in checks:
                check_rows.append({
                    "Constraint Rule": name,
                    "Validation Status": "✅ PASS" if passed else "❌ FAIL"
                })
            st.dataframe(pd.DataFrame(check_rows), width="stretch", hide_index=True)

        # TAB 8: OPTIMIZATION ANALYTICS
        with tab_opt:
            st.markdown("##### 📊 Optimization Analytics")
            if resp.status in ["OPTIMAL", "FEASIBLE"] and plan_items:
                df_plan = pd.DataFrame(plan_items)
                
                # Supplier Concentration
                fig_sup = px.pie(df_plan, values='order_quantity', names='supplier_id', title='Supplier Concentration (By Volume)')
                
                # Product Allocation
                fig_prod = px.bar(df_plan, x='product_id', y='order_quantity', color='supplier_id', title='Product-level Allocation')
                
                # Store Allocation
                fig_store = px.bar(df_plan, x='store_id', y='order_quantity', color='product_id', title='Store-level Allocation')
                
                st.plotly_chart(fig_sup, width="stretch")
                st.plotly_chart(fig_prod, width="stretch")
                st.plotly_chart(fig_store, width="stretch")
            else:
                st.write("Analytics require an optimal/feasible procurement plan.")

        # TAB 9: HYPOTHESIS TESTING
        with tab_hyp:
            st.markdown("##### 🧪 Hypothesis Testing (Statistical Comparison)")
            st.markdown("Tests whether the optimization significantly reduces cost compared to average available supplier baselines.")
            
            if resp.status in ["OPTIMAL", "FEASIBLE"] and plan_items and sups:
                # Build a synthetic baseline: the average unit cost of ALL eligible suppliers for each product.
                from backend.services.hypothesis_service import evaluate_hypothesis
                res = evaluate_hypothesis(plan_items, sups, resp.status)
                if not res["is_valid"]:
                    st.warning(res.get("message", "Statistical comparison unavailable."))
                else:
                    st.write(f"**H0**: {res['hypothesis_0']}")
                    st.write(f"**H1**: {res['hypothesis_1']}")
                    
                    if res["t_statistic"] is None or res["p_val"] is None:
                        st.warning(res["interpretation"])
                    else:
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("Test Used", res["test_used"])
                        col2.metric("Sample Size", f"n={res['sample_size']}")
                        col3.metric("Statistic", f"{res['t_statistic']:.4f}")
                        col4.metric("P-Value", f"{res['p_value']:.4e}")
                        
                        st.write(f"**Significance Level (Alpha)**: {res['significance_level']}")
                        
                        if "Reject" in res["decision"]:
                            if "Warning" in res["decision"]:
                                st.warning(f"**Conclusion**: {res['decision']}. {res['interpretation']}")
                            else:
                                st.success(f"**Conclusion**: {res['decision']}. {res['interpretation']}")
                        else:
                            st.info(f"**Conclusion**: {res['decision']}. {res['interpretation']}")
            else:
                st.write("Statistical comparison unavailable. Requires optimal plan and supplier candidates.")

        # TAB 10: GROUNDED EXPLANATION
        with tab_exp:
            st.markdown("##### 💡 Grounded Decision Justification (Explanation Agent)")
            st.markdown(resp.explanation)

    # ============================================================
    # ARCHITECTURAL TRANSPARENCY & GOVERNANCE EXPANDER
    # ============================================================
    st.markdown("---")
    with st.expander("🛡️ Architectural Transparency & Safety Guarantees"):
        st.markdown("""
        ### Why AEMIIF is Safe for Real-World Supply Chains:
        1. **Deterministic Optimization**: Large Language Models (LLMs) are used **strictly** for translating natural-language queries into structured constraints and converting mathematical results into human explanations.
        2. **PuLP Solver Guarantees**: All order quantities, supplier selections, and cost calculations are solved using deterministic Mixed-Integer Linear Programming (MILP). No arithmetic is generated by generative models.
        3. **Pre-Solver Capacity Intelligence**: Prevents infeasible solver executions through strict hard-cap and proportional candidate filtering.
        4. **Zero Automated Purchase Orders**: AEMIIF operates in **Decision Intelligence Mode**. It prepares mathematically optimal recommendations for managerial review; it does **not** autonomously execute financial transactions or purchase orders.
        """)

if __name__ == "__main__":
    main()
