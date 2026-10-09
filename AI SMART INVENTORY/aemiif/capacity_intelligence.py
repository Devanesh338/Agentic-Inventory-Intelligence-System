from typing import List, Tuple, Optional, Dict
from collections import defaultdict
from aemiif.schemas import (
    UserDecisionConfig, InventoryOutput, SupplierOption, 
    CapacityMode, CapacityStatus, CapacityPrecheckResult
)

def precheck_capacity(
    config: UserDecisionConfig,
    inventories: List[InventoryOutput],
    suppliers: List[SupplierOption]
) -> Tuple[CapacityPrecheckResult, List[SupplierOption]]:
    """
    Pre-solver capacity intelligence layer for multi-product region.
    Filters and sizing candidates before MILP optimization.
    """
    req_by_product = defaultdict(int)
    for inv in inventories:
        req_by_product[inv.product_id] += inv.replenishment_requirement
        
    total_req_qty = sum(req_by_product.values())
    initial_count = len(suppliers)
    
    eligible_suppliers = []
    filtered_out_initial = []
    
    # 1. Base eligibility check
    for s in suppliers:
        if s.feasibility_status != 'feasible':
            filtered_out_initial.append(s.supplier_id)
            continue
            
        if s.capacity < s.moq:
            filtered_out_initial.append(s.supplier_id)
            continue
            
        p = config.parameters
        if p.max_lead_time_days is not None and s.lead_time_days > p.max_lead_time_days:
            filtered_out_initial.append(s.supplier_id)
            continue
            
        if p.max_distance_km is not None and s.distance_km is not None and s.distance_km > p.max_distance_km:
            filtered_out_initial.append(s.supplier_id)
            continue
            
        if s.capacity <= 0:
            filtered_out_initial.append(s.supplier_id)
            continue
            
        eligible_suppliers.append(s)

    eligible_count = len(eligible_suppliers)
    total_capacity = sum(s.capacity for s in eligible_suppliers)
    mode = config.parameters.capacity_mode

    if total_req_qty <= 0:
        return CapacityPrecheckResult(
            mode=mode,
            required_quantity=total_req_qty,
            initial_candidate_count=initial_count,
            eligible_candidate_count=eligible_count,
            final_candidate_count=eligible_count,
            total_feasible_capacity=total_capacity,
            status=CapacityStatus.CAPACITY_SUFFICIENT,
            filtered_suppliers=list(set(filtered_out_initial))
        ), eligible_suppliers

    # Check per-product eligiblity
    sups_by_product = defaultdict(list)
    for s in eligible_suppliers:
        sups_by_product[s.product_id].append(s)
        
    for pid, req in req_by_product.items():
        if req > 0 and len(sups_by_product[pid]) == 0:
            return CapacityPrecheckResult(
                mode=mode,
                required_quantity=total_req_qty,
                initial_candidate_count=initial_count,
                eligible_candidate_count=eligible_count,
                final_candidate_count=0,
                total_feasible_capacity=total_capacity,
                status=CapacityStatus.NO_ELIGIBLE_SUPPLIERS,
                filtered_suppliers=list(set(filtered_out_initial)),
                infeasibility_reason=f"No eligible suppliers for product {pid}."
            ), []

    # 2. Strict Hard Cap Check (per product)
    if mode == CapacityMode.STRICT_HARD_CAP:
        for pid, req in req_by_product.items():
            cap_for_p = sum(s.capacity for s in sups_by_product[pid])
            if cap_for_p < req:
                return CapacityPrecheckResult(
                    mode=mode,
                    required_quantity=total_req_qty,
                    initial_candidate_count=initial_count,
                    eligible_candidate_count=eligible_count,
                    final_candidate_count=eligible_count,
                    total_feasible_capacity=total_capacity,
                    status=CapacityStatus.CAPACITY_INSUFFICIENT,
                    filtered_suppliers=list(set(filtered_out_initial)),
                    infeasibility_reason=f"Strict hard-cap capacity is insufficient for product {pid} ({cap_for_p} < {req})."
                ), []

    # 3. Proportional Mode Filtering
    final_suppliers = list(eligible_suppliers)
    proportional_targets: Dict[str, float] = {}
    filtered_out_proportional = []

    if mode == CapacityMode.PROPORTIONAL:
        final_suppliers = []
        for pid, req in req_by_product.items():
            if req == 0:
                continue
            
            sups = sups_by_product[pid]
            if len(sups) == 0:
                continue
                
            prop_target = req / len(sups)
            proportional_targets[pid] = prop_target
            
            valid_sups_for_p = []
            for s in sups:
                if s.capacity < prop_target:
                    filtered_out_proportional.append(s.supplier_id)
                else:
                    valid_sups_for_p.append(s)
                    final_suppliers.append(s)
            
            if not valid_sups_for_p:
                return CapacityPrecheckResult(
                    mode=mode,
                    required_quantity=total_req_qty,
                    initial_candidate_count=initial_count,
                    eligible_candidate_count=eligible_count,
                    proportional_target=prop_target,
                    final_candidate_count=0,
                    total_feasible_capacity=total_capacity,
                    status=CapacityStatus.PROPORTIONAL_TARGET_UNSATISFIABLE,
                    filtered_suppliers=list(set(filtered_out_initial + filtered_out_proportional)),
                    infeasibility_reason=f"No suppliers can satisfy the proportional target for {pid}."
                ), []

    final_count = len(final_suppliers)
    red_count = initial_count - final_count
    red_ratio = (red_count / initial_count) if initial_count > 0 else 0.0
    
    avg_target = sum(proportional_targets.values()) / len(proportional_targets) if proportional_targets else None

    return CapacityPrecheckResult(
        mode=mode,
        required_quantity=total_req_qty,
        initial_candidate_count=initial_count,
        eligible_candidate_count=eligible_count,
        proportional_target=avg_target,
        proportional_targets=proportional_targets,
        final_candidate_count=final_count,
        total_feasible_capacity=sum(s.capacity for s in final_suppliers),
        status=CapacityStatus.PROPORTIONAL_CANDIDATES_AVAILABLE if mode == CapacityMode.PROPORTIONAL else CapacityStatus.CAPACITY_SUFFICIENT,
        filtered_suppliers=list(set(filtered_out_initial + filtered_out_proportional)),
        candidate_reduction_count=red_count,
        candidate_reduction_ratio=red_ratio
    ), final_suppliers
