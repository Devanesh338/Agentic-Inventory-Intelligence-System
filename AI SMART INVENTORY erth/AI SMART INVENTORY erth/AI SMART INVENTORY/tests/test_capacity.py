import pytest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from aemiif.schemas import (
    UserDecisionConfig, UserParameters, ObjectiveWeights,
    InventoryOutput, SupplierOption, CapacityMode, CapacityStatus
)
from aemiif.capacity_intelligence import precheck_capacity
from aemiif.validation import post_validate_optimization
from aemiif.schemas import OptimizationResult, OrderLine

def build_mock_config(mode: CapacityMode, max_lead: int = None, max_dist: float = None):
    return UserDecisionConfig(
        parameters=UserParameters(capacity_mode=mode, max_lead_time_days=max_lead, max_distance_km=max_dist),
        weights=ObjectiveWeights(),
        original_user_request="test"
    )

def build_mock_inv(req_qty: int):
    return [InventoryOutput(
        region="TestRegion", product_id="P1", store_id="S1", current_stock=0, incoming_quantity=0,
        forecast_demand=0, projected_stock=0, safety_stock=0,
        inventory_position=0, replenishment_requirement=req_qty, risk_level="LOW"
    )]

def build_sup(id: str, cap: int, moq: int, lead: int = 2, dist: float = 10.0, rel: float = 0.99):
    return SupplierOption(
        supplier_id=id, region="TestRegion", product_id="P1", unit_cost=10.0, moq=moq,
        lead_time_days=lead, reliability=rel, capacity=cap, distance_km=dist,
        transport_cost=5.0, feasibility_status="feasible"
    )

# TEST 1: Strict mode + sufficient capacity
def test_strict_sufficient():
    config = build_mock_config(CapacityMode.STRICT_HARD_CAP)
    inv = build_mock_inv(360)
    sups = [build_sup("S1", 400, 10)]
    res, reduced = precheck_capacity(config, inv, sups)
    assert res.status == CapacityStatus.CAPACITY_SUFFICIENT
    assert len(reduced) == 1

# TEST 2: Strict mode + insufficient total capacity
def test_strict_insufficient():
    config = build_mock_config(CapacityMode.STRICT_HARD_CAP)
    inv = build_mock_inv(360)
    sups = [build_sup("S1", 40, 10), build_sup("S2", 40, 10)]
    res, reduced = precheck_capacity(config, inv, sups)
    assert res.status == CapacityStatus.CAPACITY_INSUFFICIENT
    assert len(reduced) == 0

# TEST 3 & 4: Proportional mode target & filtering
def test_proportional_target_and_filtering():
    config = build_mock_config(CapacityMode.PROPORTIONAL)
    inv = build_mock_inv(360)
    # Target should be 360 / 4 = 90
    sups = [
        build_sup("S1", 40, 10),  # Filtered out (40 < 90)
        build_sup("S2", 90, 10),  # Kept
        build_sup("S3", 120, 10), # Kept
        build_sup("S4", 200, 10)  # Kept
    ]
    res, reduced = precheck_capacity(config, inv, sups)
    assert res.status == CapacityStatus.PROPORTIONAL_CANDIDATES_AVAILABLE
    assert res.proportional_target == 90
    assert len(reduced) == 3
    assert "S1" in res.filtered_suppliers

# TEST 5: MOQ > target
def test_moq_greater_than_target():
    config = build_mock_config(CapacityMode.PROPORTIONAL)
    inv = build_mock_inv(360)
    # Target = 360 / 4 = 90
    # Supplier has cap=100 (>=90) so it's kept. MOQ=100 is fine for candidate layer.
    sups = [build_sup("S1", 100, 100), build_sup("S2", 100, 10), build_sup("S3", 100, 10), build_sup("S4", 100, 10)]
    res, reduced = precheck_capacity(config, inv, sups)
    assert res.status == CapacityStatus.PROPORTIONAL_CANDIDATES_AVAILABLE
    assert len(reduced) == 4
    assert "S1" not in res.filtered_suppliers

# TEST 6: Capacity < MOQ
def test_capacity_less_than_moq():
    config = build_mock_config(CapacityMode.STRICT_HARD_CAP)
    inv = build_mock_inv(360)
    sups = [build_sup("S1", 80, 100)] # Cap < MOQ
    res, reduced = precheck_capacity(config, inv, sups)
    assert res.status == CapacityStatus.NO_ELIGIBLE_SUPPLIERS
    assert len(reduced) == 0
    assert "S1" in res.filtered_suppliers

