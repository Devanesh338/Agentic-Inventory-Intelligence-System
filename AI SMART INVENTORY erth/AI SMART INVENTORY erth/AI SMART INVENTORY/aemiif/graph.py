import time
import os
import re
import logging
from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, START, END

from .schemas import (
    AEMIIFState, UserParameters,
    UserDecisionConfig, CapacityMode, CapacityStatus, OptimizationInput,
    OptimizationResult, FinalAEMIIFResponse
)
from .parser_agent import RequirementParserAgent, LLMParsedResult, ParsedPreferences, PreferenceLevel
from .agents import ForecastAgent, InventoryAgent, SupplierAgent
from .capacity_intelligence import precheck_capacity
from .optimization import build_optimization_input as build_opt_input, solve_procurement_problem
from .validation import post_validate_optimization
from .explanation_agent import ExplanationAgent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


# ============================================================
# HELPER: RULE-BASED FALLBACK PARSER
# ============================================================

def _fallback_parse_query(query: str) -> LLMParsedResult:
    """
    Deterministic rule-based extractor when no LLM API key is present
    and no mock_llm_result is explicitly injected.
    """
    params = UserParameters()
    prefs = ParsedPreferences()

    q_lower = query.lower()

    # 1. Budget extraction (e.g. "budget of ₹200000", "budget of 100000", "budget 50000")
    budget_match = re.search(r'budget\s*(?:of|is|:)?\s*(?:₹|rs\.?|inr)?\s*(\d+(?:,\d+)*(?:\.\d+)?)', q_lower)
    if not budget_match:
        budget_match = re.search(r'(?:₹|rs\.?|inr)\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*budget', q_lower)
    if budget_match:
        val_str = budget_match.group(1).replace(',', '')
        params.budget = float(val_str)

    # 2. Max lead time extraction (e.g. "within 5 days", "lead time 10 days")
    lead_time_match = re.search(r'(?:within|lead\s*time\s*(?:of|is|:)?)\s*(\d+)\s*days?', q_lower)
    if lead_time_match:
        params.max_lead_time_days = int(lead_time_match.group(1))

    # 3. Service level extraction (e.g. "95 percent service level", "service level 90%")
    sl_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:percent|%)\s*service\s*level', q_lower)
    if not sl_match:
        sl_match = re.search(r'service\s*level\s*(?:of|is|:)?\s*(\d+(?:\.\d+)?)\s*(?:percent|%)?', q_lower)
    if sl_match:
        sl_val = float(sl_match.group(1))
        params.min_service_level = sl_val / 100.0 if sl_val > 1.0 else sl_val

    # 4. Capacity mode extraction
    if "strict_hard_cap" in q_lower or "strict capacity" in q_lower or "hard cap" in q_lower:
        params.capacity_mode = CapacityMode.STRICT_HARD_CAP
    elif "proportional" in q_lower:
        params.capacity_mode = CapacityMode.PROPORTIONAL

    # 5. Preferences
    if "cost is very important" in q_lower or "low cost" in q_lower:
        prefs.purchase_cost = PreferenceLevel.VERY_HIGH
    elif "cost" in q_lower:
        prefs.purchase_cost = PreferenceLevel.HIGH

    if "reliability is also important" in q_lower or "reliable supplier" in q_lower:
        prefs.supplier_reliability = PreferenceLevel.HIGH

    if "avoiding stockouts is extremely critical" in q_lower or "stockout" in q_lower:
        prefs.stockout_cost = PreferenceLevel.VERY_HIGH

    return LLMParsedResult(parameters=params, preferences=prefs)


# ============================================================
# GRAPH NODES
# ============================================================

