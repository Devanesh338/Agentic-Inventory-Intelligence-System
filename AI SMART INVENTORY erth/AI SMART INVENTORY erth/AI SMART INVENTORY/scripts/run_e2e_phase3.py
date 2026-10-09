import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from aemiif.parser_agent import RequirementParserAgent, LLMParsedResult, ParsedPreferences, PreferenceLevel
from aemiif.schemas import UserParameters, UserDecisionConfig
from aemiif.agents import ForecastAgent, InventoryAgent, SupplierAgent
from aemiif.optimization import build_optimization_input, solve_procurement_problem
from aemiif.persistence import save_optimization_result

def run_e2e_phase3():
    user_request = "Replenish the inventory under a budget of 100000. Suppliers should deliver within 5 days. Maintain at least 95 percent service level. Cost is very important and supplier reliability is also important."
    
    # 1. PARSE
    parser = RequirementParserAgent()
    mock_result = LLMParsedResult(
        parameters=UserParameters(budget=100000.0, max_lead_time_days=5, min_service_level=0.95),
        preferences=ParsedPreferences(purchase_cost=PreferenceLevel.VERY_HIGH, supplier_reliability=PreferenceLevel.HIGH)
    )
    config = parser.parse_requirements(user_request, mock_llm_result=mock_result)

    print("-" * 50)
    print("USER REQUIREMENTS")
    print("-" * 50)
    print(f"Budget: INR {config.parameters.budget:,.0f}" if config.parameters.budget else "Budget: None")
    print(f"Maximum Lead Time: {config.parameters.max_lead_time_days} days" if config.parameters.max_lead_time_days else "Maximum Lead Time: None")
    print(f"Minimum Service Level: {config.parameters.min_service_level*100}%" if config.parameters.min_service_level else "Minimum Service Level: None")
    print()
    
    print("-" * 50)
    print("USER OBJECTIVE WEIGHTS")
    print("-" * 50)
    print(f"Purchase Cost: {config.weights.purchase_cost:.4f}")
    print(f"Transport Cost: {config.weights.transport_cost:.4f}")
    print(f"Holding Cost: {config.weights.holding_cost:.4f}")
    print(f"Stockout Cost: {config.weights.stockout_cost:.4f}")
    print(f"Supplier Reliability: {config.weights.supplier_reliability:.4f}")
    print()

    # Fixed combination from Phase 2
    product_id = "P006"
    store_id = "ST002"
    
    # 2. AGENTS
    forecast_agent = ForecastAgent()
    inventory_agent = InventoryAgent()
    supplier_agent = SupplierAgent()
    
    forecast = forecast_agent.run(product_id, store_id)
    print("-" * 50)
    print("FORECAST")
    print("-" * 50)
    print(f"Product: {product_id}")
    print(f"Store: {store_id}")
    print(f"Forecast Demand: {forecast.forecast_demand}")
    print()
    
    inventory = inventory_agent.run(product_id, forecast, store_id)
    print("-" * 50)
    print("INVENTORY")
    print("-" * 50)
    print(f"Current Stock: {inventory.current_stock}")
    print(f"Incoming Quantity: {inventory.incoming_quantity}")
    print(f"Replenishment Requirement: {inventory.replenishment_requirement}")
    print()
    
    suppliers = supplier_agent.run(product_id, config, store_id=store_id)
    print("-" * 50)
    print("FEASIBLE SUPPLIERS")
    print("-" * 50)
    for s in suppliers:
        if s.feasibility_status == 'feasible':
            print(f"Supplier: {s.supplier_id} | Cost: {s.unit_cost} | Lead Time: {s.lead_time_days} | Rel: {s.reliability} | Dist: {s.distance_km} | MOQ: {s.moq} | Cap: {s.capacity}")
    print()
    
    # 3. MILP OPTIMIZATION
    opt_input = build_optimization_input(config, [forecast], [inventory], suppliers)
    opt_result = solve_procurement_problem(opt_input)
    
    # Save to Database
    save_optimization_result(opt_result)

    print("-" * 50)
    print("MILP RESULT")
    print("-" * 50)
    print(f"Status: {opt_result.status}")
    if opt_result.status == "OPTIMAL":
        print(f"Selected Supplier(s): {', '.join(opt_result.selected_suppliers)}")
        print(f"Order Quantity: {opt_result.total_order_quantity}")
        print(f"Purchase Cost: INR {opt_result.total_purchase_cost:,.2f}")
        print(f"Transport Cost: INR {opt_result.total_transport_cost:,.2f}")
        print(f"Holding Cost Proxy: INR {opt_result.total_holding_cost:,.2f}")
        print(f"Stockout Penalty Cost: INR {opt_result.total_stockout_cost:,.2f}")
        print(f"Total Cost: INR {opt_result.total_cost:,.2f}")
        print(f"Budget Used: INR {opt_result.budget_used:,.2f}")
        print(f"Budget Remaining: INR {opt_result.budget_remaining:,.2f}")
        print(f"Achieved Service Level: {opt_result.achieved_service_level*100:.1f}%")
    else:
        print(f"Reason: {opt_result.infeasibility_reason}")
    print()
    
    print("-" * 50)
    print("CONSTRAINT CHECK")
    print("-" * 50)
    if opt_result.status == "OPTIMAL":
        for constraint, status in opt_result.constraint_status.items():
            print(f"{constraint}: {status}")
    else:
        print("Model infeasible, checks not applicable.")
    
if __name__ == '__main__':
    run_e2e_phase3()
