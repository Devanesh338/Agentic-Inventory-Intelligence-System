import uuid
from datetime import datetime
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from typing import Optional
from database import get_db_cursor
from aemiif.schemas import OptimizationResult

def save_optimization_result(result: OptimizationResult, request_id: Optional[str] = None):
    """Save optimization result to the optimization_results table."""
    with get_db_cursor() as cursor:
        now = datetime.now()
        base_opt_id = str(uuid.uuid4())[:8]
        
        if not result.order_lines:
            # Save a single row for infeasible/error states
            query = """
                INSERT INTO optimization_results (
                    optimization_id, request_id, solver_status, created_at
                ) VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (f"OPT-{base_opt_id}", request_id, result.status, now))
            return
            
        # Save one row per order line
        for i, ol in enumerate(result.order_lines):
            opt_id = f"OPT-{base_opt_id}-{i}"
            query = """
                INSERT INTO optimization_results (
                    optimization_id, request_id, product_id, store_id, supplier_id,
                    recommended_quantity, purchase_cost, transport_cost, total_cost,
                    expected_delivery_days, solver_status, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                opt_id, request_id, ol.product_id, ol.store_id, ol.supplier_id,
                ol.order_quantity, ol.purchase_cost, ol.transport_cost,
                ol.purchase_cost + (ol.transport_cost or 0), ol.lead_time_days, result.status, now
            ))
