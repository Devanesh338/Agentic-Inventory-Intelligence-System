import pytest
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from aemiif.graph import build_aemiif_graph, node_validate_optimization
from aemiif.schemas import (
    AEMIIFState, UserParameters, UserDecisionConfig, ObjectiveWeights,
    ForecastOutput, InventoryOutput, SupplierOption, CapacityMode,
    CapacityStatus, CapacityPrecheckResult, OptimizationResult, OrderLine
)
from aemiif.parser_agent import LLMParsedResult, ParsedPreferences, PreferenceLevel
from aemiif.explanation_agent import ExplanationAgent, generate_deterministic_explanation, _generate_infeasibility_explanation


# ============================================================
# GRAPH TESTS (1-8)
# ============================================================

def test_1_normal_successful_workflow():
    """Graph Test 1: Normal successful workflow (E2E Test Case 1)"""
    graph = build_aemiif_graph()
    mock_result = LLMParsedResult(
        parameters=UserParameters(budget=100000.0, max_lead_time_days=5, min_service_level=0.95),
        preferences=ParsedPreferences(purchase_cost=PreferenceLevel.VERY_HIGH, supplier_reliability=PreferenceLevel.HIGH)
    )
    result = graph.invoke({
        "user_query": "Replenish inventory under budget 100000, 5 days lead time, 95% service level.",
        "region": "Chennai-West",
        "mock_llm_result": mock_result
    })
    
    assert result["status"] == "OPTIMAL"
    assert result["user_config"] is not None
    assert len(result["forecast_outputs"]) > 0
    assert len(result["inventory_outputs"]) > 0
    assert len(result["supplier_outputs"]) > 0
    assert result["capacity_precheck"] is not None
    assert result["capacity_precheck"].status in [CapacityStatus.CAPACITY_SUFFICIENT, CapacityStatus.PROPORTIONAL_CANDIDATES_AVAILABLE]
    assert result["optimization_result"] is not None
    assert result["optimization_result"].status == "OPTIMAL"
    assert result["validation_result"]["status"] == "PASSED"
    assert result["explanation"] is not None
    assert "1. REQUEST SUMMARY" in result["explanation"]
    assert result["final_response"] is not None
    assert result["final_response"].status == "OPTIMAL"


def test_2_parser_failure():
    """Graph Test 2: Handle empty or invalid parser input"""
    graph = build_aemiif_graph()
    result = graph.invoke({"user_query": ""})
    
    assert result["status"] == "ERROR"
    assert len(result["errors"]) > 0
    assert "Empty or missing user_query." in result["errors"][0]
    assert result.get("optimization_result") is None
    assert result["final_response"] is not None
    assert result["final_response"].failure_type == "ERROR"


def test_3_no_supplier():
    """Graph Test 3: No suppliers satisfy hard constraints"""
    graph = build_aemiif_graph()
    # Unrealistic lead time of 0 days
    mock_result = LLMParsedResult(
        parameters=UserParameters(budget=100000.0, max_lead_time_days=0),
        preferences=ParsedPreferences()
    )
    result = graph.invoke({
        "user_query": "Need delivery in 0 days",
        "region": "Chennai-West",
        "mock_llm_result": mock_result
    })
    
    assert result["status"] == CapacityStatus.NO_ELIGIBLE_SUPPLIERS.value
    assert result["capacity_precheck"].status == CapacityStatus.NO_ELIGIBLE_SUPPLIERS
    # MILP must be skipped
    assert result.get("optimization_result") is None
    assert "NO_ELIGIBLE_SUPPLIERS" in result["explanation"]


