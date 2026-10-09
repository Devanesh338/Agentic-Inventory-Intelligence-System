import time
import pulp
from typing import List, Dict, Any, Tuple, Optional
from .schemas import (
    OptimizationInput, OptimizationResult, OrderLine,
    UserDecisionConfig, ForecastOutput, InventoryOutput, SupplierOption,
    CapacityPrecheckResult, CapacityMode
)

def build_optimization_input(
    user_config: UserDecisionConfig,
    forecast_outputs: List[ForecastOutput],
    inventory_outputs: List[InventoryOutput],
    supplier_outputs: List[SupplierOption],
    capacity_precheck: Optional[CapacityPrecheckResult] = None
) -> OptimizationInput:
    """Deterministically combine structures into OptimizationInput."""
    return OptimizationInput(
        user_config=user_config,
        forecast_outputs=forecast_outputs,
        inventory_outputs=inventory_outputs,
        supplier_outputs=supplier_outputs,
        capacity_precheck=capacity_precheck
    )

def solve_procurement_problem(opt_input: OptimizationInput) -> OptimizationResult:
    """Deterministic MILP Engine to solve the multi-product, multi-store regional procurement problem."""
    start_time = time.time()
    
    inventory = opt_input.inventory_outputs
    feasible_suppliers = [s for s in opt_input.supplier_outputs if s.feasibility_status == 'feasible']
    
    if not inventory:
        return OptimizationResult(status="ERROR", warnings=["No inventory data provided."])
        
    req_qty_map = {(inv.store_id, inv.product_id): inv.replenishment_requirement for inv in inventory}
    products = list(set(inv.product_id for inv in inventory))
    stores = list(set(inv.store_id for inv in inventory))
    
    sup_opt_map = {(s.supplier_id, s.product_id): s for s in feasible_suppliers}
    suppliers = list(set(s.supplier_id for s in feasible_suppliers))
    
    total_req = sum(req_qty_map.values())
    
    if total_req <= 0:
        return OptimizationResult(
            status="OPTIMAL", 
            total_order_quantity=0,
            warnings=["Replenishment requirement is zero across the region. No order needed."]
        )
        
    if not feasible_suppliers:
        return OptimizationResult(
            status="INFEASIBLE", 
            infeasibility_reason="No feasible suppliers available after hard constraints."
        )
        
    total_capacity = sum(s.capacity for s in feasible_suppliers)
    if total_capacity == 0:
        return OptimizationResult(
            status="INFEASIBLE", 
            infeasibility_reason="Total capacity of feasible suppliers is zero."
        )
        
    budget = opt_input.user_config.parameters.budget

    # MILP Setup
    model = pulp.LpProblem("Regional_Procurement_Optimization", pulp.LpMinimize)
    
    # Decision Variables
    x = {} # Order quantity from supplier to store for a product
    for sup in suppliers:
        for st in stores:
            for pr in products:
                if (sup, pr) in sup_opt_map:
                    x[(sup, st, pr)] = pulp.LpVariable(f"x_{sup}_{st}_{pr}", lowBound=0, cat=pulp.LpInteger)
                    
    y = {} # Binary selection of supplier for a product
    for sup in suppliers:
        for pr in products:
            if (sup, pr) in sup_opt_map:
                y[(sup, pr)] = pulp.LpVariable(f"y_{sup}_{pr}", cat=pulp.LpBinary)
                
    shortage = {}
    for st in stores:
        for pr in products:
            shortage[(st, pr)] = pulp.LpVariable(f"short_{st}_{pr}", lowBound=0, cat=pulp.LpInteger)
            
    # Costs
    total_purchase_cost = pulp.lpSum(
        x[(sup, st, pr)] * sup_opt_map[(sup, pr)].unit_cost 
        for sup, st, pr in x
    )
    
    total_transport_cost = pulp.lpSum(
        y[(sup, pr)] * (sup_opt_map[(sup, pr)].transport_cost or 0.0)
        for sup, pr in y
    )
    
    holding_cost_rate = 0.10
    total_holding_cost = pulp.lpSum(
        x[(sup, st, pr)] * sup_opt_map[(sup, pr)].unit_cost * holding_cost_rate
        for sup, st, pr in x
    )
    
    max_unit_cost = max(s.unit_cost for s in feasible_suppliers)
    
    total_shortage = pulp.lpSum(shortage[(st, pr)] for st, pr in shortage)
    total_reliability_penalty = pulp.lpSum(
        x[(sup, st, pr)] * (1.0 - sup_opt_map[(sup, pr)].reliability)
        for sup, st, pr in x
    )
    
    max_purchase = total_req * max_unit_cost if total_req > 0 else 1.0
    max_transport = sum((s.transport_cost or 0.0) for s in feasible_suppliers)
    if max_transport == 0: max_transport = 1.0
    max_shortage = total_req if total_req > 0 else 1.0
    max_reliability_penalty = total_req if total_req > 0 else 1.0
    
    norm_purchase = total_purchase_cost / max_purchase
    norm_transport = total_transport_cost / max_transport
    norm_holding = total_holding_cost / (max_purchase * holding_cost_rate)
    norm_stockout = (total_shortage / max_shortage) * 10.0
    norm_rel = total_reliability_penalty / max_reliability_penalty
    
    w = opt_input.user_config.weights
    model += (
        w.purchase_cost * norm_purchase +
        w.transport_cost * norm_transport +
        w.holding_cost * norm_holding +
        w.stockout_cost * norm_stockout +
        w.supplier_reliability * norm_rel
    )
    
    # Constraints
    # 1. Demand Coverage
    for st in stores:
        for pr in products:
            req = req_qty_map.get((st, pr), 0)
            if req > 0:
                model += (
                    pulp.lpSum(x[(sup, st, pr)] for sup in suppliers if (sup, pr) in sup_opt_map) + shortage[(st, pr)] >= req,
                    f"Demand_{st}_{pr}"
                )
                
    # 2. Budget
    if budget is not None:
        model += (total_purchase_cost + total_transport_cost <= budget, "Budget")
        
    # 3. Capacity & MOQ
    for sup in suppliers:
        for pr in products:
            if (sup, pr) in sup_opt_map:
                s = sup_opt_map[(sup, pr)]
                delivered = pulp.lpSum(x[(sup, st, pr)] for st in stores)
                model += (delivered <= s.capacity * y[(sup, pr)], f"Cap_{sup}_{pr}")
                model += (delivered >= s.moq * y[(sup, pr)], f"MOQ_{sup}_{pr}")
                
    # 3.5 Storage Capacity
    for inv in inventory:
        if inv.storage_capacity is not None and inv.storage_capacity > 0:
            delivered_to_store = pulp.lpSum(x[(sup, inv.store_id, inv.product_id)] for sup in suppliers if (sup, inv.product_id) in sup_opt_map)
            existing_stock = inv.current_stock + inv.incoming_quantity
            model += (delivered_to_store + existing_stock <= inv.storage_capacity, f"StorageCap_{inv.store_id}_{inv.product_id}")
                
    # 4. Service Level
    min_service_level = opt_input.user_config.parameters.min_service_level
    if min_service_level is not None:
        for inv in inventory:
            if inv.forecast_demand > 0:
                req_avail = min_service_level * inv.forecast_demand
                existing = inv.current_stock + inv.incoming_quantity
                req_order = req_avail - existing
                
                if req_order > 0:
                    model += (
                        pulp.lpSum(x[(sup, inv.store_id, inv.product_id)] for sup in suppliers if (sup, inv.product_id) in sup_opt_map) >= req_order,
                        f"SL_{inv.store_id}_{inv.product_id}"
                    )
                    
    # 5. Min Supplier Reliability
    min_rel = opt_input.user_config.parameters.min_supplier_reliability
    if min_rel is not None:
        for sup in suppliers:
            for pr in products:
                if (sup, pr) in sup_opt_map:
                    if sup_opt_map[(sup, pr)].reliability < min_rel:
                        model += (y[(sup, pr)] == 0, f"MinRel_{sup}_{pr}")
                        
    # Solve
    solver = pulp.PULP_CBC_CMD(msg=False)
    model.solve(solver)
    
    solve_time = time.time() - start_time
    status_str = pulp.LpStatus[model.status]
    
    if status_str != 'Optimal':
        return OptimizationResult(
            status="INFEASIBLE" if status_str == "Infeasible" else status_str,
            infeasibility_reason=f"Solver returned {status_str}",
            solve_time=solve_time
        )
        
    # Extract Results
    order_lines = []
    tot_purchase = 0.0
    tot_transport = 0.0
    tot_holding = 0.0
    tot_qty = 0
    selected_suppliers_set = set()
    
    for sup, pr in y:
        if int(y[(sup, pr)].varValue or 0) == 1:
            selected_suppliers_set.add(sup)
            tc = sup_opt_map[(sup, pr)].transport_cost or 0.0
            tot_transport += tc
            
            for st in stores:
                if (sup, st, pr) in x:
                    qty = int(x[(sup, st, pr)].varValue or 0)
                    if qty > 0:
                        s = sup_opt_map[(sup, pr)]
                        pc = qty * s.unit_cost
                        hc = pc * holding_cost_rate
                        
                        tot_purchase += pc
                        tot_holding += hc
                        tot_qty += qty
                        
                        order_lines.append(OrderLine(
                            region=s.region,
                            product_id=pr,
                            store_id=st,
                            supplier_id=sup,
                            order_quantity=qty,
                            unit_cost=s.unit_cost,
                            purchase_cost=pc,
                            transport_cost=tc if len([st_ for st_ in stores if int(x[(sup, st_, pr)].varValue or 0) > 0]) == 1 else tc / len([st_ for st_ in stores if int(x[(sup, st_, pr)].varValue or 0) > 0]), # Splitting transport cost visually among lines
                            lead_time_days=s.lead_time_days,
                            reliability=s.reliability,
                            distance_km=s.distance_km,
                            moq=s.moq,
                            capacity=s.capacity
                        ))
                        
    final_shortage = sum(int(shortage[(st, pr)].varValue or 0) for st, pr in shortage)
    tot_stockout = final_shortage * max_unit_cost
    tot_cost = tot_purchase + tot_transport
    
    # Calculate global service level across region
    total_forecast = sum(inv.forecast_demand for inv in inventory)
    available_qty = sum(inv.current_stock + inv.incoming_quantity for inv in inventory) + tot_qty
    achieved_service_level = min(available_qty / total_forecast, 1.0) if total_forecast > 0 else 1.0
    
    c_status = {
        "Budget": "PASS" if (budget is None or tot_cost <= budget) else "FAIL",
        "Demand": "PASS" if final_shortage == 0 else f"SHORTAGE ({final_shortage})",
        "Service Level": "PASS" if (min_service_level is None or achieved_service_level >= min_service_level - 0.001) else "FAIL"
    }

    return OptimizationResult(
        status="OPTIMAL",
        objective_value=pulp.value(model.objective),
        total_purchase_cost=tot_purchase,
        total_transport_cost=tot_transport,
        total_holding_cost=tot_holding,
        total_stockout_cost=tot_stockout,
        total_cost=tot_cost,
        achieved_service_level=achieved_service_level,
        selected_suppliers=list(selected_suppliers_set),
        order_lines=order_lines,
        total_order_quantity=tot_qty,
        budget_used=tot_cost,
        budget_remaining=(budget - tot_cost) if budget is not None else None,
        constraint_status=c_status,
        solver_name="PuLP CBC",
        solve_time=solve_time
    )

