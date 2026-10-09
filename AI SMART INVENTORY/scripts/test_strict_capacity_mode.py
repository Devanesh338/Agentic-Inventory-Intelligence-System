import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from aemiif.schemas import UserParameters, UserDecisionConfig, CapacityMode, ObjectiveWeights, InventoryOutput, SupplierOption, CapacityStatus
from aemiif.capacity_intelligence import precheck_capacity

def run_test_strict():
    config = UserDecisionConfig(
        parameters=UserParameters(capacity_mode=CapacityMode.STRICT_HARD_CAP),
        weights=ObjectiveWeights(),
        original_user_request="test"
    )
    
    inventory = InventoryOutput(
        product_id="P_TEST", store_id="ST_TEST", current_stock=0, incoming_quantity=0,
        forecast_demand=360, projected_stock=-360, safety_stock=0, inventory_position=0,
        replenishment_requirement=360, risk_level="HIGH"
    )
    
    suppliers = [
        SupplierOption(supplier_id=f"S{i}", product_id="P_TEST", unit_cost=10, moq=10, lead_time_days=2, reliability=0.99, capacity=40, feasibility_status="feasible")
        for i in range(1, 5)
    ]
    
    cap_res, reduced_sups = precheck_capacity(config, inventory, suppliers)
    
    print("-" * 50)
    print("STRICT CAPACITY TEST")
    print("-" * 50)
    print(f"Status: {cap_res.status.value}")
    if cap_res.status == CapacityStatus.CAPACITY_INSUFFICIENT:
        print(f"Reason: {cap_res.infeasibility_reason}")

if __name__ == '__main__':
    run_test_strict()
