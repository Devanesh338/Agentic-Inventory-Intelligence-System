from typing import Any, Dict
from app import run_aemiif_pipeline
from backend.schemas.api_responses import CanonicalOptimizationResponse
from aemiif.schemas import FinalAEMIIFResponse
import logging

logger = logging.getLogger(__name__)

def run_optimization(query: str, region: str) -> CanonicalOptimizationResponse:
    logger.info(f"Running AEMIIF pipeline for region={region} query={query}")
    final_response, result_state = run_aemiif_pipeline(query=query, region=region)
    from backend.services.mapper import map_state_to_canonical
    
    # Dump the LangGraph result state to a dictionary safely
    import json
    def fallback_serializer(obj):
        if hasattr(obj, 'model_dump'):
            return obj.model_dump()
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        return str(obj)

    # Use map_state_to_canonical to construct the canonical response
    state_dict = json.loads(json.dumps(result_state, default=fallback_serializer))
    response_dict = map_state_to_canonical(state_dict)
    
    # Persist the result in the database so analytics endpoints can retrieve it
    if final_response.plan_id:
        from database import save_procurement_decision
        from aemiif.schemas import ApprovalStatus
        save_procurement_decision(
            plan_id=final_response.plan_id,
            region=region,
            status=ApprovalStatus.PENDING_APPROVAL.value,
            plan_snapshot=response_dict
        )
    
    from backend.schemas.api_responses import CanonicalOptimizationResponse
    return CanonicalOptimizationResponse(**response_dict)
