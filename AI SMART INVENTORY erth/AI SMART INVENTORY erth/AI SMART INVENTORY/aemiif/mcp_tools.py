import sys
import os
from typing import List, Dict, Any, Optional

# Ensure we can import database from the root level
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database import get_db_cursor

def to_float(value, default=0.0):
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

def _fetch_all(query: str, params: tuple) -> List[Dict[str, Any]]:
    """Helper to execute query and fetch all results as dicts."""
    with get_db_cursor() as cursor:
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        # Convert all numeric types (like decimal.Decimal) to float
        import decimal
        for row in results:
            for key, value in row.items():
                if isinstance(value, decimal.Decimal):
                    row[key] = to_float(value)
        return results

def get_sales_history(region: str, product_id: Optional[str] = None, store_id: Optional[str] = None, days: Optional[int] = None) -> List[Dict[str, Any]]:
    """Retrieve sales history for a region, and optionally a specific product/store."""
    query = "SELECT * FROM sales_history WHERE region = %s"
    params = [region]
    
    if product_id:
        query += " AND product_id = %s"
        params.append(product_id)
        
    if store_id:
        query += " AND store_id = %s"
        params.append(store_id)
        
    query += " ORDER BY sale_date DESC"
    
    if days is not None:
        query += " LIMIT %s"
        params.append(days)
        
    return _fetch_all(query, tuple(params))

def get_inventory(region: str, product_id: Optional[str] = None, store_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve current inventory levels for a region."""
    query = "SELECT * FROM inventory WHERE region = %s"
    params = [region]
    
    if product_id:
        query += " AND product_id = %s"
        params.append(product_id)
    if store_id:
        query += " AND store_id = %s"
        params.append(store_id)
        
    return _fetch_all(query, tuple(params))

def get_supplier_options(region: str, product_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve suppliers that offer products in a specific region."""
    query = "SELECT * FROM suppliers WHERE region = %s"
    params = [region]
    
    if product_id:
        query += " AND product_id = %s"
        params.append(product_id)
        
    return _fetch_all(query, tuple(params))

def get_region_statistics(region: str) -> Dict[str, Any]:
    """Calculate aggregate statistics for a specific region directly from the database."""
    stats = {}
    
    with get_db_cursor() as cursor:
        cursor.execute("SELECT COUNT(DISTINCT store_id) FROM inventory WHERE region = %s", (region,))
        stats['num_stores'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(DISTINCT product_id) FROM inventory WHERE region = %s", (region,))
        stats['num_products'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) FROM sales_history WHERE region = %s", (region,))
        stats['num_sales_records'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) FROM inventory WHERE region = %s", (region,))
        stats['num_inventory_records'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) FROM suppliers WHERE region = %s", (region,))
        stats['num_suppliers'] = cursor.fetchone()['count']
        
    return stats
