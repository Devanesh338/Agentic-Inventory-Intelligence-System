from fastapi import APIRouter, HTTPException
from database import get_procurement_decision
from typing import Any, Dict
from backend.services.hypothesis_service import evaluate_hypothesis
from aemiif.mcp_tools import get_supplier_options

router = APIRouter(tags=["Analytics"])

def get_snapshot(request_id: str) -> Dict[str, Any]:
    decision = get_procurement_decision(request_id)
    if not decision or not decision.get("plan_snapshot"):
        raise HTTPException(status_code=404, detail="Analysis result not found")
    return decision["plan_snapshot"]

@router.get("/overview/{request_id}")
def get_overview(request_id: str):
    snapshot = get_snapshot(request_id)
    return {
        "status": snapshot.get("optimization_status"),
        "summary": snapshot.get("explanation", {}).get("summary", ""),
        "cost_summary": snapshot.get("summary", {}),
        "achieved_service_level": snapshot.get("summary", {}).get("achieved_service_level")
    }

@router.get("/procurement/{request_id}")
def get_procurement_plan(request_id: str):
    snapshot = get_snapshot(request_id)
    return {
        "procurement_plan": snapshot.get("procurement_plan", []),
        "approval_status": snapshot.get("approval_status"),
        "total_cost": snapshot.get("summary", {}).get("total_cost")
    }

@router.get("/demand-inventory/{request_id}")
def get_demand_inventory(request_id: str):
    # This was previously returning demand_summary and inventory_summary.
    # We can reconstruct it or return it if it was saved.
    # For now, let's keep it working if they exist, but the master prompt didn't ask to rewrite this specific backend data format if frontend doesn't need it.
    snapshot = get_snapshot(request_id)
    # Master prompt didn't ask to change the shape of demand_summary, just procurement etc.
    return {
        "demand_summary": snapshot.get("demand_summary", []),
        "inventory_summary": snapshot.get("inventory_summary", [])
    }

@router.get("/suppliers/{request_id}")
def get_suppliers_analysis(request_id: str):
    snapshot = get_snapshot(request_id)
    return {"supplier_analysis": snapshot.get("supplier_analysis", [])}

@router.get("/capacity/{request_id}")
def get_capacity_intelligence(request_id: str):
    snapshot = get_snapshot(request_id)
    return {"capacity_summary": snapshot.get("capacity", {})}

@router.get("/requirements/{request_id}")
def get_requirements(request_id: str):
    snapshot = get_snapshot(request_id)
    return {
        "user_requirements": snapshot.get("user_parameters", {}),
        "objective_weights": snapshot.get("objective_weights", {}),
        "original_user_query": snapshot.get("original_user_query", ""),
        "region": snapshot.get("region", "")
    }

@router.get("/constraints/{request_id}")
def get_constraints(request_id: str):
    snapshot = get_snapshot(request_id)
    return {"constraint_summary": snapshot.get("constraints", {})}

@router.get("/optimization/{request_id}")
def get_optimization(request_id: str):
    snapshot = get_snapshot(request_id)
    return {
        "status": snapshot.get("optimization_status"),
        "cost_summary": snapshot.get("summary", {}),
        "analytics": snapshot.get("optimization_analytics", {})
    }

@router.get("/hypothesis/{request_id}")
def get_hypothesis(request_id: str):
    try:
        snapshot = get_snapshot(request_id)
        if snapshot.get("hypothesis_testing") and snapshot["hypothesis_testing"].get("is_valid") is not None:
            return snapshot["hypothesis_testing"]
            
        plan_items = snapshot.get("procurement_plan", [])
        status = snapshot.get("optimization_status")
        
        decision = get_procurement_decision(request_id)
        region = decision['region'] if decision else snapshot.get("region", "Chennai-Central")
        
        sups = get_supplier_options(region)
        return evaluate_hypothesis(plan_items, sups, status)
    except Exception as e:
        import logging
        logging.exception(f"Failed to evaluate hypothesis for {request_id}: {e}")
        return {
            "is_valid": False,
            "message": f"Hypothesis testing analysis unavailable: {str(e)}"
        }

@router.get("/explanation/{request_id}")
def get_explanation(request_id: str):
    snapshot = get_snapshot(request_id)
    return {
        "explanation": snapshot.get("explanation", {}).get("rationale", ""),
        "approval_status": snapshot.get("approval_status")
    }
