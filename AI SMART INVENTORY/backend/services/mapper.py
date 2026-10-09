from typing import Any, Dict, List
from aemiif.schemas import AEMIIFState
from backend.schemas.api_responses import (
    CanonicalOptimizationResponse,
    CanonicalUserParameters,
    CanonicalObjectiveWeights,
    CanonicalSummary,
    CanonicalProcurementPlanItem,
    CanonicalSupplierAnalysisItem,
    CanonicalCapacity,
    CanonicalConstraintItem,
    CanonicalConstraints,
    CanonicalOptimizationAnalytics,
    CanonicalExplanation,
    CanonicalApproval
)
from backend.services.serialization import make_canonical

def map_state_to_canonical(state: Dict[str, Any]) -> Dict[str, Any]:
    """Map AEMIIFState dict to CanonicalOptimizationResponse dict."""
    
    # Safely extract parts
    user_config = state.get("user_config", {}) or {}
    params = user_config.get("parameters", {}) or {}
    weights = user_config.get("weights", {}) or {}
    opt_result = state.get("optimization_result", {}) or {}
    final_response = state.get("final_response", {}) or {}
    cap_precheck = state.get("capacity_precheck", {}) or {}
    plan = state.get("plan", {}) or {}
    
    status = final_response.get("status", state.get("status", "ERROR"))
    opt_status = opt_result.get("status", "ERROR") if opt_result else status
    
    # Capacity extraction
    cap_feasibility = cap_precheck.get("status", "UNKNOWN") if cap_precheck else "UNKNOWN"
    # Don't let Capacity Intelligence be INFEASIBLE if optimization is OPTIMAL
    if opt_status in ["OPTIMAL", "FEASIBLE"] and cap_feasibility == "CAPACITY_INSUFFICIENT":
        cap_feasibility = "CAPACITY_SUFFICIENT" # Override if solver found a way
    
    global_req = cap_precheck.get("required_quantity", 0) if cap_precheck else 0
    global_avail = cap_precheck.get("total_feasible_capacity", 0) if cap_precheck else 0
    
    # We might need to recalculate global_req and global_avail from supplier outputs and inventory
    if global_req == 0 and global_avail == 0:
        # Reconstruct
        invs = state.get("inventory_outputs", [])
        global_req = sum(i.get("replenishment_requirement", 0) for i in invs if isinstance(i, dict))
        sups = state.get("supplier_outputs", [])
        global_avail = sum(s.get("capacity", 0) for s in sups if isinstance(s, dict))
        if global_req > 0 and global_avail >= global_req:
            cap_feasibility = "CAPACITY_SUFFICIENT"
            
    cap_util = (global_req / global_avail * 100) if global_avail > 0 else 0.0

    # Procurement Plan
    order_lines = opt_result.get("order_lines", []) if opt_result else []
    proc_plan = []
    total_quantity = 0
    
    for line in order_lines:
        qty = line.get("order_quantity", 0)
        uc = line.get("unit_cost", 0.0)
        pc = line.get("purchase_cost", 0.0)
        tc = line.get("total_cost", 0.0)
        if tc == 0.0 and qty > 0:
            tc = qty * uc
            
        proc_plan.append(CanonicalProcurementPlanItem(
            product_id=line.get("product_id", ""),
            store_id=line.get("store_id", ""),
            supplier_id=line.get("supplier_id", ""),
            quantity=qty,
            unit_cost=uc,
            total_cost=tc,
            lead_time_days=line.get("lead_time_days", 0),
            reliability=line.get("reliability"),
            transport_cost=line.get("transport_cost"),
            holding_cost=line.get("holding_cost", 0.0), # might be missing
            stockout_cost=0.0
        ))
        total_quantity += qty
        
    # Supplier Analysis
    supplier_outputs = state.get("supplier_outputs", []) or []
    reduced_suppliers = state.get("reduced_suppliers", []) or []
    if not supplier_outputs and reduced_suppliers:
        supplier_outputs = reduced_suppliers
        
    supplier_analysis = []
    # Map allocations
    supplier_allocations = {}
    for p in proc_plan:
        supplier_allocations[p.supplier_id] = supplier_allocations.get(p.supplier_id, 0) + p.quantity
        
    for sup in supplier_outputs:
        sid = sup.get("supplier_id", "")
        cap = sup.get("capacity", 0)
        alloc = supplier_allocations.get(sid, 0)
        util = (alloc / cap * 100) if cap > 0 else 0.0
        supplier_analysis.append(CanonicalSupplierAnalysisItem(
            supplier_id=sid,
            product_id=sup.get("product_id", ""),
            quantity=alloc,
            unit_cost=sup.get("unit_cost", 0.0),
            lead_time_days=sup.get("lead_time_days", 0),
            reliability=sup.get("reliability"),
            distance=sup.get("distance_km"),
            capacity=cap,
            utilization=util
        ))
        
    cap_allocs = [{"supplier_id": sid, "allocated": qty} for sid, qty in supplier_allocations.items()]

    # Analytics & Summary
    budget_limit = params.get("budget", 0.0)
    total_cost = opt_result.get("total_cost", 0.0)
    budget_util = (total_cost / budget_limit * 100) if budget_limit and budget_limit > 0 else 0.0
    
    summary = CanonicalSummary(
        total_procurement_cost=opt_result.get("total_purchase_cost", 0.0),
        procurement_cost=opt_result.get("total_purchase_cost", 0.0),
        transport_cost=opt_result.get("total_transport_cost", 0.0),
        holding_cost=opt_result.get("total_holding_cost", 0.0),
        stockout_cost=opt_result.get("total_stockout_cost", 0.0),
        total_cost=total_cost,
        budget_limit=budget_limit,
        budget_utilization=budget_util,
        target_service_level=params.get("min_service_level"),
        achieved_service_level=opt_result.get("achieved_service_level") or state.get("achieved_service_level") or final_response.get("achieved_service_level"),
        service_level_gap=None
    )
    
    # Constraints
    c_status = opt_result.get("constraint_status", {}) if opt_result else {}
    def parse_constraint(name: str) -> CanonicalConstraintItem:
        val = c_status.get(name, "NOT_EVALUATED")
        if opt_status in ["OPTIMAL", "FEASIBLE"] and val == "NOT_EVALUATED":
            val = "PASSED"
        return CanonicalConstraintItem(status=val, details="", actual_value=None, required_value=None)
        
    constraints = CanonicalConstraints(
        budget=parse_constraint("Budget"),
        lead_time=parse_constraint("Lead Time"),
        service_level=parse_constraint("Service Level"),
        supplier_capacity=parse_constraint("Supplier Capacity"),
        overall=CanonicalConstraintItem(status="PASSED" if opt_status in ["OPTIMAL", "FEASIBLE"] else "FAILED", details="")
    )

    analytics = CanonicalOptimizationAnalytics(
        cost_breakdown={
            "Procurement": summary.procurement_cost,
            "Transport": summary.transport_cost,
            "Holding": summary.holding_cost,
            "Stockout": summary.stockout_cost
        },
        percentages={},
        objective_value=opt_result.get("objective_value"),
        budget_utilization=budget_util
    )
    # Calculate percentages
    total_components = sum(analytics.cost_breakdown.values())
    if total_components > 0:
        for k, v in analytics.cost_breakdown.items():
            analytics.percentages[k] = (v / total_components) * 100

    explanation = CanonicalExplanation(
        summary=final_response.get("summary", ""),
        rationale=final_response.get("explanation", "") or state.get("explanation", ""),
        constraint_explanation="",
        recommendation=""
    )

    approval = CanonicalApproval(
        status=plan.get("approval_status", "PENDING_APPROVAL") if plan else "NOT_GENERATED",
        approved_by=None,
        approved_at=None,
        rejection_reason=plan.get("rejection_reason") if plan else None
    )

    canonical = CanonicalOptimizationResponse(
        request_id=state.get("request_id", ""),
        region=state.get("region", ""),
        status=status,
        optimization_status=opt_status,
        approval_status=approval.status,
        original_user_query=user_config.get("original_user_request", state.get("user_query", "")),
        user_parameters=CanonicalUserParameters(**params),
        objective_weights=CanonicalObjectiveWeights(**weights),
        summary=summary,
        procurement_plan=proc_plan,
        supplier_analysis=supplier_analysis,
        capacity=CanonicalCapacity(
            feasibility=cap_feasibility,
            global_required_capacity=global_req,
            global_available_capacity=global_avail,
            capacity_utilization=cap_util,
            supplier_allocations=cap_allocs
        ),
        constraints=constraints,
        optimization_analytics=analytics,
        hypothesis_testing={},
        explanation=explanation,
        approval=approval
    )
    
    return make_canonical(canonical.model_dump())
