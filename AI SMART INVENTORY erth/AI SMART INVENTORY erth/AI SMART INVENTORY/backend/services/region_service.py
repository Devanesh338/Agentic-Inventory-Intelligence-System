from database import get_db_cursor
from typing import List

def get_available_regions() -> List[str]:
    """Retrieve all available regions from the inventory table."""
    query = "SELECT DISTINCT region FROM inventory WHERE region IS NOT NULL ORDER BY region"
    try:
        with get_db_cursor() as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
            return [row['region'] for row in results]
    except Exception:
        return []
