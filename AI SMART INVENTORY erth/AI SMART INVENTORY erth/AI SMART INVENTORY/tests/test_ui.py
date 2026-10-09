"""
Automated tests for Phase 5 AEMIIF Decision Intelligence UI (app.py).
Verifies:
- Clean module import
- Preset execution flows (Optimal, Capacity Infeasible, Proportional, Budget Infeasible, Lead Time Infeasible)
- Provenance preservation (User specified vs Prototype default)
- Output schemas and diagnostic integrity
- Masking and zero leakage of credentials
"""

import os
import sys
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import run_aemiif_pipeline
from aemiif.schemas import FinalAEMIIFResponse, CapacityStatus


def test_ui_import_and_callable():
    """Verify that app module and run_aemiif_pipeline helper are cleanly importable."""
    import app
    assert hasattr(app, "run_aemiif_pipeline")
    assert callable(app.run_aemiif_pipeline)
    assert hasattr(app, "main")
    assert callable(app.main)


def test_ui_preset1_optimal_execution():
    """Verify Preset 1 executes the real LangGraph workflow to OPTIMAL status."""
    query = (
        "Replenish the inventory under a budget of 100000. "
        "Suppliers should deliver within 5 days. "
        "Maintain at least 95 percent service level. "
        "Cost is very important and supplier reliability is also important."
    )
    resp, state = run_aemiif_pipeline(
        query=query,
        region="Chennai-West",
        preset_name="Preset 1: Standard Optimal Replenishment"
    )

    assert isinstance(resp, FinalAEMIIFResponse)
    assert resp.status == "OPTIMAL"
    assert resp.product_source == "Prototype default"
    assert resp.store_source == "Prototype default"
    assert resp.procurement_plan is not None
    assert len(resp.procurement_plan) > 0

    # Optimal selection matches audited results: SUP003, 100 units
    line = resp.procurement_plan[0]
    assert line["supplier_id"] == "SUP003"
    assert line["order_quantity"] == 100
    assert resp.cost_summary["total_cost"] == pytest.approx(1100.0, abs=1.0)
    assert resp.constraint_summary["Budget"] == "PASS"
    assert resp.constraint_summary["Demand"] == "PASS"
    assert resp.constraint_summary["Service Level"] == "PASS"


def test_ui_provenance_tracking():
    """Verify that user-supplied product and store IDs reflect 'User specified' provenance."""
    query = "Replenish inventory with budget 100000 within 5 days."
    resp, state = run_aemiif_pipeline(
        query=query,
        region="Chennai-West",
        product_id="P001",
        store_id="ST001",
        preset_name="Custom Interactive Request"
    )

    assert resp.product_source == "User specified"
    assert resp.store_source == "User specified"
    assert state["product_source"] == "User specified"
    assert state["store_source"] == "User specified"


def test_ui_preset2_capacity_infeasible():
    """Verify Preset 2 detects capacity deficit at precheck and skips MILP."""
    query = "Replenish inventory with strict_hard_cap capacity mode under a budget of 500000."
    resp, state = run_aemiif_pipeline(
        query=query,
        region="Chennai-West",
        preset_name="Preset 2: Strict Capacity Infeasible"
    )

    assert resp.status == CapacityStatus.CAPACITY_INSUFFICIENT.value
    assert state["capacity_precheck"].status == CapacityStatus.CAPACITY_INSUFFICIENT
    assert state.get("optimization_result") is None
    assert "CAPACITY_INSUFFICIENT" in resp.explanation
    assert resp.failure_type == "CAPACITY_INSUFFICIENT"


def test_ui_preset3_proportional_mode():
    """Verify Preset 3 runs proportional filtering and solves optimally."""
    query = "Replenish inventory with proportional capacity mode."
    resp, state = run_aemiif_pipeline(
        query=query,
        region="Chennai-West",
        preset_name="Preset 3: Proportional Capacity Mode"
    )

    assert resp.status == "OPTIMAL"
    cap = state["capacity_precheck"]
    assert cap.proportional_target == 90.0
    assert "SUP_A" in cap.filtered_suppliers
    assert len(state["reduced_suppliers"]) == 3
    assert state["optimization_result"].status == "OPTIMAL"


def test_ui_preset4_budget_infeasible():
    """Verify Preset 4 detects MILP mathematical infeasibility due to low budget."""
    query = "Replenish the inventory under a budget of 500."
    resp, state = run_aemiif_pipeline(
        query=query,
        region="Chennai-West",
        preset_name="Preset 4: Infeasible Budget Constraint"
    )

    assert resp.status == "INFEASIBLE"
    assert resp.failure_type == "INFEASIBLE"
    assert "MILP_INFEASIBLE" in resp.explanation
    assert state["optimization_result"].status == "INFEASIBLE"


def test_ui_preset5_lead_time_infeasible():
    """Verify Preset 5 catches lead time violations and returns NO_ELIGIBLE_SUPPLIERS."""
    query = "Replenish inventory within 1 day."
    resp, state = run_aemiif_pipeline(
        query=query,
        region="Chennai-West",
        preset_name="Preset 5: Lead Time Infeasible"
    )

    assert resp.status == "NO_ELIGIBLE_SUPPLIERS"
    assert resp.failure_type == "NO_ELIGIBLE_SUPPLIERS"
    assert "NO_ELIGIBLE_SUPPLIERS" in resp.explanation


def test_ui_security_no_secrets_exposed():
    """Verify that credentials and raw connection strings are never exposed in app.py."""
    with open(os.path.join(PROJECT_ROOT, "app.py"), "r", encoding="utf-8") as f:
        content = f.read()

    # Raw database password or sensitive string patterns must not appear hardcoded
    assert "password=" not in content.lower()
    assert "ep-cool-mountain" not in content.lower()
    assert "sk-proj-" not in content.lower()
