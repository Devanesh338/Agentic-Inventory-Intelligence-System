import os
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from .schemas import (
    AEMIIFState, CapacityMode, CapacityStatus, OptimizationResult
)

load_dotenv()
logger = logging.getLogger(__name__)

def generate_deterministic_explanation(state: AEMIIFState) -> str:
    """
    Generates a grounded, structured deterministic explanation directly
    from the graph state without invoking an LLM.
    """
    # 1. Handle Infeasibility / Failure States
    if state.status != "OPTIMAL":
        return _generate_infeasibility_explanation(state)

    # 2. Handle Zero Replenishment Requirement
    inv = state.inventory_outputs[0] if state.inventory_outputs else None
    opt = state.optimization_result
    cap = state.capacity_precheck
    cfg = state.user_config

    sections = []

    # 1. REQUEST SUMMARY
    sections.append("1. REQUEST SUMMARY")
    req_text = state.user_query if state.user_query else (cfg.original_user_request if cfg else "Unavailable")
    sections.append(f"User requested: \"{req_text}\".")
    sections.append("")

    # 2. USER CONSTRAINTS
    sections.append("2. USER CONSTRAINTS")
    if cfg and cfg.parameters:
        p = cfg.parameters
        budget_str = f"INR {p.budget:,.2f}" if p.budget is not None else "None"
        lead_time_str = f"{p.max_lead_time_days} days" if p.max_lead_time_days is not None else "None"
        dist_str = f"{p.max_distance_km} km" if p.max_distance_km is not None else "None"
        sl_str = f"{p.min_service_level * 100:.1f}%" if p.min_service_level is not None else "None"
        cap_mode_str = p.capacity_mode.value if p.capacity_mode else "None"
        sections.append(f"- Budget: {budget_str}")
        sections.append(f"- Maximum Lead Time: {lead_time_str}")
        sections.append(f"- Maximum Distance: {dist_str}")
        sections.append(f"- Minimum Service Level: {sl_str}")
        sections.append(f"- Capacity Mode: {cap_mode_str}")
    else:
        sections.append("User constraints: Unavailable.")
    sections.append("")

    # 3. USER PREFERENCES
    sections.append("3. USER PREFERENCES")
    if cfg and cfg.weights:
        w = cfg.weights
        sections.append(f"- Purchase Cost Weight: {w.purchase_cost * 100:.2f}%")
        sections.append(f"- Transport Cost Weight: {w.transport_cost * 100:.2f}%")
        sections.append(f"- Holding Cost Weight: {w.holding_cost * 100:.2f}%")
        sections.append(f"- Stockout Cost Weight: {w.stockout_cost * 100:.2f}%")
        sections.append(f"- Supplier Reliability Weight: {w.supplier_reliability * 100:.2f}%")
    else:
        sections.append("Objective weights: Unavailable.")
    sections.append("")

    # 4. DEMAND AND INVENTORY
    sections.append("4. DEMAND AND INVENTORY")
    if state.inventory_outputs:
        tot_forecast = sum(i.forecast_demand for i in state.inventory_outputs)
        tot_stock = sum(i.current_stock for i in state.inventory_outputs)
        tot_incoming = sum(i.incoming_quantity for i in state.inventory_outputs)
        tot_req = sum(i.replenishment_requirement for i in state.inventory_outputs)
        
        sections.append(f"- Region: {state.region or 'Prototype default'}")
        sections.append(f"- Total Products Analyzed: {len(state.inventory_outputs)}")
        sections.append(f"- Total Forecast Demand: {tot_forecast} units")
        sections.append(f"- Total Current Stock: {tot_stock} units")
        sections.append(f"- Total Incoming Quantity: {tot_incoming} units")
        sections.append(f"- Total Net Replenishment Requirement: {tot_req} units")
    else:
        sections.append("Demand and inventory details: Unavailable.")
    sections.append("")

    # 5. CAPACITY ANALYSIS
    sections.append("5. CAPACITY ANALYSIS")
    if cap:
        mode_val = cap.mode.value if cap.mode else "UNSPECIFIED"
        sections.append(f"- Capacity Mode: {mode_val}")
        sections.append(f"- Initial Eligible Suppliers: {cap.initial_candidate_count}")
        sections.append(f"- Total Feasible Capacity: {cap.total_feasible_capacity} units")
        if cap.proportional_target is not None:
            sections.append(f"- Proportional Target: {cap.proportional_target:.2f} units/supplier")
        filtered_str = ", ".join(cap.filtered_suppliers) if cap.filtered_suppliers else "None"
        sections.append(f"- Filtered Suppliers: {filtered_str}")
        sections.append(f"- Final Candidates Passed to MILP: {cap.final_candidate_count}")
    else:
        sections.append("Capacity analysis: Unavailable.")
    sections.append("")

    # 6. OPTIMIZATION RESULT
    sections.append("6. OPTIMIZATION RESULT")
    if opt:
        sups_str = ", ".join(opt.selected_suppliers) if opt.selected_suppliers else "None"
        sections.append(f"- Status: {opt.status}")
        sections.append(f"- Selected Supplier(s): {sups_str}")
        sections.append(f"- Total Order Quantity: {opt.total_order_quantity} units")
        if opt.order_lines:
            for line in opt.order_lines:
                sections.append(f"  * {line.supplier_id}: {line.order_quantity} units @ INR {line.unit_cost:.2f}/unit (Lead Time: {line.lead_time_days}d, Reliability: {line.reliability})")
        p_cost = f"INR {opt.total_purchase_cost:,.2f}" if opt.total_purchase_cost is not None else "INR 0.00"
        t_cost = f"INR {opt.total_transport_cost:,.2f}" if opt.total_transport_cost is not None else "INR 0.00"
        h_cost = f"INR {opt.total_holding_cost:,.2f}" if opt.total_holding_cost is not None else "INR 0.00"
        s_cost = f"INR {opt.total_stockout_cost:,.2f}" if opt.total_stockout_cost is not None else "INR 0.00"
        tot_cost = f"INR {opt.total_cost:,.2f}" if opt.total_cost is not None else "INR 0.00"
        rem_budget = f"INR {opt.budget_remaining:,.2f}" if opt.budget_remaining is not None else "N/A"
        sl_achieved = f"{opt.achieved_service_level * 100:.1f}%" if opt.achieved_service_level is not None else "N/A"
        
        sections.append(f"- Purchase Cost: {p_cost}")
        sections.append(f"- Transport Cost: {t_cost}")
        sections.append(f"- Holding Cost Proxy: {h_cost}")
        sections.append(f"- Stockout Penalty: {s_cost}")
        sections.append(f"- Total Cost: {tot_cost}")
        sections.append(f"- Budget Remaining: {rem_budget}")
        sections.append(f"- Achieved Service Level: {sl_achieved}")
    else:
        sections.append("Optimization result: Unavailable.")
    sections.append("")

    # 7. CONSTRAINT CHECK
    sections.append("7. CONSTRAINT CHECK")
    if opt and opt.constraint_status:
        for c_name, c_status in opt.constraint_status.items():
            sections.append(f"- {c_name}: {c_status}")
    elif opt and opt.status == "OPTIMAL":
        sections.append("- Budget Constraint: PASS")
        sections.append("- Demand Satisfaction: PASS")
        sections.append("- Service Level: PASS")
        sections.append("- Supplier Capacity: PASS")
        sections.append("- Supplier MOQ: PASS")
    else:
        sections.append("Constraint check: Unavailable.")
    sections.append("")

    # 8. WHY THIS PLAN
    sections.append("8. WHY THIS PLAN")
    if opt and opt.status == "OPTIMAL":
        if opt.total_order_quantity == 0:
            sections.append("No procurement order was needed because current inventory and incoming orders fully satisfy forecast demand and safety stock requirements.")
        else:
            sups_str = ", ".join(opt.selected_suppliers)
            sections.append(
                f"{sups_str} was selected by the MILP because the resulting plan satisfied all configured hard "
                f"constraints (budget, lead time, service level, supplier capacities, and MOQs) while producing "
                f"the lowest value of the predefined weighted objective among feasible solutions."
            )
    else:
        sections.append("Plan justification: Unavailable.")
    sections.append("")

    # 9. CAPACITY MODE EXPLANATION
    sections.append("9. CAPACITY MODE EXPLANATION")
    if cap and cap.mode == CapacityMode.PROPORTIONAL:
        sections.append(
            f"PROPORTIONAL capacity intelligence mode was activated. For a replenishment requirement of "
            f"{cap.required_quantity} units across {cap.eligible_candidate_count} eligible supplier(s), "
            f"the target allocation was {cap.proportional_target:.2f} units/supplier. "
            f"{len(cap.filtered_suppliers)} supplier(s) with capacity below this threshold were filtered before the MILP, "
            f"leaving {cap.final_candidate_count} pre-sized candidate(s) for final mathematical optimization."
        )
    elif cap and cap.mode == CapacityMode.STRICT_HARD_CAP:
        sections.append(
            f"STRICT_HARD_CAP mode was used. Supplier capacities were enforced as rigid upper bounds. "
            f"The combined capacity of {cap.total_feasible_capacity} units was verified sufficient "
            f"to meet the required {cap.required_quantity} units prior to solver invocation."
        )
    else:
        sections.append("Capacity mode explanation: Default capacity handling was applied.")
        
    sections.append("")
    sections.append("10. HUMAN IN THE LOOP")
    sections.append("This is a recommendation. Procurement execution requires human approval.")

    return "\n".join(sections)