def node_parse_requirements(state: AEMIIFState) -> Dict[str, Any]:
    """Node 1: Parse natural language user request into UserDecisionConfig."""
    t0 = time.time()
    req_id = state.request_id or f"req_{int(time.time()*1000)}"
    logger.info(f"[{req_id}] Node: parse_requirements started.")
    times = dict(state.execution_times)

    if not state.user_query or not state.user_query.strip():
        times["parse_requirements"] = round(time.time() - t0, 4)
        return {
            "request_id": req_id,
            "status": "ERROR",
            "errors": state.errors + ["Empty or missing user_query."],
            "execution_times": times
        }

    try:
        # If user_config was already explicitly provided, respect it
        if state.user_config:
            config = state.user_config
        else:
            parser = RequirementParserAgent()
            api_key = os.getenv("OPENAI_API_KEY")

            if state.mock_llm_result:
                config = parser.parse_requirements(state.user_query, mock_llm_result=state.mock_llm_result)
            elif api_key:
                config = parser.parse_requirements(state.user_query)
            else:
                fallback_result = _fallback_parse_query(state.user_query)
                config = parser.parse_requirements(state.user_query, mock_llm_result=fallback_result)

        # Resolve region
        if state.region:
            region = state.region
            region_source = "User specified"
        elif config.parameters.requested_region:
            region = config.parameters.requested_region
            region_source = "User specified"
        else:
            region = "Demo Region"
            region_source = "Prototype default"
            
        # Optional product/store filters
        product_id = state.product_id
        store_id = state.store_id

        times["parse_requirements"] = round(time.time() - t0, 4)
        logger.info(f"[{req_id}] Node: parse_requirements succeeded for region={region} ({region_source}).")
        return {
            "request_id": req_id,
            "user_config": config,
            "region": region,
            "region_source": region_source,
            "product_id": product_id,
            "store_id": store_id,
            "status": "PARSED",
            "execution_times": times
        }
    except Exception as e:
        logger.error(f"[{state.request_id}] Node: parse_requirements failed: {e}")
        times["parse_requirements"] = round(time.time() - t0, 4)
        return {
            "status": "ERROR",
            "errors": state.errors + [f"Requirement Parser failed: {str(e)}"],
            "execution_times": times
        }


def node_run_forecast(state: AEMIIFState) -> Dict[str, Any]:
    """Node 2: Forecast demand using ForecastAgent."""
    t0 = time.time()
    logger.info(f"[{state.request_id}] Node: run_forecast started.")
    times = dict(state.execution_times)

    if state.status == "ERROR":
        return {}

    if state.forecast_outputs:
        times["run_forecast"] = round(time.time() - t0, 4)
        return {"execution_times": times}

    try:
        agent = ForecastAgent()
        forecasts = agent.run(state.region, state.product_id, state.store_id)
        times["run_forecast"] = round(time.time() - t0, 4)
        logger.info(f"[{state.request_id}] Node: run_forecast produced {len(forecasts)} forecasts.")
        return {
            "forecast_outputs": forecasts,
            "execution_times": times
        }
    except Exception as e:
        logger.error(f"[{state.request_id}] Node: run_forecast failed: {e}")
        times["run_forecast"] = round(time.time() - t0, 4)
        return {
            "status": "ERROR",
            "errors": state.errors + [f"Forecast Agent failed: {str(e)}"],
            "execution_times": times
        }


def node_run_inventory(state: AEMIIFState) -> Dict[str, Any]:
    """Node 3: Calculate deterministic inventory indicators using InventoryAgent."""
    t0 = time.time()
    logger.info(f"[{state.request_id}] Node: run_inventory started.")
    times = dict(state.execution_times)

    if state.status == "ERROR":
        return {}

    if state.inventory_outputs:
        times["run_inventory"] = round(time.time() - t0, 4)
        return {"execution_times": times}

    try:
        forecasts = state.forecast_outputs if state.forecast_outputs else []
        agent = InventoryAgent()
        inventories = agent.run(state.region, forecasts, state.product_id, state.store_id)
        times["run_inventory"] = round(time.time() - t0, 4)
        logger.info(f"[{state.request_id}] Node: run_inventory produced {len(inventories)} inventory metrics.")
        return {
            "inventory_outputs": inventories,
            "execution_times": times
        }
    except Exception as e:
        logger.error(f"[{state.request_id}] Node: run_inventory failed: {e}")
        times["run_inventory"] = round(time.time() - t0, 4)
        return {
            "status": "ERROR",
            "errors": state.errors + [f"Inventory Agent failed: {str(e)}"],
            "execution_times": times
        }


def node_run_supplier(state: AEMIIFState) -> Dict[str, Any]:
    """Node 4: Filter and evaluate feasible supplier options using SupplierAgent."""
    t0 = time.time()
    logger.info(f"[{state.request_id}] Node: run_supplier started.")
    times = dict(state.execution_times)

    if state.status == "ERROR":
        return {}

    if state.supplier_outputs:
        times["run_supplier"] = round(time.time() - t0, 4)
        return {"execution_times": times}

    try:
        agent = SupplierAgent()
        suppliers = agent.run(state.region, state.user_config, product_id=state.product_id)
        times["run_supplier"] = round(time.time() - t0, 4)
        logger.info(f"[{state.request_id}] Node: run_supplier found {len(suppliers)} supplier option(s).")
        return {
            "supplier_outputs": suppliers,
            "execution_times": times
        }
    except Exception as e:
        logger.error(f"[{state.request_id}] Node: run_supplier failed: {e}")
        times["run_supplier"] = round(time.time() - t0, 4)
        return {
            "status": "ERROR",
            "errors": state.errors + [f"Supplier Agent failed: {str(e)}"],
            "execution_times": times
        }


