import pandas as pd
from typing import Tuple, Dict, Any, List
import re

def _check_missing_columns(df: pd.DataFrame, required: List[str]) -> List[str]:
    return [col for col in required if col not in df.columns]

def _check_nulls(df: pd.DataFrame, columns: List[str]) -> List[str]:
    errors = []
    for col in columns:
        if col in df.columns and df[col].isnull().any():
            errors.append(f"Column '{col}' contains null values.")
    return errors

def _check_and_normalize_duplicates(df: pd.DataFrame, dataset_name: str) -> List[str]:
    errors = []
    duplicate_pattern = re.compile(r'^(.*)\.(\d+)$')
    cols_to_drop = []
    
    base_to_dupes = {}
    for col in df.columns:
        match = duplicate_pattern.match(col)
        if match:
            base_col = match.group(1)
            # Only consider it a duplicate if the base column actually exists in the dataframe
            if base_col in df.columns:
                if base_col not in base_to_dupes:
                    base_to_dupes[base_col] = []
                base_to_dupes[base_col].append(col)
                
    for base_col, dupes in base_to_dupes.items():
        for dupe_col in dupes:
            if df[base_col].equals(df[dupe_col]):
                cols_to_drop.append(dupe_col)
            else:
                errors.append(f"{dataset_name} dataset contains duplicate column: {base_col}. Please provide only one {base_col} column. Conflicting values found.")
                
    if cols_to_drop:
        df.drop(columns=cols_to_drop, inplace=True)
        
    return errors

def validate_sales(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    required = ["sale_id", "date", "region", "store_id", "product_id", "quantity_sold", "unit_selling_price"]
    errors = _check_and_normalize_duplicates(df, "Sales")
    
    missing = _check_missing_columns(df, required)
    if missing:
        errors.append(f"Missing required columns: {', '.join(missing)}")
        return False, errors
        
    errors.extend(_check_nulls(df, ["sale_id", "region", "store_id", "product_id", "quantity_sold", "unit_selling_price", "date"]))
    
    if df["sale_id"].duplicated().any():
        errors.append("Duplicate 'sale_id' found.")
        
    try:
        if not pd.to_numeric(df["quantity_sold"]).ge(0).all():
            errors.append("'quantity_sold' must be non-negative.")
    except Exception:
        errors.append("'quantity_sold' must be numeric.")
        
    try:
        if not pd.to_numeric(df["unit_selling_price"]).ge(0).all():
            errors.append("'unit_selling_price' must be non-negative.")
    except Exception:
        errors.append("'unit_selling_price' must be numeric.")
        
    try:
        pd.to_datetime(df["date"])
    except Exception:
        errors.append("'date' column contains invalid dates.")
        
    return len(errors) == 0, errors

def validate_inventory(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    required = ["inventory_id", "region", "store_id", "product_id", "current_stock", "reserved_stock", "incoming_quantity", "safety_stock", "storage_capacity"]
    errors = _check_and_normalize_duplicates(df, "Inventory")
    
    missing = _check_missing_columns(df, required)
    if missing:
        errors.append(f"Missing required columns: {', '.join(missing)}")
        return False, errors
        
    errors.extend(_check_nulls(df, ["inventory_id", "region", "store_id", "product_id"]))
    
    if df["inventory_id"].duplicated().any():
        errors.append("Duplicate 'inventory_id' found.")
        
    if "store_id" in df.columns and "product_id" in df.columns:
        if df.duplicated(subset=["store_id", "product_id"]).any():
            errors.append("Duplicate 'store_id' + 'product_id' combination found.")
        
    numeric_cols = ["current_stock", "reserved_stock", "incoming_quantity", "safety_stock", "storage_capacity"]
    for col in numeric_cols:
        if col in df.columns:
            try:
                if not pd.to_numeric(df[col]).ge(0).all():
                    errors.append(f"'{col}' must be non-negative.")
            except Exception:
                errors.append(f"'{col}' must be numeric.")
            
    return len(errors) == 0, errors

def validate_suppliers(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    required = ["supplier_id", "supplier_name", "region", "product_id", "unit_cost", "moq", "capacity", "lead_time_days", "reliability_score", "latitude", "longitude", "transport_cost_per_km"]
    errors = _check_and_normalize_duplicates(df, "Supplier")
    
    missing = _check_missing_columns(df, required)
    if missing:
        errors.append(f"Missing required columns: {', '.join(missing)}")
        return False, errors
        
    errors.extend(_check_nulls(df, ["supplier_id", "region", "product_id"]))
    
    if "supplier_id" in df.columns and "product_id" in df.columns:
        if df.duplicated(subset=["supplier_id", "product_id"]).any():
            errors.append("Duplicate 'supplier_id' + 'product_id' combination found.")
        
    positive_numeric_cols = ["unit_cost", "moq", "capacity", "lead_time_days", "transport_cost_per_km"]
    for col in positive_numeric_cols:
        if col in df.columns:
            try:
                if not pd.to_numeric(df[col]).ge(0).all():
                    errors.append(f"'{col}' must be non-negative.")
            except Exception:
                errors.append(f"'{col}' must be numeric.")
            
    if "reliability_score" in df.columns:
        try:
            reliability = pd.to_numeric(df["reliability_score"])
            if not (reliability.ge(0).all() and reliability.le(1).all()):
                errors.append("'reliability_score' must be between 0 and 1.")
        except Exception:
            errors.append("'reliability_score' must be numeric.")
        
    return len(errors) == 0, errors

def validate_cross_dataset(df_sales: pd.DataFrame, df_inv: pd.DataFrame, df_sup: pd.DataFrame) -> Tuple[bool, List[str]]:
    errors = []
    
    if df_sales.empty or df_inv.empty or df_sup.empty:
        errors.append("One or more datasets are completely empty.")
        return False, errors
        
    if "region" in df_sales.columns and "region" in df_inv.columns and "region" in df_sup.columns:
        sales_regions = set(df_sales["region"].dropna().unique())
        inv_regions = set(df_inv["region"].dropna().unique())
        sup_regions = set(df_sup["region"].dropna().unique())
        
        if not sales_regions.issubset(inv_regions):
            errors.append(f"Sales regions {sales_regions - inv_regions} not found in inventory dataset.")
        if not sup_regions.issubset(inv_regions):
            errors.append(f"Supplier regions {sup_regions - inv_regions} not found in inventory dataset.")
            
    if "product_id" in df_sales.columns and "product_id" in df_inv.columns and "product_id" in df_sup.columns:
        sales_products = set(df_sales["product_id"].dropna().unique())
        inv_products = set(df_inv["product_id"].dropna().unique())
        sup_products = set(df_sup["product_id"].dropna().unique())
        
        if not sales_products.issubset(inv_products):
            errors.append(f"Sales product IDs {sales_products - inv_products} not found in inventory dataset.")
        if not inv_products.issubset(sup_products):
            errors.append(f"Inventory product IDs {inv_products - sup_products} not found in suppliers dataset.")
        
    return len(errors) == 0, errors
