from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import get_procurement_decision, save_procurement_decision
import datetime

router = APIRouter(tags=["Approval"])

class ApprovalRequest(BaseModel):
    approved_by: Optional[str] = "admin"
    comment: Optional[str] = None

class RejectionRequest(BaseModel):
    rejected_by: Optional[str] = "admin"
    reason: str

@router.post("/{request_id}/approve")
def approve_plan(request_id: str, payload: ApprovalRequest):
    decision = get_procurement_decision(request_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
        
    snapshot = decision.get("plan_snapshot", {})
    opt_status = snapshot.get("optimization_status")
    
    if opt_status not in ["OPTIMAL", "FEASIBLE"]:
        raise HTTPException(status_code=400, detail=f"Cannot approve plan with optimization status {opt_status}")
        
    current_status = snapshot.get("approval_status", decision.get("status"))
    if current_status == "APPROVED":
        return {"status": "success", "message": "Already approved", "approval_status": "APPROVED"}
        
    # Update DB
    snapshot["approval_status"] = "APPROVED"
    if "approval" not in snapshot:
        snapshot["approval"] = {}
    snapshot["approval"]["status"] = "APPROVED"
    snapshot["approval"]["approved_by"] = payload.approved_by
    snapshot["approval"]["approved_at"] = datetime.datetime.utcnow().isoformat()
    snapshot["approval"]["rejection_reason"] = None
    
    save_procurement_decision(
        plan_id=request_id,
        region=decision["region"],
        status="APPROVED",
        plan_snapshot=snapshot,
        decision_reason=payload.comment,
        approved_by=payload.approved_by
    )
    
    return {"status": "success", "approval_status": "APPROVED"}

@router.post("/{request_id}/reject")
def reject_plan(request_id: str, payload: RejectionRequest):
    decision = get_procurement_decision(request_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
        
    snapshot = decision.get("plan_snapshot", {})
    
    current_status = snapshot.get("approval_status", decision.get("status"))
    if current_status == "REJECTED":
        return {"status": "success", "message": "Already rejected", "approval_status": "REJECTED"}
    
    # Update DB
    snapshot["approval_status"] = "REJECTED"
    
    if "approval" not in snapshot:
        snapshot["approval"] = {}
    snapshot["approval"]["status"] = "REJECTED"
    snapshot["approval"]["rejection_reason"] = payload.reason
    
    save_procurement_decision(
        plan_id=request_id,
        region=decision["region"],
        status="REJECTED",
        plan_snapshot=snapshot,
        decision_reason=payload.reason,
        approved_by=payload.rejected_by
    )
    
    return {"status": "success", "approval_status": "REJECTED"}
