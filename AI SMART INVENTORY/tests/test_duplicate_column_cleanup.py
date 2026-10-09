import pytest
import pandas as pd
from unittest.mock import patch
from app import clean_duplicate_columns
from aemiif.validation_ingestion import validate_suppliers

def get_valid_supplier_data():
    return {
        "supplier_id": ["SUP001"],
        "supplier_name": ["Alpha Supplier"],
        "region": ["Chennai-North"],
        "product_id": ["PRD-001"],
        "unit_cost": [10.5],
        "moq": [100],
        "capacity": [5000],
        "lead_time_days": [2],
        "reliability_score": [0.95],
        "latitude": [13.0827],
        "longitude": [80.2707],
        "transport_cost_per_km": [2.5]
    }

@patch('app.st')
def test_identical_duplicate_columns(mock_st):
    data = get_valid_supplier_data()
    df = pd.DataFrame(data)
    df["transport_cost_per_km.1"] = df["transport_cost_per_km"]
    
    assert "transport_cost_per_km.1" in df.columns
    
    result = clean_duplicate_columns(df)
    
    assert result is True
    assert "transport_cost_per_km.1" not in df.columns
    assert "transport_cost_per_km" in df.columns
    mock_st.warning.assert_called()
    mock_st.error.assert_not_called()

@patch('app.st')
def test_conflicting_duplicate_columns(mock_st):
    data = get_valid_supplier_data()
    df = pd.DataFrame(data)
    df["transport_cost_per_km.1"] = [3.5] # Different value
    
    result = clean_duplicate_columns(df)
    
    assert result is False
    assert "transport_cost_per_km.1" in df.columns # Should not remove if conflicting
    mock_st.error.assert_called()

@patch('app.st')
def test_normal_supplier_dataset(mock_st):
    data = get_valid_supplier_data()
    df = pd.DataFrame(data)
    original_columns = list(df.columns)
    
    result = clean_duplicate_columns(df)
    
    assert result is True
    assert list(df.columns) == original_columns
    mock_st.warning.assert_not_called()
    mock_st.error.assert_not_called()

def test_max_distance_km_not_required():
    data = get_valid_supplier_data()
    df = pd.DataFrame(data)
    
    assert "max_distance_km" not in df.columns
    ok, errors = validate_suppliers(df)
    assert ok is True
