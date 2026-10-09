import uuid
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from enum import Enum

# --- ENUMS ---

class CapacityMode(str, Enum):
    STRICT_HARD_CAP = "STRICT_HARD_CAP"
    PROPORTIONAL = "PROPORTIONAL"

class CapacityStatus(str, Enum):
    CAPACITY_SUFFICIENT = "CAPACITY_SUFFICIENT"
    CAPACITY_INSUFFICIENT = "CAPACITY_INSUFFICIENT"
    NO_ELIGIBLE_SUPPLIERS = "NO_ELIGIBLE_SUPPLIERS"
    PROPORTIONAL_CANDIDATES_AVAILABLE = "PROPORTIONAL_CANDIDATES_AVAILABLE"
    PROPORTIONAL_TARGET_UNSATISFIABLE = "PROPORTIONAL_TARGET_UNSATISFIABLE"
    INVALID_INPUT = "INVALID_INPUT"

class ApprovalStatus(str, Enum):
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REVISION_REQUIRED = "REVISION_REQUIRED"
    NOT_REQUIRED = "NOT_REQUIRED"

# --- PARSER SCHEMAS ---


class UserParameters(BaseModel):
    """Hard parameters and constraints extracted from user request."""
    budget: Optional[float] = Field(None, description="Maximum total budget available for procurement.")
    max_lead_time_days: Optional[int] = Field(None, description="Maximum acceptable lead time in days for delivery.")
    max_distance_km: Optional[float] = Field(None, ge=0, description="Maximum acceptable distance in km from supplier to store.")
    min_service_level: Optional[float] = Field(None, description="Minimum service level required (e.g., 0.95 for 95%).")
    min_supplier_reliability: Optional[float] = Field(None, description="Minimum acceptable supplier reliability.")
    target_date: Optional[str] = Field(None, description="Specific target date requested for delivery, if any.")
    requested_region: Optional[str] = Field(None, description="Specific region requested for optimization.")
    requested_product_ids: Optional[List[str]] = Field(None, description="Specific product IDs requested.")
    requested_store_ids: Optional[List[str]] = Field(None, description="Specific store IDs requested.")
    capacity_mode: Optional[CapacityMode] = Field(None, description="Capacity handling mode (STRICT_HARD_CAP or PROPORTIONAL).")

class ObjectiveWeights(BaseModel):
    """Normalized objective weights derived from user preferences (must sum to 1)."""
    purchase_cost: float = 0.2
    transport_cost: float = 0.2
    holding_cost: float = 0.2
    stockout_cost: float = 0.2
    supplier_reliability: float = 0.2

class UserDecisionConfig(BaseModel):
    """Combined configuration of hard parameters and objective weights."""
    parameters: UserParameters
    weights: ObjectiveWeights
    objective_mode: Optional[str] = None
    original_user_request: str

# --- AGENT OUTPUT SCHEMAS ---

class ForecastOutput(BaseModel):
    region: str
    product_id: str
    store_id: str
    historical_period_days: int
    forecast_horizon: int
    forecast_demand: int
    average_daily_demand: float
    model_name: str
    confidence: Optional[float] = None

class InventoryOutput(BaseModel):
    region: str
    product_id: str
    store_id: str
    current_stock: int
    incoming_quantity: int
    forecast_demand: int
    projected_stock: int
    safety_stock: int
    inventory_position: int
    replenishment_requirement: int
    risk_level: str
    storage_capacity: Optional[int] = None

class SupplierOption(BaseModel):
    supplier_id: str
    region: str
    product_id: str
    unit_cost: float
    moq: int
    lead_time_days: int
    reliability: float
    capacity: int
    distance_km: Optional[float] = None
    transport_cost: Optional[float] = None
    feasibility_status: str  # e.g., 'feasible', 'infeasible'
    infeasibility_reason: Optional[str] = None

# --- PHASE 3: OPTIMIZATION SCHEMAS ---

class OptimizationInput(BaseModel):
    """Input strictly structured for the MILP Engine."""
    user_config: UserDecisionConfig
    forecast_outputs: List[ForecastOutput]
    inventory_outputs: List[InventoryOutput]
    supplier_outputs: List[SupplierOption]
    capacity_precheck: Optional['CapacityPrecheckResult'] = None

class OrderLine(BaseModel):
    """An individual line item in the procurement plan."""
    region: str
    product_id: str
    store_id: str
    supplier_id: str
    order_quantity: int
    unit_cost: float
    purchase_cost: float
    transport_cost: float
    lead_time_days: int
    reliability: float
    distance_km: Optional[float] = None
    moq: int
    capacity: int

