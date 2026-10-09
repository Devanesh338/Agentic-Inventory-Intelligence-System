# API Data Contract

The backend now uses a canonical API layer to ensure all 10 React pages receive data derived from the EXACT same `OptimizationResult`. 

## `CanonicalOptimizationResponse`
All analytical endpoints extract fragments from this single root schema stored in PostgreSQL. 

```typescript
type CanonicalOptimizationResponse = {
  request_id: string;
  region: string;
  status: string;
  optimization_status: string;
  approval_status: string;
  original_user_query: string;
  
  user_parameters: {
    budget_limit: number | null;
    max_lead_time: number | null;
    target_service_level: number | null;
    region: string | null;
  };

  objective_weights: {
    procurement_cost: number;
    transport_cost: number;
    holding_cost: number;
    stockout_cost: number;
    supplier_reliability: number;
    lead_time: number;
  };
  
  summary: {
    total_procurement_cost: number;
    procurement_cost: number;
    transport_cost: number;
    holding_cost: number;
    stockout_cost: number;
    total_cost: number;
    budget_limit: number | null;
    budget_utilization: number | null;
    target_service_level: number | null;
    achieved_service_level: number | null;
    service_level_gap: number | null;
  };

  procurement_plan: Array<{
    product_id: string;
    store_id: string;
    supplier_id: string;
    quantity: number;
    unit_cost: number;
    total_cost: number;
    lead_time_days: number;
    reliability: number | null;
    transport_cost: number | null;
    holding_cost: number | null;
    stockout_cost: number | null;
  }>;

  supplier_analysis: Array<{
    supplier_id: string;
    product_id: string;
    quantity: number;
    unit_cost: number;
    lead_time_days: number;
    reliability: number | null;
    distance: number | null;
    capacity: number;
    utilization: number;
  }>;

  capacity: {
    feasibility: string;
    global_required_capacity: number;
    global_available_capacity: number;
    capacity_utilization: number;
    supplier_allocations: Array<{supplier_id: string, allocated: number}>;
  };

  constraints: {
    budget: { status: string, details: string, actual_value: number|null, required_value: number|null };
    lead_time: { status: string, details: string, actual_value: number|null, required_value: number|null };
    service_level: { status: string, details: string, actual_value: number|null, required_value: number|null };
    supplier_capacity: { status: string, details: string, actual_value: number|null, required_value: number|null };
    overall: { status: string, details: string, actual_value: number|null, required_value: number|null };
  };

  optimization_analytics: {
    cost_breakdown: Record<string, number>;
    percentages: Record<string, number>;
    objective_value: number | null;
    budget_utilization: number | null;
  };

  hypothesis_testing: any; // Dynamic output from Hypothesis Test service

  explanation: {
    summary: string;
    rationale: string;
    constraint_explanation: string;
    recommendation: string;
  };

  approval: {
    status: string;
    approved_by: string | null;
    approved_at: string | null;
    rejection_reason: string | null;
  };
};
```