def test_4_capacity_infeasibility():
    """Graph Test 4: Strict capacity failure (E2E Test Case 2)"""
    graph = build_aemiif_graph()
    
    # 360 required, 4 suppliers of capacity 40 each (total 160 < 360)
    config = UserDecisionConfig(
        parameters=UserParameters(capacity_mode=CapacityMode.STRICT_HARD_CAP),
        weights=ObjectiveWeights(),
        original_user_request="Strict capacity test"
    )
    inv = InventoryOutput(
        region="Chennai-West", product_id="P_TEST", store_id="ST_TEST", current_stock=0, incoming_quantity=0,
        forecast_demand=360, projected_stock=-360, safety_stock=0, inventory_position=0,
        replenishment_requirement=360, risk_level="HIGH"
    )
    suppliers = [
        SupplierOption(supplier_id=f"SUP_{i}", region="Chennai-West", product_id="P_TEST", unit_cost=10, moq=10, lead_time_days=2, reliability=0.99, capacity=40, feasibility_status="feasible")
        for i in range(1, 5)
    ]
    
    result = graph.invoke({
        "user_query": "Strict capacity test",
        "user_config": config,
        "inventory_outputs": [inv],
        "supplier_outputs": suppliers
    })
    
    assert result["status"] == CapacityStatus.CAPACITY_INSUFFICIENT.value
    assert result["capacity_precheck"].status == CapacityStatus.CAPACITY_INSUFFICIENT
    # MILP must NOT run
    assert result.get("optimization_result") is None
    assert "CAPACITY_INSUFFICIENT" in result["explanation"]
    assert "160" in result["explanation"]
    assert "360" in result["explanation"]


def test_5_proportional_mode():
    """Graph Test 5: Proportional capacity filtering (E2E Test Case 3)"""
    graph = build_aemiif_graph()
    
    # 360 required, 4 suppliers: capacities 40, 100, 120, 200. Target = 90
    config = UserDecisionConfig(
        parameters=UserParameters(capacity_mode=CapacityMode.PROPORTIONAL, budget=500000.0),
        weights=ObjectiveWeights(),
        original_user_request="Proportional test"
    )
    inv = InventoryOutput(
        region="Chennai-West", product_id="P_TEST", store_id="ST_TEST", current_stock=0, incoming_quantity=0,
        forecast_demand=360, projected_stock=-360, safety_stock=0, inventory_position=0,
        replenishment_requirement=360, risk_level="HIGH"
    )
    suppliers = [
        SupplierOption(supplier_id="SUP_A", region="Chennai-West", product_id="P_TEST", unit_cost=10, moq=20, lead_time_days=2, reliability=0.99, capacity=40, feasibility_status="feasible"),
        SupplierOption(supplier_id="SUP_B", region="Chennai-West", product_id="P_TEST", unit_cost=10, moq=20, lead_time_days=2, reliability=0.99, capacity=100, feasibility_status="feasible"),
        SupplierOption(supplier_id="SUP_C", region="Chennai-West", product_id="P_TEST", unit_cost=10, moq=20, lead_time_days=2, reliability=0.99, capacity=120, feasibility_status="feasible"),
        SupplierOption(supplier_id="SUP_D", region="Chennai-West", product_id="P_TEST", unit_cost=10, moq=20, lead_time_days=2, reliability=0.99, capacity=200, feasibility_status="feasible")
    ]
    
    result = graph.invoke({
        "user_query": "Proportional test",
        "user_config": config,
        "inventory_outputs": [inv],
        "supplier_outputs": suppliers
    })
    
    assert result["status"] == "OPTIMAL"
    cap = result["capacity_precheck"]
    assert cap.proportional_target == 90.0
    assert "SUP_A" in cap.filtered_suppliers
    assert len(result["reduced_suppliers"]) == 3
    assert result["optimization_result"].status == "OPTIMAL"
    assert result["optimization_result"].total_order_quantity == 360


def test_6_milp_infeasibility():
    """Graph Test 6: MILP returns INFEASIBLE (E2E Test Case 4: budget too low)"""
    graph = build_aemiif_graph()
    
    # Budget of INR 50 cannot satisfy MOQ of 100 @ 65.29 = 6529.00
    mock_result = LLMParsedResult(
        parameters=UserParameters(budget=50.0, max_lead_time_days=5, min_service_level=0.95),
        preferences=ParsedPreferences()
    )
    result = graph.invoke({
        "user_query": "Replenish inventory under impossible budget of 50",
        "region": "Chennai-West",
        "mock_llm_result": mock_result
    })
    
    assert result["status"] == "INFEASIBLE"
    assert result["optimization_result"] is not None
    assert result["optimization_result"].status == "INFEASIBLE"
    assert "MILP_INFEASIBLE" in result["explanation"]
    assert result["final_response"].status == "INFEASIBLE"


