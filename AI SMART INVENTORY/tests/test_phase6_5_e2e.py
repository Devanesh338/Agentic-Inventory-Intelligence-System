import pytest
import os
from aemiif.schemas import (
    FinalAEMIIFResponse,
    CapacityMode,
    UserParameters
)
from aemiif.parser_agent import LLMParsedResult, ParsedPreferences, PreferenceLevel
from app import run_aemiif_pipeline

# Ensure we have mocked credentials to not hit OpenAI accidentally during testing if keys aren't set
@pytest.fixture(autouse=True)
def ensure_mock_env(monkeypatch):
    if not os.getenv("OPENAI_API_KEY"):
        monkeypatch.setenv("OPENAI_API_KEY", "mock-key")

def test_e2e_standard_optimal(monkeypatch):
    """SCENARIO 1: Standard Optimal Execution"""
    # Mock LLM Parse Result for the Parser Agent
    def mock_parser_invoke(state):
        from aemiif.parser_agent import RequirementParserAgent
        config = RequirementParserAgent().parse_requirements(
            state.user_query,
            mock_llm_result=LLMParsedResult(
                parameters=UserParameters(budget=500000.0, max_lead_time_days=10, min_service_level=0.95),
                preferences=ParsedPreferences(purchase_cost=PreferenceLevel.VERY_HIGH)
            )
        )
        return {"user_config": config}
        
    import aemiif.graph
    monkeypatch.setattr(aemiif.graph, "node_parse_requirements", mock_parser_invoke)
    
    # We use a test region, assuming ingestion seeded the DB via conftest
    resp, state = run_aemiif_pipeline(
        query="Replenish with 5L budget",
        region="Chennai-North"
    )
    
    # The pipeline should complete optimally or feasibly (depends on test DB state, usually optimal)
    assert resp.status in ["OPTIMAL", "FEASIBLE"]
    assert len(resp.procurement_plan) > 0
    assert resp.cost_summary["total_cost"] <= 500000.0
    
def test_e2e_infeasible_budget(monkeypatch):
    """SCENARIO 4: Infeasible Budget Execution"""
    def mock_parser_invoke(state):
        from aemiif.parser_agent import RequirementParserAgent
        config = RequirementParserAgent().parse_requirements(
            state.user_query,
            mock_llm_result=LLMParsedResult(
                parameters=UserParameters(budget=10.0, max_lead_time_days=10, min_service_level=0.95),
                preferences=ParsedPreferences(purchase_cost=PreferenceLevel.VERY_HIGH)
            )
        )
        return {"user_config": config}
        
    import aemiif.graph
    monkeypatch.setattr(aemiif.graph, "node_parse_requirements", mock_parser_invoke)
    
    resp, state = run_aemiif_pipeline(
        query="Replenish with very low budget",
        region="Chennai-North"
    )
    
    # The budget of 10 INR should make it impossible to satisfy the 95% service level
    assert resp.status == "INFEASIBLE"
    assert not resp.procurement_plan
    
def test_e2e_infeasible_lead_time(monkeypatch):
    """SCENARIO 5: Infeasible Lead Time"""
    def mock_parser_invoke(state):
        from aemiif.parser_agent import RequirementParserAgent
        config = RequirementParserAgent().parse_requirements(
            state.user_query,
            mock_llm_result=LLMParsedResult(
                parameters=UserParameters(budget=500000.0, max_lead_time_days=1, min_service_level=0.95),
                preferences=ParsedPreferences(purchase_cost=PreferenceLevel.VERY_HIGH)
            )
        )
        return {"user_config": config}
        
    import aemiif.graph
    monkeypatch.setattr(aemiif.graph, "node_parse_requirements", mock_parser_invoke)
    
    resp, state = run_aemiif_pipeline(
        query="Need this tomorrow",
        region="Chennai-North"
    )
    
    # 1-day lead time is below all suppliers
    assert resp.status == "NO_ELIGIBLE_SUPPLIERS"
    assert not resp.procurement_plan
