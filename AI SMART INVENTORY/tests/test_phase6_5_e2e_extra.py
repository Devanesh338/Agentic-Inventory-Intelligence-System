import pytest
import os
from aemiif.schemas import (
    FinalAEMIIFResponse,
    CapacityMode,
    UserParameters
)
from aemiif.parser_agent import LLMParsedResult, ParsedPreferences, PreferenceLevel
from app import run_aemiif_pipeline

@pytest.fixture(autouse=True)
def ensure_mock_env(monkeypatch):
    if not os.getenv("OPENAI_API_KEY"):
        monkeypatch.setenv("OPENAI_API_KEY", "mock-key")

def test_e2e_strict_capacity_infeasible(monkeypatch):
    """SCENARIO 2: Strict Capacity Infeasible"""
    def mock_parser_invoke(state):
        from aemiif.parser_agent import RequirementParserAgent
        from aemiif.schemas import CapacityMode
        config = RequirementParserAgent().parse_requirements(
            state.user_query,
            mock_llm_result=LLMParsedResult(
                parameters=UserParameters(budget=500000.0, max_lead_time_days=10, capacity_mode=CapacityMode.STRICT_HARD_CAP),
                preferences=ParsedPreferences(purchase_cost=PreferenceLevel.VERY_HIGH)
            )
        )
        return {"user_config": config}
        
    import aemiif.graph
    monkeypatch.setattr(aemiif.graph, "node_parse_requirements", mock_parser_invoke)
    
    # We mock run_supplier to return suppliers with VERY low capacity
    def mock_supplier_run(self, region, *args, **kwargs):
        from aemiif.schemas import SupplierOption
        product_id = kwargs.get("product_id") or "P006"
        return [
            SupplierOption(supplier_id="SUP_1", region=region, product_id=product_id or "P006", unit_cost=10, moq=1, lead_time_days=2, reliability=0.99, capacity=10, feasibility_status="feasible"),
            SupplierOption(supplier_id="SUP_2", region=region, product_id=product_id or "P006", unit_cost=10, moq=1, lead_time_days=2, reliability=0.99, capacity=10, feasibility_status="feasible")
        ]
    from aemiif.agents import SupplierAgent
    monkeypatch.setattr(SupplierAgent, "run", mock_supplier_run)
    
    resp, state = run_aemiif_pipeline(
        query="Strict cap mode",
        region="Chennai-North"
    )
    
    assert resp.status == "CAPACITY_INSUFFICIENT"
    assert not resp.procurement_plan

def test_e2e_proportional_capacity(monkeypatch):
    """SCENARIO 3: Proportional Capacity Mode"""
    def mock_parser_invoke(state):
        from aemiif.parser_agent import RequirementParserAgent
        from aemiif.schemas import CapacityMode
        config = RequirementParserAgent().parse_requirements(
            state.user_query,
            mock_llm_result=LLMParsedResult(
                parameters=UserParameters(budget=500000.0, max_lead_time_days=10, capacity_mode=CapacityMode.PROPORTIONAL),
                preferences=ParsedPreferences(purchase_cost=PreferenceLevel.VERY_HIGH)
            )
        )
        return {"user_config": config}
        
    import aemiif.graph
    monkeypatch.setattr(aemiif.graph, "node_parse_requirements", mock_parser_invoke)
    
    resp, state = run_aemiif_pipeline(
        query="Proportional mode",
        region="Chennai-North"
    )
    
    assert resp.status in ["OPTIMAL", "FEASIBLE"]
    assert state["capacity_precheck"].mode == CapacityMode.PROPORTIONAL
