# Frontend Architecture

## Stack
- **React 18**
- **Vite**
- **TypeScript**
- **Zustand** (State Management)
- **Recharts** (Data Visualization)
- **Axios** (API Client)

## Core Design Principles
1. **Single Source of Truth**: The backend FastAPI serves a `CanonicalOptimizationResponse` which acts as the single source of truth for the entire application. The React application does not reconstruct data or apply secondary mathematical logic. 
2. **Type Safety**: The API data contract is typed in TypeScript and strictly mirrored to the Pydantic schemas in Python.
3. **Graceful Null Handling**: Backend NaN or Infinite floats are serialized as `null`. The React UI components use formatting helpers (in `src/utils/formatters.ts`) to gracefully default `null` to `N/A` or `0%` without crashing or displaying `NaN`.
4. **Approval Driven**: The frontend explicitly gates the approval state via `useStore` ensuring cross-page persistence. The user can view the recommendation and explicitly decide via `DecisionApproval` or `ProcurementPlan`.

## Page Structure
- **Executive Overview**: High level KPIs from `summary`.
- **Procurement Plan**: Table from `procurement_plan`. Provides Approve/Reject controls.
- **Demand Inventory**: Overview from `demand_summary` & `inventory_summary`.
- **Supplier Analysis**: KPI from `supplier_analysis`.
- **Capacity Intelligence**: Aggregation from `capacity`.
- **Requirements Provenance**: View into `user_parameters` and `objective_weights`.
- **Constraint Validation**: Pass/Fail metrics from `constraints`.
- **Optimization Analytics**: Visual pie chart of `optimization_analytics`.
- **Hypothesis Testing**: Real-time statistical T-Test evaluation via `hypothesis_testing`.
- **Grounded Explanation**: Direct natural language output from LLM in `explanation`.

## Integration Flow
1. User uploads CSV in `Ingestion`.
2. User submits query in `OptimizationPanel`.
3. Action triggers `POST /optimization/run`.
4. Response writes full `CanonicalOptimizationResponse` into `useStore`.
5. All 10 pages immediately update using context data.
6. User can submit `APPROVE` / `REJECT` via `apiClient`.