def _generate_infeasibility_explanation(state: AEMIIFState) -> str:
    """Generates a structured diagnosis for failed or infeasible states."""
    cap = state.capacity_precheck
    opt = state.optimization_result
    status = state.status

    lines = [
        "==================================================",
        f"AEMIIF INFEASIBILITY REPORT — STATUS: {status}",
        "==================================================",
        f"Request ID: {state.request_id}",
        f"User Query: \"{state.user_query}\"",
        ""
    ]

    # Category 1: Capacity Insufficient
    if status == CapacityStatus.CAPACITY_INSUFFICIENT.value or (cap and cap.status == CapacityStatus.CAPACITY_INSUFFICIENT):
        req = cap.required_quantity if cap else "unknown"
        tot = cap.total_feasible_capacity if cap else "unknown"
        mode_str = cap.mode.value if (cap and cap.mode) else "STRICT_HARD_CAP"
        lines.append("DIAGNOSIS: CAPACITY_INSUFFICIENT")
        lines.append(
            f"The request cannot be satisfied under the selected {mode_str} mode because "
            f"the eligible suppliers have a combined capacity of only {tot} units, while "
            f"{req} units are required."
        )
        if cap and cap.infeasibility_reason:
            lines.append(f"Details: {cap.infeasibility_reason}")

    # Category 2: No Eligible Suppliers
    elif status == CapacityStatus.NO_ELIGIBLE_SUPPLIERS.value or (cap and cap.status == CapacityStatus.NO_ELIGIBLE_SUPPLIERS):
        lines.append("DIAGNOSIS: NO_ELIGIBLE_SUPPLIERS")
        lines.append(
            "No suppliers satisfied the user's hard constraints (such as maximum lead time, "
            "distance limits, or minimum capacity >= MOQ)."
        )
        if cap and cap.infeasibility_reason:
            lines.append(f"Details: {cap.infeasibility_reason}")

    # Category 3: Proportional Target Unsatisfiable
    elif status == CapacityStatus.PROPORTIONAL_TARGET_UNSATISFIABLE.value or (cap and cap.status == CapacityStatus.PROPORTIONAL_TARGET_UNSATISFIABLE):
        target = f"{cap.proportional_target:.2f}" if (cap and cap.proportional_target) else "calculated target"
        lines.append("DIAGNOSIS: PROPORTIONAL_TARGET_UNSATISFIABLE")
        lines.append(
            f"Under PROPORTIONAL capacity mode, no candidate suppliers have sufficient capacity to meet "
            f"the proportional target threshold ({target} units)."
        )
        if cap and cap.infeasibility_reason:
            lines.append(f"Details: {cap.infeasibility_reason}")

    # Category 4: MILP Infeasible
    elif status in ["INFEASIBLE", "MILP_INFEASIBLE"] or (opt and opt.status == "INFEASIBLE"):
        lines.append("DIAGNOSIS: MILP_INFEASIBLE")
        reason = opt.infeasibility_reason if opt else "Solver proved infeasible."
        lines.append(f"The MILP optimization engine determined that the problem is mathematically infeasible.")
        lines.append(f"Reason: {reason}")
        if state.user_config and state.user_config.parameters.budget:
            lines.append(f"Configured Budget: INR {state.user_config.parameters.budget:,.2f}")

    # Category 5: Validation Failed
    elif status == "VALIDATION_FAILED":
        lines.append("DIAGNOSIS: VALIDATION_FAILED")
        lines.append("The mathematical solver returned a solution, but it was rejected by post-solver validation rules.")
        if state.validation_result and "error" in state.validation_result:
            lines.append(f"Validation Error: {state.validation_result['error']}")
        for err in state.errors:
            lines.append(f"- {err}")

    # Category 6: System Error
    else:
        lines.append("DIAGNOSIS: SYSTEM_ERROR")
        lines.append("An error prevented successful completion of the workflow.")
        for err in state.errors:
            lines.append(f"- Error: {err}")

    lines.append("")
    lines.append("RECOMMENDATION:")
    lines.append("Review the constraints in your request (e.g. increase budget, extend lead time, or select an alternative capacity mode) and submit a new request.")

    return "\n".join(lines)