def test_7_validation_failure():
    """Graph Test 7: Post-solver validation failure detected and routed"""
    state = AEMIIFState(
        user_query="test",
        user_config=UserDecisionConfig(
            parameters=UserParameters(budget=1000.0),
            weights=ObjectiveWeights(),
            original_user_request="test"
        ),
        inventory_outputs=[
            InventoryOutput(
                region="Chennai-West", product_id="P001", store_id="ST001", current_stock=10, incoming_quantity=0,
                forecast_demand=100, projected_stock=-90, safety_stock=0, inventory_position=10,
                replenishment_requirement=90, risk_level="HIGH"
            )
        ],
        reduced_suppliers=[
            SupplierOption(supplier_id="SUP001", region="Chennai-West", product_id="P001", unit_cost=10, moq=10, lead_time_days=2, reliability=0.95, capacity=100, feasibility_status="feasible")
        ],
        capacity_precheck=CapacityPrecheckResult(status=CapacityStatus.CAPACITY_SUFFICIENT, total_feasible_capacity=100),
        # Fake solution that exceeds capacity (150 > 100)
        optimization_result=OptimizationResult(
            status="OPTIMAL",
            selected_suppliers=["SUP001"],
            order_lines=[OrderLine(region="Chennai-West", product_id="P001", store_id="ST001", supplier_id="SUP001", order_quantity=150, unit_cost=10, purchase_cost=1500, transport_cost=0, lead_time_days=2, reliability=0.95, moq=10, capacity=100)],
            total_order_quantity=150
        ),
        status="OPTIMAL"
    )
    
    update = node_validate_optimization(state)
    assert update["status"] == "VALIDATION_FAILED"
    assert update["validation_result"]["status"] == "FAILED"
    assert "exceeds capacity" in update["validation_result"]["error"]


def test_8_explanation_fallback():
    """Graph Test 8: ExplanationAgent gracefully falls back when no LLM is present"""
    agent = ExplanationAgent()
    agent.llm = None # Force fallback
    
    state = AEMIIFState(
        user_query="Test query",
        user_config=UserDecisionConfig(
            parameters=UserParameters(budget=50000.0),
            weights=ObjectiveWeights(),
            original_user_request="Test query"
        ),
        optimization_result=OptimizationResult(
            status="OPTIMAL",
            selected_suppliers=["SUP001"],
            total_order_quantity=50,
            total_cost=500.0
        ),
        status="OPTIMAL"
    )
    
    explanation = agent.explain(state)
    assert "1. REQUEST SUMMARY" in explanation
    assert "6. OPTIMIZATION RESULT" in explanation
    assert "SUP001" in explanation


# ============================================================
# STATE TESTS (9-13)
# ============================================================

def test_9_state_contains_user_decision_config():
    """State Test 9: State contains UserDecisionConfig"""
    graph = build_aemiif_graph()
    mock_result = LLMParsedResult(
        parameters=UserParameters(budget=50000.0),
        preferences=ParsedPreferences(purchase_cost=PreferenceLevel.HIGH)
    )
    res = graph.invoke({
        "user_query": "budget 50000",
        "mock_llm_result": mock_result
    })
    assert isinstance(res["user_config"], UserDecisionConfig)
    assert res["user_config"].parameters.budget == 50000.0
    assert isinstance(res["user_config"].weights, ObjectiveWeights)


def test_10_state_contains_agent_outputs():
    """State Test 10: State contains Forecast, Inventory, and Supplier outputs"""
    graph = build_aemiif_graph()
    res = graph.invoke({
        "user_query": "Replenish inventory",
        "region": "Chennai-West"
    })
    assert len(res["forecast_outputs"]) == 1
    assert isinstance(res["forecast_outputs"][0], ForecastOutput)
    assert len(res["inventory_outputs"]) == 1
    assert isinstance(res["inventory_outputs"][0], InventoryOutput)
    assert len(res["supplier_outputs"]) > 0
    assert isinstance(res["supplier_outputs"][0], SupplierOption)


def test_11_state_contains_capacity_result():
    """State Test 11: State contains CapacityPrecheckResult"""
    graph = build_aemiif_graph()
    res = graph.invoke({"user_query": "Replenish inventory", "region": "Chennai-West"})
    assert isinstance(res["capacity_precheck"], CapacityPrecheckResult)
    assert hasattr(res["capacity_precheck"], "status")
    assert hasattr(res["capacity_precheck"], "total_feasible_capacity")


