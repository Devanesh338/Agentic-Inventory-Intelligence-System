from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class APIHealthResponse(BaseModel):
    status: str
    service: str

class APIUploadValidationResult(BaseModel):
    status: str
    tables: Dict[str, Dict[str, Any]]
    validation: Dict[str, Any]

class APIApprovalRequest(BaseModel):
    decision: str
    reason: Optional[str] = None

class APIApprovalResponse(BaseModel):
    plan_id: str
    status: str

class APIHypothesisResult(BaseModel):
    hypothesis_0: str
    hypothesis_1: str
    test_used: str
    sample_size: int
    t_statistic: Optional[float]
    p_value: Optional[float]
    significance_level: float
    decision: str
    interpretation: str
    is_valid: bool

class CanonicalUserParameters(BaseModel):
    budget_limit: Optional[float] = None
    max_lead_time: Optional[int] = None
    target_service_level: Optional[float] = None
    region: Optional[str] = None

class CanonicalObjectiveWeights(BaseModel):
    procurement_cost: float = 0.0
    transport_cost: float = 0.0
    holding_cost: float = 0.0
    stockout_cost: float = 0.0
    supplier_reliability: float = 0.0
    lead_time: float = 0.0

class CanonicalSummary(BaseModel):
    total_procurement_cost: float = 0.0
    procurement_cost: float = 0.0
    transport_cost: float = 0.0
    holding_cost: float = 0.0
    stockout_cost: float = 0.0
    total_cost: float = 0.0
    budget_limit: Optional[float] = None
    budget_utilization: Optional[float] = None
    target_service_level: Optional[float] = None
    achieved_service_level: Optional[float] = None
    service_level_gap: Optional[float] = None

class CanonicalProcurementPlanItem(BaseModel):
    product_id: str
    store_id: str
    supplier_id: str
    quantity: int
    unit_cost: float
    total_cost: float
    lead_time_days: int
    reliability: Optional[float] = None
    transport_cost: Optional[float] = None
    holding_cost: Optional[float] = None
    stockout_cost: Optional[float] = None

class CanonicalSupplierAnalysisItem(BaseModel):
    supplier_id: str
    product_id: str
    quantity: int
    unit_cost: float
    lead_time_days: int
    reliability: Optional[float] = None
    distance: Optional[float] = None
    capacity: int
    utilization: float

class CanonicalCapacity(BaseModel):
    feasibility: str
    global_required_capacity: int
    global_available_capacity: int
    capacity_utilization: float
    supplier_allocations: List[Dict[str, Any]] = []

class CanonicalConstraintItem(BaseModel):
    status: str
    details: str
    actual_value: Optional[float] = None
    required_value: Optional[float] = None

class CanonicalConstraints(BaseModel):
    budget: CanonicalConstraintItem
    lead_time: CanonicalConstraintItem
    service_level: CanonicalConstraintItem
    supplier_capacity: CanonicalConstraintItem
    overall: CanonicalConstraintItem

class CanonicalOptimizationAnalytics(BaseModel):
    cost_breakdown: Dict[str, float]
    percentages: Dict[str, float]
    objective_value: Optional[float] = None
    budget_utilization: Optional[float] = None

class CanonicalExplanation(BaseModel):
    summary: str
    rationale: str
    constraint_explanation: str
    recommendation: str

class CanonicalApproval(BaseModel):
    status: str
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    rejection_reason: Optional[str] = None

class CanonicalOptimizationResponse(BaseModel):
    request_id: str
    region: str
    status: str
    optimization_status: str
    approval_status: str
    original_user_query: str
    
    user_parameters: CanonicalUserParameters
    objective_weights: CanonicalObjectiveWeights
    
    summary: CanonicalSummary
    procurement_plan: List[CanonicalProcurementPlanItem]
    supplier_analysis: List[CanonicalSupplierAnalysisItem]
    capacity: CanonicalCapacity
    constraints: CanonicalConstraints
    optimization_analytics: CanonicalOptimizationAnalytics
    hypothesis_testing: Dict[str, Any] = {}
    explanation: CanonicalExplanation
    approval: CanonicalApproval

class APIOptimizationRunRequest(BaseModel):
    user_query: str
    region: Optional[str] = None
