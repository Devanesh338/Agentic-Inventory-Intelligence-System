from fastapi import APIRouter, HTTPException
from backend.schemas.api_responses import APIOptimizationRunRequest, CanonicalOptimizationResponse
from backend.services.aemiif_runner import run_optimization

router = APIRouter(tags=["Optimization"])

@router.post("/run", response_model=CanonicalOptimizationResponse)
def run_optimization_endpoint(request: APIOptimizationRunRequest):
    try:
        return run_optimization(query=request.user_query, region=request.region)
    except Exception as e:
        import logging
        logging.exception("Optimization failed")
        raise HTTPException(status_code=500, detail="An unexpected error occurred during optimization.")
