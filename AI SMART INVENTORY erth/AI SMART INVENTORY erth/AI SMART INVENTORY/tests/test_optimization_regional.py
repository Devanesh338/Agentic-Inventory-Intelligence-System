import pytest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from aemiif.optimization import build_optimization_input, solve_procurement_problem
from aemiif.schemas import (
    UserDecisionConfig, UserParameters, ObjectiveWeights,
    ForecastOutput, InventoryOutput, SupplierOption,
    CapacityPrecheckResult, CapacityMode
)

def test_optimization_storage_capacity():
    config = UserDecisionConfig(
        parameters=UserParameters(budget=50000.0),
        weights=ObjectiveWeights(),
        original_user_request="test"
    )
    # Store 1 has a storage capacity of 50. Current stock is 0. Req is 110.
    inv = InventoryOutput(
        region="TestRegion", product_id="P1", store_id="S1", current_stock=0, incoming_quantity=0,
        forecast_demand=100, projected_stock=-100, safety_stock=10,
        inventory_position=0, replenishment_requirement=110, risk_level="HIGH",
        storage_capacity=50
    )
    sup = SupplierOption(
        region="TestRegion", supplier_id="SUP1", product_id="P1", unit_cost=10.0, moq=10,
        lead_time_days=2, reliability=0.99, capacity=500, distance_km=10,
        transport_cost=5.0, feasibility_status="feasible"
    )
    
    opt_input = build_optimization_input(config, [], [inv], [sup])
    res = solve_procurement_problem(opt_input)
    
    assert res.status == "OPTIMAL"
    # Even though req is 110, the storage capacity caps it at 50
    assert res.total_order_quantity == 50

def test_optimization_proportional_capacity():
    config = UserDecisionConfig(
        parameters=UserParameters(budget=50000.0),
        weights=ObjectiveWeights(),
        original_user_request="test"
    )
    inv1 = InventoryOutput(
        region="TestRegion", product_id="P1", store_id="S1", current_stock=0, incoming_quantity=0,
        forecast_demand=100, projected_stock=-100, safety_stock=10,
        inventory_position=0, replenishment_requirement=110, risk_level="HIGH"
    )
    inv2 = InventoryOutput(
        region="TestRegion", product_id="P2", store_id="S1", current_stock=0, incoming_quantity=0,
        forecast_demand=100, projected_stock=-100, safety_stock=10,
        inventory_position=0, replenishment_requirement=110, risk_level="HIGH"
    )
    # Supplier has 500 capacity, but proportional target limits it
    sup1 = SupplierOption(
        region="TestRegion", supplier_id="SUP1", product_id="P1", unit_cost=10.0, moq=10,
        lead_time_days=2, reliability=0.99, capacity=500, distance_km=10,
        transport_cost=5.0, feasibility_status="feasible"
    )
    sup2 = SupplierOption(
        region="TestRegion", supplier_id="SUP2", product_id="P2", unit_cost=10.0, moq=10,
        lead_time_days=2, reliability=0.99, capacity=500, distance_km=10,
        transport_cost=5.0, feasibility_status="feasible"
    )
    
    cap_precheck = CapacityPrecheckResult(
        mode=CapacityMode.PROPORTIONAL,
        proportional_targets={"P1": 60, "P2": 40},
        status="PROPORTIONAL_CANDIDATES_AVAILABLE"
    )
    
    opt_input = build_optimization_input(config, [], [inv1, inv2], [sup1, sup2], capacity_precheck=cap_precheck)
    res = solve_procurement_problem(opt_input)
    
    assert res.status == "OPTIMAL"
    # Supplier has 500 capacity.
    # Note: Proportional filtering happens in Capacity Intelligence. The MILP does not artificially cap
    # feasible suppliers below their true physical capacity if it needs them to fulfill the order.
    # P1 and P2 require 110 each. Total 220.
    p1_order = sum(ol.order_quantity for ol in res.order_lines if ol.product_id == "P1")
    p2_order = sum(ol.order_quantity for ol in res.order_lines if ol.product_id == "P2")
    assert p1_order == 110
    assert p2_order == 110
    assert res.total_order_quantity == 220

def test_optimization_cross_product_budget_tradeoff():
    # Very tight budget: 1000. 
    # P1 costs 100 per unit, needs 10 (cost = 1000)
    # P2 costs 10 per unit, needs 100 (cost = 1000)
    # They compete for the same budget.
    config = UserDecisionConfig(
        parameters=UserParameters(budget=1000.0),
        weights=ObjectiveWeights(),
        original_user_request="test"
    )
    inv1 = InventoryOutput(
        region="TestRegion", product_id="P1", store_id="S1", current_stock=0, incoming_quantity=0,
        forecast_demand=10, projected_stock=-10, safety_stock=0,
        inventory_position=0, replenishment_requirement=10, risk_level="HIGH"
    )
    inv2 = InventoryOutput(
        region="TestRegion", product_id="P2", store_id="S1", current_stock=0, incoming_quantity=0,
        forecast_demand=100, projected_stock=-100, safety_stock=0,
        inventory_position=0, replenishment_requirement=100, risk_level="HIGH"
    )
    sup1 = SupplierOption(
        region="TestRegion", supplier_id="SUP1", product_id="P1", unit_cost=100.0, moq=1,
        lead_time_days=2, reliability=0.99, capacity=500, distance_km=10,
        transport_cost=0.0, feasibility_status="feasible"
    )
    sup2 = SupplierOption(
        region="TestRegion", supplier_id="SUP2", product_id="P2", unit_cost=10.0, moq=1,
        lead_time_days=2, reliability=0.99, capacity=500, distance_km=10,
        transport_cost=0.0, feasibility_status="feasible"
    )
    
    opt_input = build_optimization_input(config, [], [inv1, inv2], [sup1, sup2])
    res = solve_procurement_problem(opt_input)
    
    assert res.status == "OPTIMAL"
    assert res.total_purchase_cost + res.total_transport_cost <= 1000.0
    # Should fulfill a mix or one entirely, but not exceed budget
