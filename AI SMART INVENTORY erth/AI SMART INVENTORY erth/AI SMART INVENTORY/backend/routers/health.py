from fastapi import APIRouter
from backend.schemas.api_responses import APIHealthResponse

router = APIRouter(tags=["Health"])

@router.get("/health", response_model=APIHealthResponse)
def health_check():
    return APIHealthResponse(status="ok", service="AEMIIF Backend")
