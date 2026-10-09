# React Migration Audit

## 1. Existing Backend Endpoints
- `GET /api/v1/health`
- `GET /api/v1/regions`
- `POST /api/v1/ingestion/upload`
- `POST /api/v1/optimization/run`
- `POST /api/v1/approval/{request_id}/approve`
- `GET /api/v1/analytics/overview/{request_id}`
- `GET /api/v1/analytics/procurement/{request_id}`
- `GET /api/v1/analytics/demand-inventory/{request_id}`
- `GET /api/v1/analytics/suppliers/{request_id}`
- `GET /api/v1/analytics/capacity/{request_id}`
- `GET /api/v1/analytics/requirements/{request_id}`
- `GET /api/v1/analytics/constraints/{request_id}`
- `GET /api/v1/analytics/optimization/{request_id}`
- `GET /api/v1/analytics/hypothesis/{request_id}`
- `GET /api/v1/analytics/explanation/{request_id}`

## 2. Existing Response Schemas
`APIAnalysisResponse` encapsulates the entire graph output, which is fully modeled in `backend/schemas/api_responses.py`. It contains arrays and dicts for the various tabs (e.g. `demand_summary`, `procurement_plan`, `cost_summary`, `constraint_summary`, `capacity_summary`).

## 3. Existing Analytics Data
The analytics data maps 1:1 with the tabs requested, which stream directly from the saved PostgreSQL `plan_snapshot` object populated by `aemiif_runner.py`.

## 4. Existing Approval Flow
The endpoint `POST /api/v1/approval/{request_id}/approve` currently supports passing a `{"decision": "APPROVE"}` or `{"decision": "REJECT"}` payload alongside a `reason`. It updates the Postgres table `procurement_decisions` effectively. Rejection functionally is completely built in.

## 5. Missing API Fields
Currently, no crucial API fields seem explicitly missing. The 10 pages all have dedicated backend JSON endpoints that return strictly structured dictionaries directly derived from the LangGraph node states.

## 6. Missing Approval Functionality
We already have `REJECT` alongside `APPROVE` in the backend endpoint. However, if the user explicitly prefers a separate `POST /api/v1/approval/{request_id}/reject` endpoint to mirror the `approve` one, we can easily add it, but using the JSON `decision: "REJECT"` is already functional. I will stick to what we built or wrap a separate router path for semantics.

## 7. Streamlit -> React Page Mapping
1. Executive Overview -> `ExecutiveOverview.tsx`
2. Procurement Plan -> `ProcurementPlan.tsx`
3. Demand & Inventory -> `DemandInventory.tsx`
4. Supplier Analysis -> `SupplierAnalysis.tsx`
5. Capacity Intelligence -> `CapacityIntelligence.tsx`
6. Requirements & Provenance -> `RequirementsProvenance.tsx`
7. Constraint Validation -> `ConstraintValidation.tsx`
8. Optimization Analytics -> `OptimizationAnalytics.tsx`
9. Hypothesis Testing -> `HypothesisTesting.tsx`
10. Grounded Explanation -> `GroundedExplanation.tsx`
11. Approval UI -> `ApprovalPanel.tsx` integrated in Procurement Plan.

## 8. Files that Must Remain Untouched
- `aemiif/graph.py`
- `aemiif/optimization.py`
- `aemiif/agents.py`
- `aemiif/capacity_intelligence.py`
- `aemiif/mcp_tools.py`
- `database.py`
- `app.py` (legacy UI)
- All `tests/` except new frontend ones.

## 9. Risks
- Chart components in React not mapping perfectly to the `plotly` charts in Streamlit without exact data structures. We'll use `recharts` for clean composability.
- Upload component dealing with multiple concurrent file buffers.

## 10. Recommended Implementation Order
1. Phase 1: Vite project creation (`npx create-vite frontend --template react-ts`)
2. Phase 2: Axios/Fetch API client hooks.
3. Phase 3: Zustand or React Context for `request_id` and global states.
4. Phase 4, 5, 6, 7: Core execution side panel (Ingestion, Region, Requirements, Run).
5. Phase 8, 9, 10: Procurement Plan + Approval/Rejection buttons.
6. Phase 11-19: Analytics view components.
7. Phase 20-24: Navigation layout and styling (Tailwind CSS is best, but since I'm told to use CSS/Tailwind rules, I'll use Tailwind if requested or vanilla CSS with a good design system).
8. Phase 28: E2E test.
