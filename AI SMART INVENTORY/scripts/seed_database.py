import os
import csv
import sys
import logging
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database import get_db_cursor
import psycopg2.extras

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

SCHEMA_SQL = """
DROP TABLE IF EXISTS sales_history CASCADE;
DROP TABLE IF EXISTS inventory CASCADE;
DROP TABLE IF EXISTS suppliers CASCADE;

CREATE TABLE sales_history (
 sale_id VARCHAR(50) PRIMARY KEY,
 sale_date DATE,
 region VARCHAR(100),
 store_id VARCHAR(50),
 product_id VARCHAR(50),
 quantity_sold INT,
 unit_selling_price NUMERIC(12,2)
);

CREATE TABLE inventory (
 inventory_id VARCHAR(50) PRIMARY KEY,
 region VARCHAR(100),
 store_id VARCHAR(50),
 product_id VARCHAR(50),
 current_stock INT,
 reserved_stock INT,
 incoming_quantity INT,
 safety_stock INT,
 storage_capacity INT
);

CREATE TABLE suppliers (
 supplier_id VARCHAR(50),
 supplier_name VARCHAR(150),
 region VARCHAR(100),
 product_id VARCHAR(50),
 unit_cost NUMERIC(12,2),
 moq INT,
 capacity INT,
 lead_time_days INT,
 reliability_score NUMERIC(5,3),
 latitude NUMERIC(10,6),
 longitude NUMERIC(10,6),
 transport_cost_per_km NUMERIC(10,2),
 PRIMARY KEY(supplier_id, product_id, region)
);

CREATE INDEX idx_sales_region_prod_store ON sales_history(region, product_id, store_id);
CREATE INDEX idx_inventory_region_prod_store ON inventory(region, product_id, store_id);
CREATE INDEX idx_supplier_region_prod ON suppliers(region, product_id);

CREATE TABLE IF NOT EXISTS procurement_decisions (
    decision_id SERIAL PRIMARY KEY,
    plan_id VARCHAR(100) UNIQUE NOT NULL,
    region VARCHAR(100),
    status VARCHAR(50),
    decision_reason TEXT,
    approved_by VARCHAR(100),
    decision_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    plan_snapshot JSONB
);
"""

def initialize_schema():
    logger.info("Initializing schema...")
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(SCHEMA_SQL)
    logger.info("Schema initialized successfully.")

def ingest_dataframe(table_name, df):
    """Utility function to ingest a pandas DataFrame directly into the DB."""
    if df.empty:
        return
        
    if 'date' in df.columns and table_name == 'sales_history':
        df = df.rename(columns={'date': 'sale_date'})
        
    # Fetch valid columns from DB
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = %s", (table_name,))
        db_cols = [row['column_name'] for row in cursor.fetchall()]
        
    valid_cols = [c for c in df.columns if c in db_cols]
    df = df[valid_cols]
    
    cols = ",".join(list(df.columns))
    
    # Create a list of tuples from the dataframe values
    tuples = [tuple(x) for x in df.to_numpy()]
    
    # Comma-separated dataframe columns
    query = f"INSERT INTO {table_name} ({cols}) VALUES %s ON CONFLICT DO NOTHING"
    
    with get_db_cursor(commit=True) as cursor:
        psycopg2.extras.execute_values(cursor, query, tuples, page_size=500)
        logger.info(f"Successfully inserted {len(df)} rows into {table_name}.")

def main():
    try:
        initialize_schema()
        logger.info("Database schema updated. Awaiting data ingestion via Streamlit UI.")
    except Exception as e:
        logger.error(f"Error during schema initialization: {e}")

if __name__ == "__main__":
    main()