class ExplanationAgent:
    """
    Read-only Explanation Agent.
    Converts structured deterministic results into a grounded, human-readable narrative.
    Falls back gracefully to a deterministic template if no LLM key is available or LLM errors occur.
    """
    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.model_name = model_name
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.llm = ChatOpenAI(model=model_name, temperature=0)
        else:
            self.llm = None

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are the Explanation Agent for the AEMIIF procurement system.
Your job is ONLY to explain the DETERMINISTIC result produced by the MILP optimizer and capacity intelligence.
CRITICAL RULES:
1. You are strictly READ-ONLY. You cannot change numbers, suppliers, quantities, costs, or constraints.
2. Ground your explanation 100% in the provided facts. DO NOT HALLUCINATE ANY NUMBERS, REASONS, OR SAVINGS.
3. NEVER make alternative recommendations or say "I think Supplier X would be better".
4. If a piece of information is unavailable, say it is unavailable.
5. If the status is OPTIMAL, strictly follow this 9-section structure:
   1. REQUEST SUMMARY
   2. USER CONSTRAINTS
   3. USER PREFERENCES
   4. DEMAND AND INVENTORY
   5. CAPACITY ANALYSIS
   6. OPTIMIZATION RESULT
   7. CONSTRAINT CHECK
   8. WHY THIS PLAN
   9. CAPACITY MODE EXPLANATION
