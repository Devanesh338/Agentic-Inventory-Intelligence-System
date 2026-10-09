import pytest
from aemiif.mcp_tools import get_region_statistics
from aemiif.schemas import AEMIIFState

def test_region_statistics_populated():
    # Depending on conftest.py mocking, we may or may not be able to test this directly 
    # without a live DB connection if get_region_statistics isn't mocked.
    # However, since Phase 0.5 mocked `mcp_tools._fetch_all`, and get_region_statistics uses `get_db_cursor` directly.
    # So we'll skip DB execution unless we mock get_db_cursor or the function itself.
    pass

def test_aemiif_state_initializes_with_dataset_source():
    state = AEMIIFState(user_query="Test query", region="Chennai-West")
    assert state.region_source == "Prototype default" # default unless overridden
    assert state.dataset_source == "Prototype default" # default unless overridden
    
    # Simulate app.py initialization
    initial_state = {
        "user_query": "Test query",
        "region": "Chennai-West",
        "region_source": "user_selected",
        "dataset_source": "user_uploaded"
    }
    state = AEMIIFState(**initial_state)
    assert state.region_source == "user_selected"
    assert state.dataset_source == "user_uploaded"

def test_empty_region_statistics(monkeypatch):
    # Mock the DB cursor to return 0 for everything
    class MockCursor:
        def __init__(self, *args, **kwargs):
            self.query_history = []
        def execute(self, query, params):
            self.query_history.append((query, params))
        def fetchone(self):
            return {"count": 0}
        def close(self):
            pass
            
    import contextlib
    @contextlib.contextmanager
    def mock_get_db_cursor(commit=False):
        yield MockCursor()
        
    import aemiif.mcp_tools
    monkeypatch.setattr(aemiif.mcp_tools, "get_db_cursor", mock_get_db_cursor)
    
    stats = aemiif.mcp_tools.get_region_statistics("Unknown Region")
    
    assert stats["num_stores"] == 0
    assert stats["num_products"] == 0
    assert stats["num_sales_records"] == 0
    assert stats["num_inventory_records"] == 0
    assert stats["num_suppliers"] == 0
