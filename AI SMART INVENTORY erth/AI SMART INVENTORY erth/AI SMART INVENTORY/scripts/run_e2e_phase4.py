import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from aemiif.graph import build_aemiif_graph
from aemiif.parser_agent import LLMParsedResult, ParsedPreferences, PreferenceLevel
from aemiif.schemas import UserParameters

def run_e2e_phase4():
    print("=" * 50)
    print("AEMIIF PHASE 4")
    print("=" * 50)

    user_query = (
        "Replenish the inventory under a budget of 100000. "
        "Suppliers should deliver within 5 days. "
        "Maintain at least 95 percent service level. "
        "Cost is very important and supplier reliability is also important."
    )

    print("\n[1] USER REQUEST")
    print("-" * 50)
    print(user_query)

    # Discover region dynamically
    region = "Chennai-West"
    try:
        from aemiif.database import get_db_cursor
        with get_db_cursor() as cur:
            cur.execute("SELECT region FROM inventory LIMIT 1")
            res = cur.fetchone()
            if res and 'region' in res:
                region = res['region']
    except Exception:
        pass

    # If no OpenAI API key is present in the environment, supply mock LLM parsed result
    # to test deterministic parsing seamlessly without external network failures.
    mock_result = None
    if not os.getenv("OPENAI_API_KEY"):
        mock_result = LLMParsedResult(
            parameters=UserParameters(
                budget=100000.0,
                max_lead_time_days=5,
                min_service_level=0.95,
                requested_product_ids=None,
                requested_store_ids=None
            ),
            preferences=ParsedPreferences(
                purchase_cost=PreferenceLevel.VERY_HIGH,
                supplier_reliability=PreferenceLevel.HIGH
            )
        )

    # Build and compile graph
    graph = build_aemiif_graph()

    # Execute workflow
    initial_state = {
        "user_query": user_query,
        "region": region,
        "product_id": None,
        "store_id": None,
        "mock_llm_result": mock_result
    }
    
    result = graph.invoke(initial_state)

    # [2] REQUIREMENT PARSER
    print("\n[2] REQUIREMENT PARSER")
    print("-" * 50)
    cfg = result.get("user_config")
    if cfg:
        p = cfg.parameters
        w = cfg.weights
        print(f"Budget: INR {p.budget:,.2f}" if p.budget else "Budget: None")
        print(f"Max Lead Time: {p.max_lead_time_days} days" if p.max_lead_time_days else "Max Lead Time: None")
        print(f"Min Service Level: {p.min_service_level*100:.1f}%" if p.min_service_level else "Min Service Level: None")
        print(f"Weights -> Purchase Cost: {w.purchase_cost:.4f}, Transport: {w.transport_cost:.4f}, Reliability: {w.supplier_reliability:.4f}")
    else:
        print("No UserDecisionConfig parsed.")

    # [3] FORECAST AGENT
    print("\n[3] FORECAST AGENT")
    print("-" * 50)
    forecasts = result.get("forecast_outputs", [])
    if forecasts:
        f = forecasts[0]
        print(f"Product: {f.product_id} | Store: {f.store_id} | Forecast Demand: {f.forecast_demand} units")
    else:
        print("No forecast output.")

    # [4] INVENTORY AGENT
    print("\n[4] INVENTORY AGENT")
    print("-" * 50)
    invs = result.get("inventory_outputs", [])
    if invs:
        inv = invs[0]
        print(f"Current Stock: {inv.current_stock} | Incoming: {inv.incoming_quantity} | Replenishment Req: {inv.replenishment_requirement} units | Risk: {inv.risk_level}")
    else:
        print("No inventory output.")

    # [5] SUPPLIER AGENT
    print("\n[5] SUPPLIER AGENT")
    print("-" * 50)
    sups = result.get("supplier_outputs", [])
    feasible_sups = [s for s in sups if s.feasibility_status == "feasible"]
    print(f"Total Suppliers Evaluated: {len(sups)} | Feasible Candidates: {len(feasible_sups)}")
    for s in feasible_sups:
        print(f"  * {s.supplier_id}: Unit Cost: INR {s.unit_cost:.2f}, Lead Time: {s.lead_time_days}d, Rel: {s.reliability}, MOQ: {s.moq}, Cap: {s.capacity}")

    # [6] CAPACITY INTELLIGENCE
    print("\n[6] CAPACITY INTELLIGENCE")
    print("-" * 50)
    cap = result.get("capacity_precheck")
    if cap:
        print(f"Mode: {cap.mode.value if cap.mode else 'None'} | Status: {cap.status.value}")
        print(f"Initial Candidates: {cap.initial_candidate_count} | Eligible: {cap.eligible_candidate_count} | Total Capacity: {cap.total_feasible_capacity}")
        if cap.proportional_target is not None:
            print(f"Proportional Target: {cap.proportional_target:.2f} units/supplier")
        print(f"Filtered Suppliers: {', '.join(cap.filtered_suppliers) if cap.filtered_suppliers else 'None'}")
        print(f"Candidates Passed to MILP: {cap.final_candidate_count}")
    else:
        print("No capacity precheck performed.")

    # [7] MILP OPTIMIZATION
    print("\n[7] MILP OPTIMIZATION")
    print("-" * 50)
    opt = result.get("optimization_result")
    if opt:
        print(f"Status: {opt.status}")
        if opt.status == "OPTIMAL":
            print(f"Selected Supplier(s): {', '.join(opt.selected_suppliers)}")
            print(f"Total Order Quantity: {opt.total_order_quantity} units")
            print(f"Total Cost: INR {opt.total_cost:,.2f} (Purchase: INR {opt.total_purchase_cost:,.2f}, Transport: INR {opt.total_transport_cost:,.2f})")
            print(f"Budget Remaining: INR {opt.budget_remaining:,.2f}")
            print(f"Achieved Service Level: {opt.achieved_service_level*100:.1f}%")
        else:
            print(f"Infeasibility Reason: {opt.infeasibility_reason}")
    else:
        print("MILP was not executed.")

    # [8] POST-SOLVER VALIDATION
    print("\n[8] POST-SOLVER VALIDATION")
    print("-" * 50)
    val = result.get("validation_result")
    if val:
        print(f"Validation Status: {val.get('status')}")
        if "error" in val:
            print(f"Validation Error: {val.get('error')}")
    else:
        print("Validation was skipped.")

    # [9] EXPLANATION AGENT
    print("\n[9] EXPLANATION AGENT")
    print("-" * 50)
    explanation = result.get("explanation")
    if explanation:
        print(explanation)
    else:
        print("No explanation generated.")

    # [10] FINAL RESPONSE
    print("\n[10] FINAL RESPONSE")
    print("-" * 50)
    final_resp = result.get("final_response")
    if final_resp:
        print(f"Request ID: {final_resp.request_id}")
        print(f"Overall Status: {final_resp.status}")
        print(f"Summary: {final_resp.summary}")
        if final_resp.execution_times:
            total_t = final_resp.execution_times.get("total_pipeline_time", 0)
            print(f"Total Pipeline Execution Time: {total_t:.4f}s")
    else:
        print("No FinalAEMIIFResponse structured output.")

if __name__ == '__main__':
    run_e2e_phase4()

