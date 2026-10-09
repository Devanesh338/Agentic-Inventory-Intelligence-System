import pytest
import pandas as pd
from aemiif.validation_ingestion import validate_sales, validate_inventory, validate_suppliers, validate_cross_dataset

def test_validate_sales_valid():
    df = pd.DataFrame({
        "sale_id": ["S1", "S2"],
        "date": ["2023-01-01", "2023-01-02"],
        "region": ["R1", "R1"],
        "store_id": ["ST1", "ST1"],
        "product_id": ["P1", "P2"],
        "quantity_sold": [10, 20],
        "unit_selling_price": [50.0, 60.0]
    })
    is_valid, errors = validate_sales(df)
    assert is_valid is True
    assert len(errors) == 0

def test_validate_sales_missing_columns():
    df = pd.DataFrame({
        "sale_id": ["S1"],
        "date": ["2023-01-01"]
    })
    is_valid, errors = validate_sales(df)
    assert is_valid is False
    assert any("Missing required columns" in e for e in errors)

def test_validate_sales_negative_quantity():
    df = pd.DataFrame({
        "sale_id": ["S1"],
        "date": ["2023-01-01"],
        "region": ["R1"],
        "store_id": ["ST1"],
        "product_id": ["P1"],
        "quantity_sold": [-10],
        "unit_selling_price": [50.0]
    })
    is_valid, errors = validate_sales(df)
    assert is_valid is False
    assert any("non-negative" in e for e in errors)

def test_validate_inventory_valid():
    df = pd.DataFrame({
        "inventory_id": ["I1"],
        "region": ["R1"],
        "store_id": ["ST1"],
        "product_id": ["P1"],
        "current_stock": [100],
        "reserved_stock": [10],
        "incoming_quantity": [0],
        "safety_stock": [20],
        "storage_capacity": [500]
    })
    is_valid, errors = validate_inventory(df)
    assert is_valid is True

def test_validate_inventory_duplicate_store_product():
    df = pd.DataFrame({
        "inventory_id": ["I1", "I2"],
        "region": ["R1", "R1"],
        "store_id": ["ST1", "ST1"],
        "product_id": ["P1", "P1"],
        "current_stock": [100, 50],
        "reserved_stock": [10, 5],
        "incoming_quantity": [0, 0],
        "safety_stock": [20, 10],
        "storage_capacity": [500, 200]
    })
    is_valid, errors = validate_inventory(df)
    assert is_valid is False
    assert any("Duplicate 'store_id' + 'product_id'" in e for e in errors)

def test_validate_suppliers_valid():
    df = pd.DataFrame({
        "supplier_id": ["SUP1"],
        "supplier_name": ["Supplier A"],
        "region": ["R1"],
        "product_id": ["P1"],
        "unit_cost": [10.5],
        "moq": [100],
        "capacity": [1000],
        "lead_time_days": [5],
        "reliability_score": [0.95],
        "latitude": [12.9716],
        "longitude": [77.5946],
        "transport_cost_per_km": [2.5]
    })
    is_valid, errors = validate_suppliers(df)
    assert is_valid is True

def test_validate_suppliers_invalid_reliability():
    df = pd.DataFrame({
        "supplier_id": ["SUP1"],
        "supplier_name": ["Supplier A"],
        "region": ["R1"],
        "product_id": ["P1"],
        "unit_cost": [10.5],
        "moq": [100],
        "capacity": [1000],
        "lead_time_days": [5],
        "reliability_score": [1.5], # Invalid
        "latitude": [12.9716],
        "longitude": [77.5946],
        "transport_cost_per_km": [2.5]
    })
    is_valid, errors = validate_suppliers(df)
    assert is_valid is False
    assert any("between 0 and 1" in e for e in errors)

def test_validate_cross_dataset_valid():
    df_sales = pd.DataFrame({"region": ["R1"], "product_id": ["P1"]})
    df_inv = pd.DataFrame({"region": ["R1", "R2"], "product_id": ["P1", "P2"]})
    df_sup = pd.DataFrame({"region": ["R1", "R1"], "product_id": ["P1", "P2"]})
    
    is_valid, errors = validate_cross_dataset(df_sales, df_inv, df_sup)
    assert is_valid is True

def test_validate_cross_dataset_invalid_product():
    df_sales = pd.DataFrame({"region": ["R1"], "product_id": ["P3"]}) # P3 not in inventory
    df_inv = pd.DataFrame({"region": ["R1"], "product_id": ["P1"]})
    df_sup = pd.DataFrame({"region": ["R1"], "product_id": ["P1"]})
    
    is_valid, errors = validate_cross_dataset(df_sales, df_inv, df_sup)
    assert is_valid is False
    assert any("not found in inventory" in e for e in errors)
