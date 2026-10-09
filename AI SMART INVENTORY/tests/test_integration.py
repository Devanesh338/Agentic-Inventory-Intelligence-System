import pytest
import sys
import os
from unittest.mock import patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from aemiif.parser_agent import RequirementParserAgent, LLMParsedResult, ParsedPreferences, PreferenceLevel
from aemiif.schemas import UserParameters
from aemiif.agents import ForecastAgent, InventoryAgent, SupplierAgent

@patch('aemiif.mcp_tools._fetch_all')
def test_integration_pipeline(mock_fetch):
    """Verify the pipeline flow: Parser -> Forecast -> Inventory -> Supplier"""
    
    # Mocking database returns depending on the query
    def mock_db_return(query, params):
        if "sales_history" in query:
            return [{'product_id': 'PRD-001', 'store_id': 'STR-001', 'quantity_sold': 10}]
        if "inventory" in query:
            return [{'product_id': 'PRD-001', 'store_id': 'STR-001', 'current_stock': 50, 'safety_stock': 20, 'incoming_quantity': 10}]
        if "suppliers" in query:
            return [{'supplier_id': 'SUP-001', 'product_id': 'PRD-001', 'unit_cost': 10, 'moq': 100, 'lead_time_days': 4, 'reliability_score': 0.96, 'capacity': 1000, 'transport_cost_per_km': 2.0}]
        return []
    
    mock_fetch.side_effect = mock_db_return
    
    # 1. Parse
    parser = RequirementParserAgent()
    mock_result = LLMParsedResult(
        parameters=UserParameters(budget=50000.0, max_lead_time_days=10),
        preferences=ParsedPreferences(purchase_cost=PreferenceLevel.HIGH)
    )
    config = parser.parse_requirements("Mock request", mock_llm_result=mock_result)
    
    assert config.parameters.budget == 50000.0
    assert config.weights.purchase_cost > config.weights.supplier_reliability
    
    # 2. Run agents regionally
    region = "TestRegion"
    
    forecast_agent = ForecastAgent()
    forecasts = forecast_agent.run(region)
    assert len(forecasts) == 1
    assert forecasts[0].forecast_demand >= 0
    
    inventory_agent = InventoryAgent()
    inventories = inventory_agent.run(region, forecasts)
    assert len(inventories) == 1
    assert inventories[0].current_stock >= 0
    
    supplier_agent = SupplierAgent()
    suppliers = supplier_agent.run(region, config)
    assert isinstance(suppliers, list)
    
    if suppliers:
        assert hasattr(suppliers[0], 'feasibility_status')
