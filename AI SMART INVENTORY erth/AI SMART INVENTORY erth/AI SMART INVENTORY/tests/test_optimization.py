import pytest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from aemiif.optimization import build_optimization_input, solve_procurement_problem
from aemiif.schemas import (
    UserDecisionConfig, UserParameters, ObjectiveWeights,
    ForecastOutput, InventoryOutput, SupplierOption
)

def test_optimization_zero_requirement():
    config = UserDecisionConfig(
        parameters=UserParameters(budget=1000.0),
        weights=ObjectiveWeights(),
        original_user_request="test"
    )
    inv = InventoryOutput(
        region="TestRegion", product_id="P1", store_id="S1", current_stock=100, incoming_quantity=0,
        forecast_demand=50, projected_stock=50, safety_stock=10,
        inventory_position=100, replenishment_requirement=0, risk_level="LOW"
    )
    opt_input = build_optimization_input(config, [], [inv], [])
    res = solve_procurement_problem(opt_input)
    assert res.status == "OPTIMAL"
    assert res.total_order_quantity == 0

def test_optimization_infeasible_budget():
    config = UserDecisionConfig(
        parameters=UserParameters(budget=10.0, min_service_level=0.95), # Too low budget
        weights=ObjectiveWeights(),
        original_user_request="test"
    )
    inv = InventoryOutput(
        region="TestRegion", product_id="P1", store_id="S1", current_stock=0, incoming_quantity=0,
        forecast_demand=100, projected_stock=-100, safety_stock=10,
        inventory_position=0, replenishment_requirement=110, risk_level="HIGH"
    )
    sup = SupplierOption(
        region="TestRegion", supplier_id="SUP1", product_id="P1", unit_cost=50.0, moq=10,
        lead_time_days=2, reliability=0.99, capacity=500, distance_km=10,
        transport_cost=5.0, feasibility_status="feasible"
    )
    opt_input = build_optimization_input(config, [], [inv], [sup])
    res = solve_procurement_problem(opt_input)
    assert res.status == "INFEASIBLE"

def test_optimization_optimal_selection():
    config = UserDecisionConfig(
        parameters=UserParameters(budget=50000.0, min_supplier_reliability=0.9),
        weights=ObjectiveWeights(purchase_cost=0.1, supplier_reliability=0.1, transport_cost=0.0, holding_cost=0.0, stockout_cost=0.8),
        original_user_request="test"
    )
    inv = InventoryOutput(
        region="TestRegion", product_id="P1", store_id="S1", current_stock=0, incoming_quantity=0,
        forecast_demand=100, projected_stock=-100, safety_stock=10,
        inventory_position=0, replenishment_requirement=110, risk_level="HIGH"
    )
    
    # Sup1 is cheap but unreliable (should fail SL constraint or be penalized heavily)
    sup1 = SupplierOption(
        region="TestRegion", supplier_id="SUP1", product_id="P1", unit_cost=10.0, moq=10,
        lead_time_days=2, reliability=0.80, capacity=500, distance_km=10,
        transport_cost=5.0, feasibility_status="feasible"
    )
    # Sup2 is expensive but reliable
    sup2 = SupplierOption(
        region="TestRegion", supplier_id="SUP2", product_id="P1", unit_cost=20.0, moq=10,
        lead_time_days=2, reliability=0.99, capacity=500, distance_km=10,
        transport_cost=5.0, feasibility_status="feasible"
    )
    
    opt_input = build_optimization_input(config, [], [inv], [sup1, sup2])
    res = solve_procurement_problem(opt_input)
    
    assert res.status == "OPTIMAL"
    # Because min_service_level is 0.9, SUP1 alone (0.8) is not feasible. 
    # It must pick SUP2 or a mix, but SUP2 alone is 0.99 > 0.9.
    assert "SUP2" in res.selected_suppliers
    assert res.total_order_quantity == 110

def test_optimization_no_feasible_suppliers():
    config = UserDecisionConfig(
        parameters=UserParameters(budget=50000.0),
        weights=ObjectiveWeights(),
        original_user_request="test"
    )
    inv = InventoryOutput(
        region="TestRegion", product_id="P1", store_id="S1", current_stock=0, incoming_quantity=0,
        forecast_demand=100, projected_stock=-100, safety_stock=10,
        inventory_position=0, replenishment_requirement=110, risk_level="HIGH"
    )
    # Both suppliers are infeasible due to hard constraints (marked in Agent)
    sup1 = SupplierOption(
        region="TestRegion", supplier_id="SUP1", product_id="P1", unit_cost=10.0, moq=10,
        lead_time_days=2, reliability=0.80, capacity=500, distance_km=10,
        transport_cost=5.0, feasibility_status="infeasible"
    )
    opt_input = build_optimization_input(config, [], [inv], [sup1])
    res = solve_procurement_problem(opt_input)
    assert res.status == "INFEASIBLE"
    assert "No feasible suppliers available" in res.infeasibility_reason
