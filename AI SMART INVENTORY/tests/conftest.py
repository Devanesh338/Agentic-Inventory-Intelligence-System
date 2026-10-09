import pytest
from unittest.mock import patch

@pytest.fixture(autouse=True)
def mock_db_fetch_all():
    def mock_db_return(query, params):
        if "sales_history" in query:
            return [{'product_id': 'P006', 'store_id': 'ST002', 'quantity_sold': 10}]
        if "inventory" in query:
            return [{'product_id': 'P006', 'store_id': 'ST002', 'current_stock': 50, 'safety_stock': 20, 'incoming_quantity': 10, 'inventory_position': 60, 'forecast_demand': 20, 'projected_stock': 40, 'replenishment_requirement': 0, 'risk_level': 'LOW'}]
        if "suppliers" in query:
            return [{'supplier_id': 'SUP003', 'product_id': 'P006', 'unit_cost': 10, 'moq': 100, 'lead_time_days': 4, 'reliability_score': 0.96, 'capacity': 1000, 'transport_cost_per_km': 2.0}]
        return []
        
    with patch('aemiif.mcp_tools._fetch_all', side_effect=mock_db_return) as mock:
        yield mock
