import os
from enum import Enum
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from .schemas import UserParameters, ObjectiveWeights, UserDecisionConfig

load_dotenv()

class PreferenceLevel(str, Enum):
    VERY_LOW = "VERY_LOW"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"
    UNSPECIFIED = "UNSPECIFIED"

class ParsedPreferences(BaseModel):
    """Raw preference levels extracted from user text."""
    purchase_cost: PreferenceLevel = Field(default=PreferenceLevel.UNSPECIFIED, description="Importance of purchase cost.")
    transport_cost: PreferenceLevel = Field(default=PreferenceLevel.UNSPECIFIED, description="Importance of transport cost.")
    holding_cost: PreferenceLevel = Field(default=PreferenceLevel.UNSPECIFIED, description="Importance of holding cost.")
    stockout_cost: PreferenceLevel = Field(default=PreferenceLevel.UNSPECIFIED, description="Importance of avoiding stockouts.")
    supplier_reliability: PreferenceLevel = Field(default=PreferenceLevel.UNSPECIFIED, description="Importance of supplier reliability.")

class LLMParsedResult(BaseModel):
    """The raw structure returned by the LLM."""
    parameters: UserParameters
    preferences: ParsedPreferences
    objective_mode: Optional[str] = Field(None, description="General objective mode if specified (e.g. 'MINIMIZE_COST', 'MAXIMIZE_RELIABILITY').")

def map_preference_to_weight(level: PreferenceLevel) -> float:
    """Deterministic mapping of qualitative preference to numerical weight."""
    mapping = {
        PreferenceLevel.VERY_LOW: 0.05,
        PreferenceLevel.LOW: 0.10,
        PreferenceLevel.MEDIUM: 0.20,
        PreferenceLevel.HIGH: 0.30,
        PreferenceLevel.VERY_HIGH: 0.40,
        PreferenceLevel.UNSPECIFIED: 0.20
    }
    return mapping.get(level, 0.20)

def normalize_weights(weights_dict: Dict[str, float]) -> ObjectiveWeights:
    """Normalizes a dictionary of weights so they sum to 1."""
    total = sum(weights_dict.values())
    if total == 0:
        # Fallback to equal weights
        total = 1.0
        for k in weights_dict:
            weights_dict[k] = 1.0 / len(weights_dict)
            
    normalized = {k: round(v / total, 4) for k, v in weights_dict.items()}
    return ObjectiveWeights(**normalized)

class RequirementParserAgent:
    def __init__(self, model_name: str = "gpt-4o-mini"):
        # We will use ChatOpenAI. If no key, we will raise an error early.
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            # We allow mocking for tests if API key is not present, but for production it's needed
            self.llm = None
        else:
            self.llm = ChatOpenAI(model=model_name, temperature=0)
            
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are the Requirement Parser for the AEMIIF procurement system.
Your job is ONLY to extract HARD constraints (parameters) and SOFT preferences from the user's natural language request.
NEVER invent mathematical formulas. NEVER select suppliers or quantities.
- Hard constraints (like budget, max_lead_time_days < 5, min_service_level) go into UserParameters.
- Soft preferences ("cost is very important", "i don't care about transport") go into ParsedPreferences using the PreferenceLevel enum.
- If a user says "budget is 10000", that is a hard parameter, NOT a soft preference.
- Do NOT convert hard constraints into soft preferences."""),
            ("user", "{user_request}")
        ])

    def parse_requirements(self, user_request: str, mock_llm_result: Optional[LLMParsedResult] = None) -> UserDecisionConfig:
        """Parse natural language into structured config with deterministic weights."""
        if not user_request.strip():
            raise ValueError("Empty user request provided.")

        if mock_llm_result:
            llm_result = mock_llm_result
        else:
            if not self.llm:
                raise ValueError("OPENAI_API_KEY not set. Cannot run LLM parser without mock.")
            chain = self.prompt | self.llm.with_structured_output(LLMParsedResult)
            llm_result = chain.invoke({"user_request": user_request})

        # Validate hard parameters
        if llm_result.parameters.budget is not None and llm_result.parameters.budget < 0:
            raise ValueError("Budget cannot be negative.")
        if llm_result.parameters.min_service_level is not None:
            if not (0 <= llm_result.parameters.min_service_level <= 1.0) and llm_result.parameters.min_service_level <= 100:
                if llm_result.parameters.min_service_level > 1:
                     llm_result.parameters.min_service_level /= 100.0 # Convert 95 to 0.95

        # Deterministic weight interpretation
        raw_weights = {
            "purchase_cost": map_preference_to_weight(llm_result.preferences.purchase_cost),
            "transport_cost": map_preference_to_weight(llm_result.preferences.transport_cost),
            "holding_cost": map_preference_to_weight(llm_result.preferences.holding_cost),
            "stockout_cost": map_preference_to_weight(llm_result.preferences.stockout_cost),
            "supplier_reliability": map_preference_to_weight(llm_result.preferences.supplier_reliability),
        }
        
        final_weights = normalize_weights(raw_weights)

        config = UserDecisionConfig(
            parameters=llm_result.parameters,
            weights=final_weights,
            objective_mode=llm_result.objective_mode,
            original_user_request=user_request
        )
        return config
