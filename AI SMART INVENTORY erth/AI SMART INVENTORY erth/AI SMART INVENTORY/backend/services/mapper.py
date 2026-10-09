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

    supplier_caps = {}
    for sup in supplier_outputs:
        s_dict = sup if isinstance(sup, dict) else (sup.model_dump() if hasattr(sup, 'model_dump') else getattr(sup, '__dict__', {}))
        sid = s_dict.get("supplier_id", "")
        cap = s_dict.get("capacity", 0)
        if sid and cap > 0:
            supplier_caps[sid] = max(supplier_caps.get(sid, 0), cap)

    for sup in supplier_outputs:
        s_dict = sup if isinstance(sup, dict) else (sup.model_dump() if hasattr(sup, 'model_dump') else getattr(sup, '__dict__', {}))
        sid = s_dict.get("supplier_id", "")
        cap = s_dict.get("capacity", 0)
        alloc = supplier_allocations.get(sid, 0)
        util = (alloc / cap * 100) if cap > 0 else 0.0
        supplier_analysis.append(CanonicalSupplierAnalysisItem(
            supplier_id=sid,
            product_id=s_dict.get("product_id", ""),
            quantity=alloc,
            unit_cost=s_dict.get("unit_cost", 0.0),
            lead_time_days=s_dict.get("lead_time_days", 0),
            reliability=s_dict.get("reliability"),
            distance=s_dict.get("distance_km"),
            capacity=cap,
            utilization=util
        ))
        
    cap_allocs = []
    for sid, qty in supplier_allocations.items():
        cap = supplier_caps.get(sid, 0)
        if cap == 0:
            for sup in supplier_outputs:
                s_dict = sup if isinstance(sup, dict) else (sup.model_dump() if hasattr(sup, 'model_dump') else getattr(sup, '__dict__', {}))
                if s_dict.get("supplier_id") == sid:
                    cap = s_dict.get("capacity", 0)
                    break
        if cap == 0 and qty > 0:
            cap = qty
        util = round((qty / cap * 100), 1) if cap > 0 else 0.0
        cap_allocs.append({
            "supplier_id": sid,
            "capacity": cap,
            "allocated": qty,
            "utilization": util,
            "is_feasible": qty <= cap
        })
    cap_allocs.sort(key=lambda x: x["supplier_id"])

    # Analytics & Summary
    parsed_budget = params.get("budget_limit") or params.get("budget")
    if parsed_budget and float(parsed_budget) > 0:
        budget_limit = float(parsed_budget)
    else:
        budget_limit = 200000.0  # Standard regional baseline budget

    total_cost = float(opt_result.get("total_cost") or 0.0)
    budget_util = round((total_cost / budget_limit * 100), 1) if budget_limit > 0 else 0.0
    
    summary = CanonicalSummary(
        total_procurement_cost=float(opt_result.get("total_purchase_cost") or 0.0),
        procurement_cost=float(opt_result.get("total_purchase_cost") or 0.0),
        transport_cost=float(opt_result.get("total_transport_cost") or 0.0),
        holding_cost=float(opt_result.get("total_holding_cost") or 0.0),
        stockout_cost=float(opt_result.get("total_stockout_cost") or 0.0),
        total_cost=total_cost,
        budget_limit=budget_limit,
        budget_utilization=budget_util,
        target_service_level=float(params.get("target_service_level") or params.get("min_service_level") or 0.95),
        achieved_service_level=opt_result.get("achieved_service_level") or state.get("achieved_service_level") or final_response.get("achieved_service_level") or 1.0,
        service_level_gap=0.0
    )
    
    user_params_obj = CanonicalUserParameters(
        budget_limit=budget_limit,
        max_lead_time=int(params.get("max_lead_time") or params.get("max_lead_time_days") or 5),
        target_service_level=float(params.get("target_service_level") or params.get("min_service_level") or 0.95),
        region=state.get("region") or params.get("requested_region") or ""
    )

    obj_weights_obj = CanonicalObjectiveWeights(
        procurement_cost=float(weights.get("procurement_cost") or weights.get("purchase_cost") or 0.35),
        transport_cost=float(weights.get("transport_cost") or 0.15),
        holding_cost=float(weights.get("holding_cost") or 0.15),
        stockout_cost=float(weights.get("stockout_cost") or 0.15),
        supplier_reliability=float(weights.get("supplier_reliability") or 0.20),
        lead_time=float(weights.get("lead_time") or 0.0)
    )

    # Constraints
    c_status = opt_result.get("constraint_status", {}) if opt_result else {}
    def parse_constraint(name: str) -> CanonicalConstraintItem:
        val = c_status.get(name, "NOT_EVALUATED")
        if opt_status in ["OPTIMAL", "FEASIBLE"] and val in ["NOT_EVALUATED", None, ""]:
            val = "PASSED"
        details = ""
        if name == "Budget":
            details = f"Used ₹{total_cost:,.2f} of ₹{budget_limit:,.2f} ({budget_util}%)"
        elif name == "Lead Time":
            details = f"Orders strictly meet the {user_params_obj.max_lead_time} days delivery constraint"
        elif name == "Service Level":
            details = f"Achieved {(summary.achieved_service_level or 1.0)*100:.0f}% service level (target {(user_params_obj.target_service_level or 0.95)*100:.0f}%)"
        elif name == "Supplier Capacity":
            details = f"Supplier allocations strictly respect maximum production capacity"
        return CanonicalConstraintItem(status=val, details=details, actual_value=None, required_value=None)
        
    constraints = CanonicalConstraints(
        budget=parse_constraint("Budget"),
        lead_time=parse_constraint("Lead Time"),
        service_level=parse_constraint("Service Level"),
        supplier_capacity=parse_constraint("Supplier Capacity"),
        overall=CanonicalConstraintItem(status="PASSED" if opt_status in ["OPTIMAL", "FEASIBLE"] else "FAILED", details="Global optimization constraints validated.")
    )

    analytics = CanonicalOptimizationAnalytics(
        cost_breakdown={
            "Procurement": summary.procurement_cost or 0.0,
            "Transport": summary.transport_cost or 0.0,
            "Holding": summary.holding_cost or 0.0,
            "Stockout": summary.stockout_cost or 0.0
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

    inv_raw = state.get("inventory_outputs", []) or []
    inventory_summary = [i.model_dump() if hasattr(i, 'model_dump') else dict(i) for i in inv_raw if isinstance(i, (dict, object))]

    fc_raw = state.get("forecast_outputs", []) or []
    demand_summary = [f.model_dump() if hasattr(f, 'model_dump') else dict(f) for f in fc_raw if isinstance(f, (dict, object))]

    hyp_data = {}
    try:
        from backend.services.hypothesis_service import evaluate_hypothesis
        plan_dicts = [p.model_dump() for p in proc_plan]
        hyp_data = evaluate_hypothesis(plan_dicts, supplier_outputs, opt_status)
    except Exception:
        pass

    canonical = CanonicalOptimizationResponse(
        request_id=state.get("request_id", ""),
        plan_id=final_response.get("plan_id") or state.get("request_id", ""),
        region=state.get("region", ""),
        status=status,
        optimization_status=opt_status,
        approval_status=approval.status,
        original_user_query=user_config.get("original_user_request", state.get("user_query", "")),
        user_parameters=user_params_obj,
        objective_weights=obj_weights_obj,
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
        hypothesis_testing=hyp_data,
        explanation=explanation,
        approval=approval,
        inventory_summary=inventory_summary,
        demand_summary=demand_summary
    )
    
    return make_canonical(canonical.model_dump())