class OptimizationResult(BaseModel):
    """Output from the deterministic MILP Engine."""
    status: str
    objective_value: Optional[float] = None
    total_purchase_cost: Optional[float] = None
    total_transport_cost: Optional[float] = None
    total_holding_cost: Optional[float] = None
    total_stockout_cost: Optional[float] = None
    total_cost: Optional[float] = None
    achieved_service_level: Optional[float] = None
    selected_suppliers: List[str] = []
    order_lines: List[OrderLine] = []
    total_order_quantity: int = 0
    budget_used: Optional[float] = None
    budget_remaining: Optional[float] = None
    constraint_status: Dict[str, str] = {}
    solver_name: str = "PuLP"
    solve_time: Optional[float] = None
    warnings: List[str] = []
    infeasibility_reason: Optional[str] = None

import datetime

class OptimizedProcurementPlan(BaseModel):
    """A first-class decision object representing an optimization result pending human approval."""
    plan_id: str
    region: str
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    optimization_status: str
    approval_status: ApprovalStatus = ApprovalStatus.PENDING_APPROVAL
    rejection_reason: Optional[str] = None
    
    # Preserve the exact solver output
    result: OptimizationResult

class CapacityPrecheckResult(BaseModel):
    mode: Optional[CapacityMode] = None
    required_quantity: int = 0
    initial_candidate_count: int = 0
    eligible_candidate_count: int = 0
    proportional_target: Optional[float] = None
    proportional_targets: Dict[str, float] = Field(default_factory=dict)
    final_candidate_count: int = 0
    total_feasible_capacity: int = 0
    status: CapacityStatus
    filtered_suppliers: List[str] = []
    supplier_capacity_details: Dict[str, Any] = {}
    candidate_reduction_count: int = 0
    candidate_reduction_ratio: float = 0.0
    infeasibility_reason: Optional[str] = None

class FinalAEMIIFResponse(BaseModel):
    request_id: str
    status: str
    summary: str
    failure_type: Optional[str] = None
    user_requirements: Optional[Dict[str, Any]] = None
    objective_weights: Optional[Dict[str, Any]] = None
    demand_summary: Optional[List[Dict[str, Any]]] = None
    inventory_summary: Optional[List[Dict[str, Any]]] = None
    capacity_summary: Optional[Dict[str, Any]] = None
    procurement_plan: Optional[List[Dict[str, Any]]] = None
    cost_summary: Optional[Dict[str, Any]] = None
    constraint_summary: Optional[Dict[str, Any]] = None
    explanation: str
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    relevant_diagnostics: Optional[Dict[str, Any]] = None
    execution_times: Optional[Dict[str, float]] = None
    region_source: Optional[str] = None
    product_source: Optional[str] = None
    store_source: Optional[str] = None
    dataset_source: Optional[str] = None
    achieved_service_level: Optional[float] = None
    plan_id: Optional[str] = None

class AEMIIFState(BaseModel):
    """Strongly-typed state for the LangGraph workflow."""
    request_id: str = Field(default_factory=lambda: f"req_{uuid.uuid4().hex[:8]}")
    user_query: str
    region: Optional[str] = None
    product_id: Optional[str] = None
    store_id: Optional[str] = None
    region_source: str = "Prototype default"
    product_source: str = "Prototype default"
    store_source: str = "Prototype default"
    dataset_source: str = "Prototype default"
    mock_llm_result: Optional[Any] = None

    user_config: Optional[UserDecisionConfig] = None
    forecast_outputs: List[ForecastOutput] = Field(default_factory=list)
    inventory_outputs: List[InventoryOutput] = Field(default_factory=list)
    supplier_outputs: List[SupplierOption] = Field(default_factory=list)

    capacity_precheck: Optional[CapacityPrecheckResult] = None
    reduced_suppliers: List[SupplierOption] = Field(default_factory=list)

    optimization_input: Optional[OptimizationInput] = None
    optimization_result: Optional[OptimizationResult] = None

    validation_result: Optional[Dict[str, Any]] = None
    explanation: Optional[str] = None

    plan: Optional[OptimizedProcurementPlan] = None
    requires_approval: bool = False
    approval_status: str = "NOT_REQUIRED"  # NOT_REQUIRED, PENDING, APPROVED, REJECTED

    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    status: str = "INITIALIZED"
    execution_times: Dict[str, float] = Field(default_factory=dict)
    final_response: Optional[FinalAEMIIFResponse] = None


