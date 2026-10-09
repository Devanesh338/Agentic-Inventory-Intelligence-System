import os
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import logging
from contextlib import contextmanager

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

db_pool = None
try:
    if DATABASE_URL:
        db_pool = psycopg2.pool.SimpleConnectionPool(1, 20, DATABASE_URL)
        logger.info("Database connection pool created successfully")
    else:
        logger.error("DATABASE_URL environment variable is not set")
except Exception as e:
    logger.error(f"Failed to create connection pool: {e}")


@contextmanager
def get_db_connection():
    """Context manager for obtaining and releasing a connection from the pool, with retry logic for dead connections."""
    global db_pool
    if not db_pool:
        raise Exception("Database connection pool is not initialized.")
    
    conn = db_pool.getconn()
    
    # Check if the connection is dead
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
    except psycopg2.OperationalError:
        # The connection was dropped by Neon or timed out
        db_pool.putconn(conn, close=True)
        # Attempt to get a fresh connection
        conn = psycopg2.connect(DATABASE_URL)
        
    try:
        yield conn
    finally:
        if not conn.closed:
            # We don't want to throw ad-hoc connections back into the pool indiscriminately
            if hasattr(db_pool, '_used') and conn in db_pool._used:
                db_pool.putconn(conn)
            else:
                conn.close()
        else:
            if hasattr(db_pool, '_used') and conn in db_pool._used:
                db_pool.putconn(conn, close=True)

@contextmanager
def get_db_cursor(commit=False):
    """Context manager for getting a dictionary cursor and handling transactions."""
    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            yield cursor
            if commit:
                conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database transaction error: {e}")
            raise
        finally:
            cursor.close()

def check_health():
    """Simple health check for the database."""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT 1;")
            result = cursor.fetchone()
            if result:
                return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "details": str(e)}
    return {"status": "unhealthy", "details": "No result from database"}

import json

def save_procurement_decision(plan_id: str, region: str, status: str, plan_snapshot: dict, decision_reason: str = None, approved_by: str = None):
    query = """
    INSERT INTO procurement_decisions (plan_id, region, status, decision_reason, approved_by, plan_snapshot)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (plan_id) DO UPDATE SET
        status = EXCLUDED.status,
        decision_reason = EXCLUDED.decision_reason,
        approved_by = EXCLUDED.approved_by,
        plan_snapshot = EXCLUDED.plan_snapshot,
        decision_timestamp = CURRENT_TIMESTAMP
    """
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(query, (plan_id, region, status, decision_reason, approved_by, json.dumps(plan_snapshot)))

def get_procurement_decision(plan_id: str):
    query = "SELECT * FROM procurement_decisions WHERE plan_id = %s OR plan_snapshot->>'request_id' = %s LIMIT 1"
    with get_db_cursor() as cursor:
        cursor.execute(query, (plan_id, plan_id))
        return cursor.fetchone()

def list_procurement_decisions():
    query = "SELECT decision_id, plan_id, region, status, approved_by, decision_timestamp FROM procurement_decisions ORDER BY decision_timestamp DESC"
    with get_db_cursor() as cursor:
        cursor.execute(query)
        return cursor.fetchall()
