from fastapi import APIRouter
from typing import List
from backend.services.region_service import get_available_regions

router = APIRouter(tags=["Regions"])

@router.get("/regions", response_model=List[str])
def list_regions():
    return get_available_regions()
