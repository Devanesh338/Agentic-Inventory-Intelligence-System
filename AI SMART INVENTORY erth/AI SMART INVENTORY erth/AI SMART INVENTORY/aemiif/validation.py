from typing import List
from aemiif.schemas import UserDecisionConfig, InventoryOutput, SupplierOption, OptimizationResult, CapacityPrecheckResult, CapacityStatus

def post_validate_optimization(
    opt_result: OptimizationResult,
    config: UserDecisionConfig,
    inventories: List[InventoryOutput],
    suppliers: List[SupplierOption],
    capacity_result: CapacityPrecheckResult
) -> None:
    """
    Validates the MILP optimization result against strict business rules.
    Raises ValueError if any fake/impossible solution is detected.
    """
    if opt_result.status != "OPTIMAL":
        return

    req_qty = sum(inv.replenishment_requirement for inv in inventories)
    if req_qty <= 0:
        if opt_result.total_order_quantity > 0:
            raise ValueError("Validation Failed: Order quantity > 0 when requirement is <= 0 across the region.")
        return

    budget = config.parameters.budget
    max_lead_time = config.parameters.max_lead_time_days
    max_distance = config.parameters.max_distance_km
    min_service_level = config.parameters.min_service_level

    # Check individual order lines
    supplier_map = {(s.supplier_id, s.product_id): s for s in suppliers}
    
    total_qty = 0
    
    # We must aggregate order quantities from a specific supplier-product across stores to check against Capacity/MOQ
    # OrderLine: supplier_id, product_id, store_id, order_quantity
    sup_prod_ordered = {}
    
    for ol in opt_result.order_lines:
        if ol.order_quantity < 0:
            raise ValueError(f"Validation Failed: Negative order quantity for {ol.supplier_id}.")
            
        sup_prod_key = (ol.supplier_id, ol.product_id)
        if ol.order_quantity > 0 and sup_prod_key not in supplier_map:
            raise ValueError(f"Validation Failed: Ordered from unselected/filtered supplier {ol.supplier_id} for product {ol.product_id}.")
            
        sup = supplier_map[sup_prod_key]
        
        if max_lead_time is not None and sup.lead_time_days > max_lead_time:
            raise ValueError(f"Validation Failed: Supplier {sup.supplier_id} lead time {sup.lead_time_days} > max {max_lead_time}.")
            
        if max_distance is not None and sup.distance_km is not None and sup.distance_km > max_distance:
            raise ValueError(f"Validation Failed: Supplier {sup.supplier_id} distance {sup.distance_km} > max {max_distance}.")
            
        if sup.feasibility_status != "feasible":
            raise ValueError(f"Validation Failed: Supplier {sup.supplier_id} for product {sup.product_id} is marked as infeasible.")
            
        total_qty += ol.order_quantity
        sup_prod_ordered[sup_prod_key] = sup_prod_ordered.get(sup_prod_key, 0) + ol.order_quantity
        
        # Check storage capacity per store
        store_inv = next((inv for inv in inventories if inv.store_id == ol.store_id and inv.product_id == ol.product_id), None)
        if store_inv and store_inv.storage_capacity is not None:
            projected = store_inv.current_stock + store_inv.incoming_quantity + ol.order_quantity
            if projected > store_inv.storage_capacity:
                raise ValueError(f"Validation Failed: Order quantity for store {ol.store_id} product {ol.product_id} exceeds storage capacity ({projected} > {store_inv.storage_capacity}).")
                
    for sp_key, qty in sup_prod_ordered.items():
        sup = supplier_map[sp_key]
        if qty > sup.capacity:
            raise ValueError(f"Validation Failed: Total order quantity {qty} exceeds capacity {sup.capacity} for {sup.supplier_id} and product {sup.product_id}.")
        if qty < sup.moq:
            raise ValueError(f"Validation Failed: Total order quantity {qty} is below MOQ {sup.moq} for {sup.supplier_id} and product {sup.product_id}.")


    if budget is not None and opt_result.total_cost > budget + 0.01:
        raise ValueError(f"Validation Failed: Total cost {opt_result.total_cost} exceeds budget {budget}.")

    if min_service_level is not None and opt_result.achieved_service_level is not None:
        if opt_result.achieved_service_level < min_service_level - 0.001:
            raise ValueError(f"Validation Failed: Achieved service level {opt_result.achieved_service_level} < {min_service_level}.")
            
    if total_qty != opt_result.total_order_quantity:
        raise ValueError("Validation Failed: Order line sum does not match total_order_quantity.")

    if capacity_result.status == CapacityStatus.CAPACITY_INSUFFICIENT:
        raise ValueError("Validation Failed: Solver returned OPTIMAL but capacity was insufficient.")
