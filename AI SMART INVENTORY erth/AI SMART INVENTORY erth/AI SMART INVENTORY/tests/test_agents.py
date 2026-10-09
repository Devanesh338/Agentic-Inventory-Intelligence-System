import pytest
import sys
import os
from unittest.mock import patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from aemiif.agents import ForecastAgent, InventoryAgent, SupplierAgent
from aemiif.schemas import ForecastOutput, UserDecisionConfig, UserParameters, ObjectiveWeights

@patch('aemiif.agents.get_sales_history')
def test_forecast_agent(mock_get_sales):
    mock_get_sales.return_value = [
        {'product_id': 'PRD-001', 'store_id': 'STR-001', 'quantity_sold': 10},
        {'product_id': 'PRD-001', 'store_id': 'STR-001', 'quantity_sold': 12},
        {'product_id': 'PRD-001', 'store_id': 'STR-001', 'quantity_sold': 8},
        {'product_id': 'PRD-002', 'store_id': 'STR-001', 'quantity_sold': 5}
    ]
    agent = ForecastAgent()
    forecasts = agent.run(region="TestRegion")
    
    assert len(forecasts) == 2
    f1 = next(f for f in forecasts if f.product_id == "PRD-001")
    f2 = next(f for f in forecasts if f.product_id == "PRD-002")
    
    assert f1.historical_period_days == 3
    assert f1.average_daily_demand == 10.0
    assert f1.forecast_demand == 70  # 10 * 7
    
    assert f2.historical_period_days == 1
    assert f2.forecast_demand == 35  # 5 * 7

@patch('aemiif.agents.get_inventory')
def test_inventory_agent(mock_inv):
    mock_inv.return_value = [
        {'product_id': 'PRD-001', 'store_id': 'STR-001', 'current_stock': 50, 'safety_stock': 20, 'incoming_quantity': 30}
    ]
    
    forecasts = [
        ForecastOutput(
            region="TestRegion", product_id="PRD-001", store_id="STR-001", 
            historical_period_days=7, forecast_horizon=7, forecast_demand=100, 
            average_daily_demand=14.3, model_name="test", confidence=0.8
        )
    ]
    
    agent = InventoryAgent()
    inventories = agent.run(region="TestRegion", forecasts=forecasts)
    
    assert len(inventories) == 1
    inventory = inventories[0]
    assert inventory.current_stock == 50
    assert inventory.incoming_quantity == 30
    assert inventory.inventory_position == 80
    assert inventory.projected_stock == -20
    assert inventory.replenishment_requirement == 40  # max(0, 100 + 20 - 80)
    assert inventory.risk_level == "HIGH"

@patch('aemiif.agents.get_supplier_options')
def test_supplier_agent(mock_suppliers):
    mock_suppliers.return_value = [
        {
            'supplier_id': 'SUP-001', 'product_id': 'PRD-001', 
            'unit_cost': 10, 'moq': 100, 'lead_time_days': 4, 
            'reliability_score': 0.96, 'capacity': 1000, 
            'transport_cost_per_km': 2.0
        }
    ]
    
    config = UserDecisionConfig(
        parameters=UserParameters(max_lead_time_days=3, max_distance_km=100, requested_store_ids=[]),
        weights=ObjectiveWeights(),
        original_user_request="test"
    )
    
    agent = SupplierAgent()
    options = agent.run(region="TestRegion", config=config)
    
    assert len(options) == 1
    assert options[0].feasibility_status == "infeasible"
    assert "Lead time 4 > limit 3" in options[0].infeasibility_reason

@patch('aemiif.agents.get_sales_history')
def test_forecast_agent_missing_sales_history(mock_get_sales):
    mock_get_sales.return_value = []
    agent = ForecastAgent()
    forecasts = agent.run(region="EmptyRegion")
    assert len(forecasts) == 0

@patch('aemiif.agents.get_inventory')
def test_inventory_agent_zero_demand_zero_stock(mock_inv):
    mock_inv.return_value = [
        {'product_id': 'PRD-ZERO', 'store_id': 'STR-ZERO', 'current_stock': 0, 'safety_stock': 10, 'incoming_quantity': 0}
    ]
    forecasts = [] # Missing/zero forecast
    agent = InventoryAgent()
    inventories = agent.run(region="TestRegion", forecasts=forecasts)
    
    assert len(inventories) == 1
    inventory = inventories[0]
    assert inventory.forecast_demand == 0
    assert inventory.projected_stock == 0
    assert inventory.replenishment_requirement == 10  # 0 + 10 - 0
    assert inventory.risk_level == "MEDIUM"  # 0 < safety_stock (10)

@patch('aemiif.agents.get_supplier_options')
def test_supplier_agent_multiple_candidates_infeasible_reliability(mock_suppliers):
    mock_suppliers.return_value = [
        {
            'supplier_id': 'SUP-001', 'product_id': 'PRD-001', 
            'unit_cost': 10, 'moq': 10, 'lead_time_days': 2, 
            'reliability_score': 0.85, 'capacity': 1000, 
            'transport_cost_per_km': 2.0
        },
        {
            'supplier_id': 'SUP-002', 'product_id': 'PRD-001', 
            'unit_cost': 12, 'moq': 5, 'lead_time_days': 1, 
            'reliability_score': 0.98, 'capacity': 500, 
            'transport_cost_per_km': 1.0
        }
    ]
    
    config = UserDecisionConfig(
        parameters=UserParameters(min_supplier_reliability=0.90, requested_store_ids=[]),
        weights=ObjectiveWeights(),
        original_user_request="test"
    )
    
    agent = SupplierAgent()
    options = agent.run(region="TestRegion", config=config)
    
    assert len(options) == 2
    assert options[0].feasibility_status == "infeasible"
    assert "Supplier reliability 0.85 < limit 0.9" in options[0].infeasibility_reason
    assert options[1].feasibility_status == "feasible"