def node_run_capacity_intelligence(state: AEMIIFState) -> Dict[str, Any]:
    """Node 5: Run deterministic pre-solver capacity checks and candidate sizing."""
    t0 = time.time()
    logger.info(f"[{state.request_id}] Node: run_capacity_intelligence started.")
    times = dict(state.execution_times)

    if state.status == "ERROR":
        return {}

    try:
        cap_res, reduced_sups = precheck_capacity(state.user_config, state.inventory_outputs, state.supplier_outputs)

        infeasible_statuses = [
            CapacityStatus.CAPACITY_INSUFFICIENT,
            CapacityStatus.NO_ELIGIBLE_SUPPLIERS,
            CapacityStatus.PROPORTIONAL_TARGET_UNSATISFIABLE,
            CapacityStatus.INVALID_INPUT
        ]

        if cap_res.status in infeasible_statuses:
            status = cap_res.status.value
            errs = list(state.errors)
            if cap_res.infeasibility_reason:
                errs.append(cap_res.infeasibility_reason)
            logger.warning(f"[{state.request_id}] Node: run_capacity_intelligence detected infeasibility: {status}")
        else:
            status = "CAPACITY_PASSED"
            errs = state.errors

        times["run_capacity_intelligence"] = round(time.time() - t0, 4)
        return {
            "capacity_precheck": cap_res,
            "reduced_suppliers": reduced_sups,
            "status": status,
            "errors": errs,
            "execution_times": times
        }
    except Exception as e:
        logger.error(f"[{state.request_id}] Node: run_capacity_intelligence failed: {e}")
        times["run_capacity_intelligence"] = round(time.time() - t0, 4)
        return {
            "status": "ERROR",
            "errors": state.errors + [f"Capacity Intelligence failed: {str(e)}"],
            "execution_times": times
        }


def node_build_optimization_input(state: AEMIIFState) -> Dict[str, Any]:
    """Node 6: Deterministically assemble OptimizationInput."""
    t0 = time.time()
    logger.info(f"[{state.request_id}] Node: build_optimization_input started.")
    times = dict(state.execution_times)

    if state.status == "ERROR":
        return {}

    try:
        opt_input = build_opt_input(
            state.user_config,
            state.forecast_outputs,
            state.inventory_outputs,
            state.reduced_suppliers,
            state.capacity_precheck
        )
        times["build_optimization_input"] = round(time.time() - t0, 4)
        return {
            "optimization_input": opt_input,
            "execution_times": times
        }
    except Exception as e:
        logger.error(f"[{state.request_id}] Node: build_optimization_input failed: {e}")
        times["build_optimization_input"] = round(time.time() - t0, 4)
        return {
            "status": "ERROR",
            "errors": state.errors + [f"Build Optimization Input failed: {str(e)}"],
            "execution_times": times
        }


def node_run_milp(state: AEMIIFState) -> Dict[str, Any]:
    """Node 7: Solve procurement problem using the deterministic MILP engine."""
    t0 = time.time()
    logger.info(f"[{state.request_id}] Node: run_milp started.")
    times = dict(state.execution_times)

    if state.status == "ERROR":
        return {}

    try:
        opt_result = solve_procurement_problem(state.optimization_input)
        status = opt_result.status

        errs = list(state.errors)
        if status != "OPTIMAL" and opt_result.infeasibility_reason:
            errs.append(opt_result.infeasibility_reason)

        times["run_milp"] = round(time.time() - t0, 4)
        logger.info(f"[{state.request_id}] Node: run_milp solved with status={status}.")
        return {
            "optimization_result": opt_result,
            "status": status,
            "errors": errs,
            "execution_times": times
        }
    except Exception as e:
        logger.error(f"[{state.request_id}] Node: run_milp failed: {e}")
        times["run_milp"] = round(time.time() - t0, 4)
        return {
            "status": "ERROR",
            "errors": state.errors + [f"MILP Engine failed: {str(e)}"],
            "execution_times": times
        }


