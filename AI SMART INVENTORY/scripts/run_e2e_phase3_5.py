import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from aemiif.parser_agent import RequirementParserAgent, LLMParsedResult, ParsedPreferences, PreferenceLevel
from aemiif.schemas import UserParameters, UserDecisionConfig, CapacityMode, InventoryOutput, SupplierOption
from aemiif.capacity_intelligence import precheck_capacity
from aemiif.optimization import build_optimization_input, solve_procurement_problem
from aemiif.validation import post_validate_optimization

def run_e2e_phase3_5():
    config = UserDecisionConfig(
        parameters=UserParameters(budget=100000.0, max_lead_time_days=5, capacity_mode=CapacityMode.PROPORTIONAL),
        weights=RequirementParserAgent().parse_requirements("test", mock_llm_result=LLMParsedResult(parameters=UserParameters(), preferences=ParsedPreferences(purchase_cost=PreferenceLevel.VERY_HIGH))).weights,
        original_user_request="test"
    )
    
    inventory = InventoryOutput(
        product_id="P_TEST", store_id="ST_TEST", current_stock=0, incoming_quantity=0,
        forecast_demand=360, projected_stock=-360, safety_stock=0, inventory_position=0,
        replenishment_requirement=360, risk_level="HIGH"
    )
    
    suppliers = [
        SupplierOption(supplier_id="SUP_A", product_id="P_TEST", unit_cost=10, moq=20, lead_time_days=2, reliability=0.99, capacity=40, feasibility_status="feasible"),
        SupplierOption(supplier_id="SUP_B", product_id="P_TEST", unit_cost=10, moq=50, lead_time_days=2, reliability=0.99, capacity=100, feasibility_status="feasible"),
        SupplierOption(supplier_id="SUP_C", product_id="P_TEST", unit_cost=10, moq=50, lead_time_days=2, reliability=0.99, capacity=120, feasibility_status="feasible"),
        SupplierOption(supplier_id="SUP_D", product_id="P_TEST", unit_cost=10, moq=50, lead_time_days=2, reliability=0.99, capacity=200, feasibility_status="feasible")
    ]
    
    cap_res, reduced_sups = precheck_capacity(config, inventory, suppliers)
    
    print("-" * 50)
    print("CAPACITY PRECHECK")
    print("-" * 50)
    print(f"Mode:\n{cap_res.mode.value}")
    print(f"\nRequired Quantity:\n{cap_res.required_quantity}")
    print(f"\nInitial Eligible Suppliers:\n{cap_res.initial_candidate_count}")
    print(f"\nProportional Target:\n{cap_res.proportional_target}")
    print(f"\nFiltered Suppliers:\n{', '.join(cap_res.filtered_suppliers) if cap_res.filtered_suppliers else 'None'}")
    print(f"\nMILP Candidate Suppliers:\n{', '.join([s.supplier_id for s in reduced_sups])}")
    print("-" * 50)
    
    opt_input = build_optimization_input(config, [], [inventory], reduced_sups)
    opt_result = solve_procurement_problem(opt_input)
    
    post_validate_optimization(opt_result, config, inventory, reduced_sups, cap_res)
    
    print("MILP RESULT")
    print("-" * 50)
    print(f"Status: {opt_result.status}")
    if opt_result.status == "OPTIMAL":
        for line in opt_result.order_lines:
            print(f"Supplier: {line.supplier_id} | Qty: {line.order_quantity}")
    else:
        print(f"Reason: {opt_result.infeasibility_reason}")

if __name__ == '__main__':
    run_e2e_phase3_5()
