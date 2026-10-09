import pytest
import pandas as pd
from aemiif.validation_ingestion import validate_suppliers, _check_and_normalize_duplicates
from scripts.seed_database import ingest_dataframe
from unittest.mock import patch, MagicMock

# Base valid data matching the expected schema
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

def test_normal_suppliers_csv():
    df = pd.DataFrame(get_valid_supplier_data())
    ok, errors = validate_suppliers(df)
    assert ok is True
    assert len(errors) == 0

def test_duplicate_column_identical_values():
    data = get_valid_supplier_data()
    # Pandas naturally names the duplicate as col.1
    data["transport_cost_per_km.1"] = [2.5]
    df = pd.DataFrame(data)
    
    ok, errors = validate_suppliers(df)
    assert ok is True
    assert len(errors) == 0
    # verify it was normalized
    assert "transport_cost_per_km.1" not in df.columns
    assert "transport_cost_per_km" in df.columns

def test_duplicate_column_conflicting_values():
    data = get_valid_supplier_data()
    data["transport_cost_per_km.1"] = [3.5]
    df = pd.DataFrame(data)
    
    ok, errors = validate_suppliers(df)
    assert ok is False
    assert len(errors) > 0
    assert any("Conflicting values found" in err for err in errors)
    assert any("transport_cost_per_km" in err for err in errors)

def test_missing_required_column():
    data = get_valid_supplier_data()
    del data["transport_cost_per_km"]
    df = pd.DataFrame(data)
    
    ok, errors = validate_suppliers(df)
    assert ok is False
    assert any("Missing required columns" in err for err in errors)

def test_extra_unexpected_column():
    data = get_valid_supplier_data()
    data["random_column"] = ["some_value"]
    df = pd.DataFrame(data)
    
    ok, errors = validate_suppliers(df)
    assert ok is True # Extra columns are ignored by validation layer
    
def test_max_distance_km_not_required():
    df = pd.DataFrame(get_valid_supplier_data())
    assert "max_distance_km" not in df.columns
    ok, errors = validate_suppliers(df)
    assert ok is True
    assert len(errors) == 0

@patch('scripts.seed_database.get_db_cursor')
@patch('psycopg2.extras.execute_values')
def test_no_generated_sql_contains_dot_1(mock_execute_values, mock_get_cursor):
    # Setup mock cursor
    mock_cursor = MagicMock()
    mock_get_cursor.return_value.__enter__.return_value = mock_cursor
    
    # Mock the DB schema query to return the base canonical columns
    mock_cursor.fetchall.return_value = [{'column_name': col} for col in get_valid_supplier_data().keys()]
    
    data = get_valid_supplier_data()
    data["transport_cost_per_km.1"] = [3.5] # Conflicting but seed_database handles dropping it because it queries DB schema
    
    df = pd.DataFrame(data)
    # Call ingest_dataframe
    ingest_dataframe("suppliers", df)
    
    # Verify execute_values was called with query
    assert mock_execute_values.called
    query = mock_execute_values.call_args[0][1]
    
    # Verify the SQL query does not contain .1
    assert ".1" not in query
    assert "transport_cost_per_km.1" not in query
