import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from aemiif.parser_agent import RequirementParserAgent, LLMParsedResult, ParsedPreferences, PreferenceLevel
from aemiif.schemas import UserParameters, UserDecisionConfig
from aemiif.agents import ForecastAgent, InventoryAgent, SupplierAgent

def run_e2e():
    user_request = "Replenish the inventory under a budget of 100000. Suppliers should deliver within 5 days. Maintain at least 95 percent service level. Cost is very important and supplier reliability is also important."
    print("--- USER REQUEST ---")
    print(user_request)
    print()

    api_key = os.getenv("OPENAI_API_KEY")
    parser = RequirementParserAgent()
    
    if api_key:
        print("Parsing using real LLM...")
        config = parser.parse_requirements(user_request)
    else:
        print("Parsing using mock LLM (No OPENAI_API_KEY found)...")
        mock_result = LLMParsedResult(
            parameters=UserParameters(budget=100000.0, max_lead_time_days=5, min_service_level=0.95),
            preferences=ParsedPreferences(purchase_cost=PreferenceLevel.VERY_HIGH, supplier_reliability=PreferenceLevel.HIGH)
        )
        config = parser.parse_requirements(user_request, mock_llm_result=mock_result)

    print("\n--- USER CONFIGURATION ---")
    print(f"Budget: INR {config.parameters.budget:,.0f}" if config.parameters.budget else "Budget: None")
    print(f"Maximum lead time: {config.parameters.max_lead_time_days} days" if config.parameters.max_lead_time_days else "Maximum lead time: None")
    print(f"Minimum service level: {config.parameters.min_service_level*100}%" if config.parameters.min_service_level else "Minimum service level: None")

    print("\n--- OBJECTIVE WEIGHTS ---")
    print(f"Purchase cost: {config.weights.purchase_cost}")
    print(f"Transport cost: {config.weights.transport_cost}")
    print(f"Holding cost: {config.weights.holding_cost}")
    print(f"Stockout cost: {config.weights.stockout_cost}")
    print(f"Supplier reliability: {config.weights.supplier_reliability}")

    product_id = "P006"
    store_id = "ST002"
    
    print("\n--- RETRIEVING OPERATIONAL DATA (MCP) ---")
    forecast_agent = ForecastAgent()
    inventory_agent = InventoryAgent()
    supplier_agent = SupplierAgent()

    print(f"Targeting Product: {product_id} at Store: {store_id}")
    
    forecast = forecast_agent.run(product_id, store_id)
    print("\nFORECAST OUTPUT")
    print(f"Product {forecast.product_id}")
    print(f"Forecast demand: {forecast.forecast_demand}")
    
    inventory = inventory_agent.run(product_id, forecast, store_id)
    print("\nINVENTORY OUTPUT")
    print(f"Current stock: {inventory.current_stock}")
    print(f"Replenishment requirement: {inventory.replenishment_requirement}")
    print(f"Risk level: {inventory.risk_level}")
    
    suppliers = supplier_agent.run(product_id, config)
    print("\nSUPPLIER OPTIONS")
    for s in suppliers:
        if s.feasibility_status == 'feasible':
            print(f"Supplier {s.supplier_id}: feasible")
        else:
            print(f"Supplier {s.supplier_id}: infeasible \u2014 {s.infeasibility_reason}")

if __name__ == '__main__':
    run_e2e()
