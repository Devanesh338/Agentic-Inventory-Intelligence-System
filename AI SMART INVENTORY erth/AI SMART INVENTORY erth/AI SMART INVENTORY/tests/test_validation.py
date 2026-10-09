import pytest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from aemiif.validation import post_validate_optimization
from aemiif.schemas import (
    OptimizationResult, OrderLine, UserDecisionConfig, UserParameters, ObjectiveWeights,
    InventoryOutput, SupplierOption, CapacityPrecheckResult, CapacityStatus, CapacityMode
)

def build_mock_setup():
    config = UserDecisionConfig(
        parameters=UserParameters(budget=50000.0, max_lead_time_days=5, max_distance_km=100, min_service_level=0.9),
        weights=ObjectiveWeights(),
        original_user_request="test"
    )
    inv = InventoryOutput(
        region="TestRegion", product_id="P1", store_id="S1", current_stock=0, incoming_quantity=0,
        forecast_demand=100, projected_stock=-100, safety_stock=0, inventory_position=0,
        replenishment_requirement=100, risk_level="HIGH", storage_capacity=100
    )
    sup = SupplierOption(
        supplier_id="SUP1", region="TestRegion", product_id="P1", unit_cost=10.0, moq=10,
        lead_time_days=2, reliability=0.99, capacity=500, distance_km=10.0, transport_cost=5.0,
        feasibility_status="feasible"
    )
    cap = CapacityPrecheckResult(status=CapacityStatus.CAPACITY_SUFFICIENT, mode=CapacityMode.STRICT_HARD_CAP)
    return config, [inv], [sup], cap

def test_validation_success():
    config, inventories, suppliers, cap = build_mock_setup()
    
    res = OptimizationResult(
        status="OPTIMAL", total_cost=1000.0, achieved_service_level=1.0,
        total_order_quantity=100,
        order_lines=[
            OrderLine(
                region="TestRegion", product_id="P1", store_id="S1", supplier_id="SUP1",
                order_quantity=100, unit_cost=10.0, purchase_cost=1000.0, transport_cost=5.0,
                lead_time_days=2, reliability=0.99, moq=10, capacity=500, distance_km=10.0
            )
        ]
    )
    # Should not raise
    post_validate_optimization(res, config, inventories, suppliers, cap)

def test_validation_storage_capacity_exceeded():
    config, inventories, suppliers, cap = build_mock_setup()
    inventories[0].storage_capacity = 50 # Set storage cap < order quantity
    
    res = OptimizationResult(
        status="OPTIMAL", total_cost=1000.0, achieved_service_level=1.0,
        total_order_quantity=100,
        order_lines=[
            OrderLine(
                region="TestRegion", product_id="P1", store_id="S1", supplier_id="SUP1",
                order_quantity=100, unit_cost=10.0, purchase_cost=1000.0, transport_cost=5.0,
                lead_time_days=2, reliability=0.99, moq=10, capacity=500, distance_km=10.0
            )
        ]
    )
    
    with pytest.raises(ValueError, match="exceeds storage capacity"):
        post_validate_optimization(res, config, inventories, suppliers, cap)

def test_validation_infeasible_supplier_selected():
    config, inventories, suppliers, cap = build_mock_setup()
    suppliers[0].feasibility_status = "infeasible"
    
    res = OptimizationResult(
        status="OPTIMAL", total_cost=1000.0, achieved_service_level=1.0,
        total_order_quantity=100,
        order_lines=[
            OrderLine(
                region="TestRegion", product_id="P1", store_id="S1", supplier_id="SUP1",
                order_quantity=100, unit_cost=10.0, purchase_cost=1000.0, transport_cost=5.0,
                lead_time_days=2, reliability=0.99, moq=10, capacity=500, distance_km=10.0
            )
        ]
    )
    
    with pytest.raises(ValueError, match="is marked as infeasible"):
        post_validate_optimization(res, config, inventories, suppliers, cap)
