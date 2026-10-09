import pytest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from aemiif.parser_agent import RequirementParserAgent, normalize_weights, map_preference_to_weight, PreferenceLevel, LLMParsedResult, ParsedPreferences
from aemiif.schemas import UserParameters

def test_map_preference_to_weight():
    assert map_preference_to_weight(PreferenceLevel.VERY_HIGH) == 0.40
    assert map_preference_to_weight(PreferenceLevel.LOW) == 0.10
    assert map_preference_to_weight(PreferenceLevel.UNSPECIFIED) == 0.20

def test_normalize_weights():
    weights_dict = {
        "purchase_cost": 0.4,
        "transport_cost": 0.2,
        "holding_cost": 0.2,
        "stockout_cost": 0.2,
        "supplier_reliability": 0.0
    }
    normalized = normalize_weights(weights_dict)
    
    assert normalized.purchase_cost == 0.4
    assert normalized.transport_cost == 0.2
    assert normalized.holding_cost == 0.2
    assert normalized.stockout_cost == 0.2
    assert normalized.supplier_reliability == 0.0
    
    total = sum([normalized.purchase_cost, normalized.transport_cost, normalized.holding_cost, 
                 normalized.stockout_cost, normalized.supplier_reliability])
    assert round(total, 4) == 1.0

def test_budget_validation():
    parser = RequirementParserAgent()
    mock_result = LLMParsedResult(
        parameters=UserParameters(budget=-500.0),
        preferences=ParsedPreferences()
    )
    with pytest.raises(ValueError, match="Budget cannot be negative"):
        parser.parse_requirements("Mock request", mock_llm_result=mock_result)

def test_service_level_conversion():
    parser = RequirementParserAgent()
    mock_result = LLMParsedResult(
        parameters=UserParameters(min_service_level=95.0),
        preferences=ParsedPreferences()
    )
    config = parser.parse_requirements("Mock request", mock_llm_result=mock_result)
    assert config.parameters.min_service_level == 0.95