def test_12_state_contains_optimization_result():
    """State Test 12: State contains OptimizationResult"""
    graph = build_aemiif_graph()
    res = graph.invoke({"user_query": "budget 100000", "region": "Chennai-West"})
    assert isinstance(res["optimization_result"], OptimizationResult)
    assert res["optimization_result"].status in ["OPTIMAL", "INFEASIBLE"]


def test_13_state_contains_validation_result():
    """State Test 13: State contains validation_result"""
    graph = build_aemiif_graph()
    res = graph.invoke({"user_query": "budget 100000", "region": "Chennai-West"})
    assert "validation_result" in res
    assert res["validation_result"] is not None
    assert res["validation_result"]["status"] in ["PASSED", "SKIPPED", "FAILED"]


# ============================================================
# EXPLANATION TESTS (14-17)
# ============================================================

def test_14_explanation_uses_actual_result():
    """Explanation Test 14: Explanation reflects exact numbers and selected supplier"""
    state = AEMIIFState(
        user_query="Replenish stock",
        user_config=UserDecisionConfig(
            parameters=UserParameters(budget=100000.0),
            weights=ObjectiveWeights(),
            original_user_request="Replenish stock"
        ),
        optimization_result=OptimizationResult(
            status="OPTIMAL",
            selected_suppliers=["SUP004"],
            total_order_quantity=100,
            total_cost=7100.26,
            total_purchase_cost=6592.0,
            total_transport_cost=508.26
        ),
        status="OPTIMAL"
    )
    explanation = generate_deterministic_explanation(state)
    assert "SUP004" in explanation
    assert "100" in explanation
    assert "7,100.26" in explanation
    assert "6,592.00" in explanation


def test_15_explanation_does_not_invent_values():
    """Explanation Test 15: Explanation does NOT recommend alternatives or invent suppliers"""
    state = AEMIIFState(
        user_query="test",
        user_config=UserDecisionConfig(parameters=UserParameters(), weights=ObjectiveWeights(), original_user_request="test"),
        optimization_result=OptimizationResult(status="OPTIMAL", selected_suppliers=["SUP003"], total_order_quantity=100),
        status="OPTIMAL"
    )
    explanation = generate_deterministic_explanation(state)
    assert "I think Supplier" not in explanation
    assert "would be better" not in explanation
    assert "savings" not in explanation.lower() or "cost" in explanation.lower()


def test_16_explanation_handles_infeasibility():
    """Explanation Test 16: Infeasibility explanation clearly distinguishes failure modes"""
    # 1. Capacity insufficient
    state1 = AEMIIFState(
        user_query="test",
        status=CapacityStatus.CAPACITY_INSUFFICIENT.value,
        capacity_precheck=CapacityPrecheckResult(
            status=CapacityStatus.CAPACITY_INSUFFICIENT,
            required_quantity=360,
            total_feasible_capacity=160,
            infeasibility_reason="Insufficient capacity"
        )
    )
    diag1 = _generate_infeasibility_explanation(state1)
    assert "DIAGNOSIS: CAPACITY_INSUFFICIENT" in diag1
    assert "160" in diag1
    assert "360" in diag1

    # 2. MILP Infeasible
    state2 = AEMIIFState(
        user_query="test",
        status="INFEASIBLE",
        optimization_result=OptimizationResult(status="INFEASIBLE", infeasibility_reason="Budget too low.")
    )
    diag2 = _generate_infeasibility_explanation(state2)
    assert "DIAGNOSIS: MILP_INFEASIBLE" in diag2
    assert "Budget too low" in diag2


def test_17_deterministic_fallback_works():
    """Explanation Test 17: Fallback handles both optimal and zero-demand scenarios cleanly"""
    state = AEMIIFState(
        user_query="No demand test",
        user_config=UserDecisionConfig(parameters=UserParameters(), weights=ObjectiveWeights(), original_user_request="No demand"),
        inventory_outputs=[
            InventoryOutput(region="Chennai-West", product_id="P001", store_id="ST001", current_stock=100, incoming_quantity=0, forecast_demand=0, projected_stock=100, safety_stock=10, inventory_position=100, replenishment_requirement=0, risk_level="LOW")
        ],
        optimization_result=OptimizationResult(status="OPTIMAL", total_order_quantity=0),
        status="OPTIMAL"
    )
    exp = generate_deterministic_explanation(state)
    assert "8. WHY THIS PLAN" in exp
    assert "No procurement order was needed" in exp