# TEST 7 & 8 & 9: Lead time, distance, and feasibility filtering before N
def test_hard_filtering_before_denominator():
    config = build_mock_config(CapacityMode.PROPORTIONAL, max_lead=5, max_dist=50.0)
    inv = build_mock_inv(360)
    sups = [
        build_sup("S1", 200, 10, lead=10), # Fails lead time
        build_sup("S2", 200, 10, dist=100.0), # Fails distance
        build_sup("S3", 200, 10), # Valid
        build_sup("S4", 200, 10)  # Valid
    ]
    res, reduced = precheck_capacity(config, inv, sups)
    assert res.eligible_candidate_count == 2
    assert res.proportional_target == 180 # 360 / 2 valid suppliers
    assert len(reduced) == 2

# TEST 10 & 11: Zero or negative req quantity
def test_zero_or_negative_requirement():
    config = build_mock_config(CapacityMode.STRICT_HARD_CAP)
    sups = [build_sup("S1", 100, 10)]
    
    res, red = precheck_capacity(config, build_mock_inv(0), sups)
    assert res.status == CapacityStatus.CAPACITY_SUFFICIENT # 0 requirement is trivially met
    
    res, red = precheck_capacity(config, build_mock_inv(-10), sups)
    assert res.status == CapacityStatus.CAPACITY_SUFFICIENT

# TEST 12: Missing or zero capacity
def test_zero_capacity():
    config = build_mock_config(CapacityMode.PROPORTIONAL)
    inv = build_mock_inv(100)
    sups = [build_sup("S1", 0, 10)]
    res, reduced = precheck_capacity(config, inv, sups)
    assert "S1" in res.filtered_suppliers
    assert res.status == CapacityStatus.NO_ELIGIBLE_SUPPLIERS

# TEST 15: Fractional target
def test_fractional_target():
    config = build_mock_config(CapacityMode.PROPORTIONAL)
    inv = build_mock_inv(365)
    sups = [build_sup(f"S{i}", 100, 10) for i in range(4)]
    res, reduced = precheck_capacity(config, inv, sups)
    assert res.proportional_target == 91.25
    assert len(reduced) == 4

# TEST 17: Proportional mode where all are below target
def test_proportional_all_below_target():
    config = build_mock_config(CapacityMode.PROPORTIONAL)
    inv = build_mock_inv(360)
    sups = [build_sup(f"S{i}", 40, 10) for i in range(4)]
    res, reduced = precheck_capacity(config, inv, sups)
    assert res.status == CapacityStatus.PROPORTIONAL_TARGET_UNSATISFIABLE
    assert len(reduced) == 0

# TEST 25: Post-solver validation failure (fake solution)
def test_validation_catches_fake():
    config = build_mock_config(CapacityMode.STRICT_HARD_CAP)
    inv = build_mock_inv(360)
    sups = [build_sup("S1", 40, 10)]
    cap_res, _ = precheck_capacity(config, inv, sups)
    
    opt_res = OptimizationResult(
        status="OPTIMAL",
        total_order_quantity=40,
        order_lines=[OrderLine(region="TestRegion", product_id="P1", store_id="S1", supplier_id="S1", order_quantity=40, unit_cost=10, purchase_cost=400, transport_cost=0, lead_time_days=2, reliability=1.0, moq=10, capacity=40)]
    )
    
    with pytest.raises(ValueError, match="Validation Failed: Solver returned OPTIMAL but capacity was insufficient."):
        post_validate_optimization(opt_res, config, inv, sups, cap_res)

def test_validation_catches_moq():
    config = build_mock_config(CapacityMode.STRICT_HARD_CAP)
    inv = build_mock_inv(360)
    sups = [build_sup("S1", 400, 100)]
    cap_res, _ = precheck_capacity(config, inv, sups)
    
    opt_res = OptimizationResult(
        status="OPTIMAL",
        total_order_quantity=50, # Below MOQ 100
        order_lines=[OrderLine(region="TestRegion", product_id="P1", store_id="S1", supplier_id="S1", order_quantity=50, unit_cost=10, purchase_cost=500, transport_cost=0, lead_time_days=2, reliability=1.0, moq=100, capacity=400)]
    )
    
    with pytest.raises(ValueError, match="is below MOQ"):
        post_validate_optimization(opt_res, config, inv, sups, cap_res)