6. In "WHY THIS PLAN", explain that the selected supplier(s) satisfied all hard constraints while minimizing the predefined weighted objective.
7. If the status is NOT OPTIMAL (e.g. CAPACITY_INSUFFICIENT, MILP_INFEASIBLE, VALIDATION_FAILED), clearly explain the diagnosis and exact numbers that caused the infeasibility.
8. AT THE VERY END OF YOUR EXPLANATION, YOU MUST APPEND THIS EXACT TEXT: "This is a recommendation. Procurement execution requires human approval."""
            ),
            ("user", "{structured_state}")
        ])

    def explain(self, state: AEMIIFState) -> str:
        """Explain the state using LLM or deterministic fallback."""
        if not self.llm:
            return generate_deterministic_explanation(state)

        try:
            # Prepare structured context for LLM
            state_dict = {
                "request_id": state.request_id,
                "user_query": state.user_query,
                "status": state.status,
                "user_config": state.user_config.model_dump() if state.user_config else None,
                "forecasts": [f.model_dump() for f in state.forecast_outputs] if state.forecast_outputs else [],
                "inventories": [i.model_dump() for i in state.inventory_outputs] if state.inventory_outputs else [],
                "capacity_precheck": state.capacity_precheck.model_dump() if state.capacity_precheck else None,
                "optimization_result": state.optimization_result.model_dump() if state.optimization_result else None,
                "validation_result": state.validation_result,
                "errors": state.errors,
                "warnings": state.warnings
            }
            chain = self.prompt | self.llm
            response = chain.invoke({"structured_state": str(state_dict)})
            return response.content
        except Exception as e:
            logger.warning(f"ExplanationAgent LLM call failed ({e}), falling back to deterministic explanation.")
            return generate_deterministic_explanation(state)