def test_18_strict_lead_time_violation():
    """Edge-case 3: Supplier violating max lead time is excluded from capacity"""
    graph = build_aemiif_graph()
    config = UserDecisionConfig(
        parameters=UserParameters(capacity_mode=CapacityMode.STRICT_HARD_CAP, max_lead_time_days=3),
        weights=ObjectiveWeights(),
        original_user_request="Lead time test"
    )
    inv = InventoryOutput(
        region="Chennai-West", product_id="P_TEST", store_id="ST_TEST", current_stock=0, incoming_quantity=0,
        forecast_demand=360, projected_stock=-360, safety_stock=0, inventory_position=0,
        replenishment_requirement=360, risk_level="HIGH"
    )
    # S1 has lead time 2 (feasible, cap 200). S2 has lead time 5 (violates max 3, cap 200).
    suppliers = [
        SupplierOption(supplier_id="S1", region="Chennai-West", product_id="P_TEST", unit_cost=10, moq=10, lead_time_days=2, reliability=0.99, capacity=200, feasibility_status="feasible"),
        SupplierOption(supplier_id="S2", region="Chennai-West", product_id="P_TEST", unit_cost=10, moq=10, lead_time_days=5, reliability=0.99, capacity=200, feasibility_status="feasible")
    ]
    res = graph.invoke({
        "user_query": "Lead time test",
        "user_config": config,
        "inventory_outputs": [inv],
        "supplier_outputs": suppliers
    })
    assert res["status"] == CapacityStatus.CAPACITY_INSUFFICIENT.value
    # S2 was excluded, so feasible capacity was only 200 < 360
    assert res["capacity_precheck"].total_feasible_capacity == 200
    assert res.get("optimization_result") is None


def test_19_existing_inventory_satisfies_demand():
    """Edge-case 9: Existing stock satisfies demand -> zero replenishment"""
    graph = build_aemiif_graph()
    config = UserDecisionConfig(
        parameters=UserParameters(budget=100000.0),
        weights=ObjectiveWeights(),
        original_user_request="Sufficient inventory"
    )
    forecast = ForecastOutput(
        region="Chennai-West", product_id="P006", store_id="ST002", historical_period_days=7, forecast_horizon=7,
        forecast_demand=50, average_daily_demand=7.14, model_name="7-Day MA"
    )
    inv = InventoryOutput(
        region="Chennai-West", product_id="P006", store_id="ST002", current_stock=100, incoming_quantity=0,
        forecast_demand=50, projected_stock=50, safety_stock=10, inventory_position=100,
        replenishment_requirement=0, risk_level="LOW"
    )
    res = graph.invoke({
        "user_query": "Sufficient inventory",
        "user_config": config,
        "forecast_outputs": [forecast],
        "inventory_outputs": [inv]
    })
    assert res["status"] == "OPTIMAL"
    assert res["optimization_result"].total_order_quantity == 0
    assert res["final_response"].status == "OPTIMAL"


def test_20_repeated_identical_request_deterministic():
    """Edge-case 11: Repeated identical request yields identical deterministic output"""
    graph = build_aemiif_graph()
    mock_result = LLMParsedResult(
        parameters=UserParameters(budget=100000.0, max_lead_time_days=5, min_service_level=0.95),
        preferences=ParsedPreferences(purchase_cost=PreferenceLevel.VERY_HIGH, supplier_reliability=PreferenceLevel.HIGH)
    )
    payload = {
        "user_query": "Replenish inventory",
        "region": "Chennai-West",
        "mock_llm_result": mock_result
    }
    r1 = graph.invoke(payload)
    r2 = graph.invoke(payload)
    
    assert r1["status"] == r2["status"] == "OPTIMAL"
    assert r1["optimization_result"].selected_suppliers == r2["optimization_result"].selected_suppliers
    assert r1["optimization_result"].total_order_quantity == r2["optimization_result"].total_order_quantity
    assert r1["optimization_result"].total_cost == r2["optimization_result"].total_cost
    assert r1["optimization_result"].achieved_service_level == r2["optimization_result"].achieved_service_level