def node_validate_optimization(state: AEMIIFState) -> Dict[str, Any]:
    """Node 8: Post-solver business rule validation."""
    t0 = time.time()
    logger.info(f"[{state.request_id}] Node: validate_optimization started.")
    times = dict(state.execution_times)

    if state.status != "OPTIMAL":
        times["validate_optimization"] = round(time.time() - t0, 4)
        return {
            "validation_result": {"status": "SKIPPED"},
            "execution_times": times
        }

    try:
        post_validate_optimization(
            state.optimization_result,
            state.user_config,
            state.inventory_outputs,
            state.reduced_suppliers,
            state.capacity_precheck
        )
        times["validate_optimization"] = round(time.time() - t0, 4)
        logger.info(f"[{state.request_id}] Node: validate_optimization PASSED.")
        return {
            "validation_result": {"status": "PASSED"},
            "status": "OPTIMAL",
            "execution_times": times
        }
    except ValueError as e:
        logger.warning(f"[{state.request_id}] Node: validate_optimization FAILED: {e}")
        times["validate_optimization"] = round(time.time() - t0, 4)
        return {
            "validation_result": {"status": "FAILED", "error": str(e)},
            "status": "VALIDATION_FAILED",
            "errors": state.errors + [str(e)],
            "execution_times": times
        }
    except Exception as e:
        logger.error(f"[{state.request_id}] Node: validate_optimization unexpected error: {e}")
        times["validate_optimization"] = round(time.time() - t0, 4)
        return {
            "status": "ERROR",
            "errors": state.errors + [f"Validation unexpected error: {str(e)}"],
            "execution_times": times
        }


def node_explain_result(state: AEMIIFState) -> Dict[str, Any]:
    """Node 9: Generate grounded natural-language explanation using ExplanationAgent."""
    t0 = time.time()
    logger.info(f"[{state.request_id}] Node: explain_result started.")
    times = dict(state.execution_times)

    try:
        agent = ExplanationAgent()
        explanation = agent.explain(state)
        times["explain_result"] = round(time.time() - t0, 4)
        logger.info(f"[{state.request_id}] Node: explain_result completed successfully.")
        return {
            "explanation": explanation,
            "execution_times": times
        }
    except Exception as e:
        logger.error(f"[{state.request_id}] Node: explain_result failed: {e}")
        times["explain_result"] = round(time.time() - t0, 4)
        return {
            "explanation": f"Explanation generation failed: {str(e)}",
            "execution_times": times
        }


def node_finalize_response(state: AEMIIFState) -> Dict[str, Any]:
    """Node 10: Build structured FinalAEMIIFResponse."""
    t0 = time.time()
    logger.info(f"[{state.request_id}] Node: finalize_response started.")
    times = dict(state.execution_times)

    opt = state.optimization_result
    cfg = state.user_config
    inv_list = state.inventory_outputs if state.inventory_outputs else []
    fc_list = state.forecast_outputs if state.forecast_outputs else []
    cap = state.capacity_precheck

    is_success = (state.status == "OPTIMAL")
    summary = "Procurement plan optimized successfully." if is_success else f"Workflow concluded with status: {state.status}."
    failure_type = None if is_success else state.status

    from .schemas import OptimizedProcurementPlan, ApprovalStatus
    
    cost_summary = None
    plan = None
    if opt and is_success:
        plan_id = f"PLAN-{time.strftime('%Y')}-{state.request_id.split('_')[-1].upper()}"
        plan = OptimizedProcurementPlan(
            plan_id=plan_id,
            region=state.region or "Unknown",
            optimization_status=state.status,
            approval_status=ApprovalStatus.PENDING_APPROVAL,
            result=opt
        )
        state.plan = plan # update state reference if needed
        state.requires_approval = True
        state.approval_status = "PENDING_APPROVAL"
        
        cost_summary = {
            "total_purchase_cost": opt.total_purchase_cost,
            "total_transport_cost": opt.total_transport_cost,
            "total_holding_cost": opt.total_holding_cost,
            "total_stockout_cost": opt.total_stockout_cost,
            "total_cost": opt.total_cost,
            "budget_used": opt.budget_used,
            "budget_remaining": opt.budget_remaining,
            "achieved_service_level": opt.achieved_service_level
        }

    procurement_plan = None
    if opt and opt.order_lines:
        procurement_plan = [line.model_dump() for line in opt.order_lines]

    diag = {}
    if opt and opt.infeasibility_reason:
        diag["opt_infeasibility_reason"] = opt.infeasibility_reason
    if cap and cap.infeasibility_reason:
        diag["capacity_infeasibility_reason"] = cap.infeasibility_reason
    if state.validation_result:
        diag["validation_result"] = state.validation_result

    times["finalize_response"] = round(time.time() - t0, 4)
    times["total_pipeline_time"] = round(sum(v for k, v in times.items() if k != "total_pipeline_time"), 4)

    final_resp = FinalAEMIIFResponse(
        request_id=state.request_id,
        status=state.status,
        summary=summary,
        failure_type=failure_type,
        user_requirements=cfg.parameters.model_dump() if cfg else None,
        objective_weights=cfg.weights.model_dump() if cfg else None,
        demand_summary=[fc.model_dump() for fc in fc_list] if fc_list else None,
        inventory_summary=[inv.model_dump() for inv in inv_list] if inv_list else None,
        capacity_summary=cap.model_dump() if cap else None,
        procurement_plan=procurement_plan,
        cost_summary=cost_summary,
        constraint_summary=opt.constraint_status if opt else None,
        explanation=state.explanation or "No explanation generated.",
        warnings=state.warnings + (opt.warnings if opt else []),
        errors=state.errors,
        relevant_diagnostics=diag if diag else None,
        execution_times=times,
        product_source=state.product_source,
        store_source=state.store_source,
        achieved_service_level=opt.achieved_service_level if opt else None,
        plan_id=plan.plan_id if plan else None
    )

    logger.info(f"[{state.request_id}] Pipeline completed in {times.get('total_pipeline_time', 0):.4f}s with status={state.status}.")
    return {
        "final_response": final_resp,
        "execution_times": times,
        "plan": plan,
        "requires_approval": state.requires_approval,
        "approval_status": state.approval_status
    }


