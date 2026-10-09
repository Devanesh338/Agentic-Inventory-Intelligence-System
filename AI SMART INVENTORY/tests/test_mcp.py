import pytest
import sys
import os
from unittest.mock import patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from aemiif.mcp_tools import get_sales_history, get_inventory, get_supplier_options

@patch('aemiif.mcp_tools._fetch_all')
def test_get_inventory(mock_fetch):
    mock_fetch.return_value = [{'product_id': 'P1', 'region': 'TestRegion'}]
    inv = get_inventory("TestRegion")
    assert isinstance(inv, list)
    assert inv[0]['product_id'] == 'P1'

@patch('aemiif.mcp_tools._fetch_all')
def test_get_sales_history(mock_fetch):
    mock_fetch.return_value = [{'product_id': 'P1', 'quantity_sold': 10}]
    sales = get_sales_history("TestRegion", days=7)
    assert isinstance(sales, list)
    assert sales[0]['quantity_sold'] == 10

@patch('aemiif.mcp_tools._fetch_all')
def test_get_supplier_options(mock_fetch):
    mock_fetch.return_value = [{'supplier_id': 'S1', 'unit_cost': 10.0, 'reliability_score': 0.99}]
    suppliers = get_supplier_options("TestRegion")
    assert isinstance(suppliers, list)
    if suppliers:
        assert 'unit_cost' in suppliers[0]
        assert 'reliability_score' in suppliers[0]
