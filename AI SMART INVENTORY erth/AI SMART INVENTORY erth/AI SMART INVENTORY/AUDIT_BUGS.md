# AEMIIF AUDIT_BUGS.md

## 1. Procurement Plan Page
- **Frontend Field**: `total_cost` (blank)
- **API Endpoint**: `/api/v1/analytics/procurement/{request_id}`
- **Backend Response Field**: `procurement_plan[i].total_cost` (currently undefined or returned as `None` or not handled in `OptimizationResult`).
- **Database Field**: JSON inside `plan_snapshot -> procurement_plan`
- **Original Optimization Result Field**: `order_lines[i].total_cost` (which doesn't exist natively, only `purchase_cost` and `transport_cost` exist, so total cost needs to be explicitly calculated as `quantity * unit_cost` or `purchase_cost`).

- **Frontend Field**: `reliability` (NaN%)
- **API Endpoint**: `/api/v1/analytics/procurement/{request_id}`
- **Backend Response Field**: `procurement_plan[i].reliability`
- **Database Field**: JSON inside `plan_snapshot -> procurement_plan`
- **Original Optimization Result Field**: `order_lines[i].reliability`. The frontend gets something like `null` or `NaN` from backend serialization issues if the value was NumPy `NaN` or similar.

- **Frontend Field**: `approval_status`, `total_cost` (overall)
- **API Endpoint**: Currently these don't seem to be cleanly returned in the same API call, or the frontend computes them inconsistently.

## 2. Executive Overview Page
- **Frontend Field**: `budget_utilization`
- **API Endpoint**: `/api/v1/analytics/overview/{request_id}`
- **Backend Response Field**: Needs to be derived from `budget_used` / `budget_limit`. Currently, `FinalAEMIIFResponse` does not serialize `budget_limit` easily unless fetched from `user_requirements`.

- **Frontend Field**: `achieved_service_level`
- **API Endpoint**: `/api/v1/analytics/overview/{request_id}`
- **Backend Response Field**: `achieved_service_level`
- **Database Field**: `plan_snapshot -> achieved_service_level`
- **Original Optimization Result Field**: `achieved_service_level`. It might be blank if the solver fails or if formatting in the frontend is broken.

## 3. Capacity Intelligence Page
- **Frontend Field**: `system_feasibility` (shows INFEASIBLE despite OPTIMAL optimization)
- **API Endpoint**: `/api/v1/analytics/capacity/{request_id}`
- **Backend Response Field**: `capacity_summary -> status`
- **Original Optimization Result Field**: `capacity_precheck.status`. This is populated *before* optimization. If it's returning empty, it means `FinalAEMIIFResponse` does not store the `capacity_precheck` result properly.

## 4. Requirements & Provenance Page
- **Frontend Field**: `original_user_query` (shows "No query provided")
- **API Endpoint**: `/api/v1/analytics/requirements/{request_id}`
- **Backend Response Field**: `user_requirements.original_user_request` (Missing)
- **Original Optimization Result Field**: `user_config.original_user_request` is in `AEMIIFState` but not pushed to `FinalAEMIIFResponse`.

- **Frontend Field**: `objective_weights` (blank)
- **API Endpoint**: `/api/v1/analytics/requirements/{request_id}`
- **Backend Response Field**: `objective_weights` (Missing)
- **Original Optimization Result Field**: `user_config.weights` in `AEMIIFState`, but missing from `FinalAEMIIFResponse`.

## 5. Constraint Validation Page
- **Frontend Field**: `status` for constraints (N/A)
- **API Endpoint**: `/api/v1/analytics/constraints/{request_id}`
- **Backend Response Field**: `constraint_summary` (Missing or Empty)
- **Original Optimization Result Field**: `optimization_result.constraint_status`. Missing from `FinalAEMIIFResponse` mapping.

## 6. Supplier Analysis Page
- **Frontend Field**: `reliability` (NaN%)
- **API Endpoint**: `/api/v1/analytics/suppliers/{request_id}`
- **Backend Response Field**: Currently mapping to `procurement_plan`.
- **Original Optimization Result Field**: Full supplier analysis is in `AEMIIFState.supplier_outputs`, not preserved in `FinalAEMIIFResponse`.

## 7. Hypothesis Testing Page
- **Frontend Field**: Shows 404 Error
- **API Endpoint**: `/api/v1/analytics/hypothesis/{request_id}`
- **Root Cause**: While there is an endpoint in `backend/routers/analytics.py`, it might not be registered correctly in `main.py`, or it crashes due to missing data resulting in 500 (which frontend might misinterpret, or the CORS/path prefix is wrong in `client.ts`). The endpoint fetches `get_supplier_options(region)` from the database but if region is empty it might crash.

## 8. Human Approval
- **Frontend Field**: Approve / Reject buttons
- **API Endpoint**: Needs `/api/v1/approval/{request_id}/approve`
- **Root Cause**: Endpoint does not exist in FastAPI.