# ============================================================
# CONDITIONAL ROUTING FUNCTIONS
# ============================================================

def route_after_parser(state: AEMIIFState) -> str:
    """Check if parsing succeeded or failed."""
    if state.status == "ERROR":
        return "explain_result"
    return "run_forecast"


def route_after_capacity(state: AEMIIFState) -> str:
    """
    Route based on capacity intelligence result.
    If capacity is insufficient or no eligible suppliers, SKIP MILP and route to explanation.
    """
    if state.status == "ERROR":
        return "explain_result"

    infeasible_statuses = [
        CapacityStatus.CAPACITY_INSUFFICIENT.value,
        CapacityStatus.NO_ELIGIBLE_SUPPLIERS.value,
        CapacityStatus.PROPORTIONAL_TARGET_UNSATISFIABLE.value,
        CapacityStatus.INVALID_INPUT.value
    ]
    if state.status in infeasible_statuses:
        return "explain_result"

    return "build_optimization_input"


def route_after_milp(state: AEMIIFState) -> str:
    """Route based on solver status."""
    if state.status in ["OPTIMAL", "FEASIBLE"]:
        return "validate_optimization"
    return "explain_result"


# ============================================================
# GRAPH BUILDER
# ============================================================

def build_aemiif_graph():
    """
    Constructs and compiles the AEMIIF LangGraph workflow.
    """
    builder = StateGraph(AEMIIFState)

    # 1. Add all 10 nodes
    builder.add_node("parse_requirements", node_parse_requirements)
    builder.add_node("run_forecast", node_run_forecast)
    builder.add_node("run_inventory", node_run_inventory)
    builder.add_node("run_supplier", node_run_supplier)
    builder.add_node("run_capacity_intelligence", node_run_capacity_intelligence)
    builder.add_node("build_optimization_input", node_build_optimization_input)
    builder.add_node("run_milp", node_run_milp)
    builder.add_node("validate_optimization", node_validate_optimization)
    builder.add_node("explain_result", node_explain_result)
    builder.add_node("finalize_response", node_finalize_response)

    # 2. Add edges
    builder.add_edge(START, "parse_requirements")

    builder.add_conditional_edges(
        "parse_requirements",
        route_after_parser,
        {
            "run_forecast": "run_forecast",
            "explain_result": "explain_result"
        }
    )

    builder.add_edge("run_forecast", "run_inventory")
    builder.add_edge("run_inventory", "run_supplier")
    builder.add_edge("run_supplier", "run_capacity_intelligence")

    builder.add_conditional_edges(
        "run_capacity_intelligence",
        route_after_capacity,
        {
            "build_optimization_input": "build_optimization_input",
            "explain_result": "explain_result"
        }
    )

    builder.add_edge("build_optimization_input", "run_milp")

    builder.add_conditional_edges(
        "run_milp",
        route_after_milp,
        {
            "validate_optimization": "validate_optimization",
            "explain_result": "explain_result"
        }
    )

    builder.add_edge("validate_optimization", "explain_result")
    builder.add_edge("explain_result", "finalize_response")
    builder.add_edge("finalize_response", END)

    return builder.compile()
