# AEMIIF FINAL ARCHITECTURE REPORT
**Agentic Explainable Multi-Agent Inventory Intelligence Framework**

## 1. Final Architecture Overview
The final AEMIIF system successfully transitioned from a single-product localized prototype to a dynamic, multi-dataset, region-aware framework orchestrated by LangGraph. It is designed to act as an intelligent intermediary between a human supply chain planner, structured dataset inputs, and deterministic linear programming constraints.

```
USER
  │
  ├── Upload sales_history.csv
  ├── Upload inventory.csv
  ├── Upload suppliers.csv
  │
  ▼
DATA VALIDATION
  │
  ▼
POSTGRESQL INGESTION
  │
  ▼
REGION SELECTION
  │
  ▼
USER NATURAL-LANGUAGE REQUIREMENT
  │
  ▼
PARSER AGENT  ─────────────► (UserParameters, ObjectiveWeights, UserDecisionConfig)
  │
  ▼
FORECAST AGENT ────────────► (Regional demand forecasts)
  │
  ▼
INVENTORY AGENT ───────────► (Current stock, Incoming stock, Safety stock, Replenishment)
  │
  ▼
SUPPLIER AGENT ────────────► (Candidate suppliers, Hard constraint filtering)
  │
  ▼
CAPACITY INTELLIGENCE ─────► (STRICT_HARD_CAP / PROPORTIONAL candidate reduction)
  │
  ▼
MILP OPTIMIZATION ENGINE ──► (PuLP-backed mathematical solver for cost minimization)
  │
  ▼
POST-VALIDATOR ────────────► (Strict mathematical constraint compliance check)
  │
  ▼
EXPLANATION AGENT ─────────► (Generates deterministic, grounded reasoning)
  │
  ▼
10-TAB DECISION DASHBOARD ─► (Provides Executive Summaries, Hypothesis Testing, Analytics)
  │
  ▼
HUMAN APPROVAL ────────────► "This is a recommendation. Procurement execution requires human approval."
```

## 2. Data Flow
1. **Ingestion**: Streamlit components parse pandas DataFrames into a validated SQLAlchemy schema via `seed_database.py`. 
2. **Configuration**: Streamlit triggers the `AEMIIFState` LangGraph graph with the target region and user query.
3. **Execution**: The Graph passes data cleanly down the chain. Output parameters of one node serve as bounded context for the next.
4. **Resolution**: Output is validated deterministically and sent back via a `FinalAEMIIFResponse` schema to be rendered.

## 3. Agent Responsibilities
- **Parser Agent**: Extracts structural constraints (budget, lead time) and objective preferences (transport vs purchase cost) from unstructured text. Normalizes weights to `1.0`.
- **Forecast Agent**: Calculates future demand horizons dynamically based on historical sales datasets per product/store combination. Gracefully defaults to zero if historical records are missing.
- **Inventory Agent**: Evaluates physical warehouse physics. Determines the exact replenishment requirement after factoring in `current_stock`, `incoming_quantity`, and `safety_stock`.
- **Supplier Agent**: Filters candidates via regional eligibility, distance maxes, and supplier minimum-order quantities (MOQ).
- **Explanation Agent**: Responsible *only* for deterministic translation of the MILP results and post-validation checks into human-readable text. It has no authority to alter parameters.

## 4. MILP Responsibilities
The Mixed-Integer Linear Programming (MILP) engine is tasked with multi-dimensional resource allocation spanning `[product, store, supplier]`.
- Enforces user budget constraints.
- Prevents breaking storage capacity limits.
- Meets minimum service level requirements via safety stock margins.
- Ensures order quantities respect supplier MOQ floors and aggregate capacity ceilings.
- Minimizes the weighted objective function corresponding to the user's explicit preferences.

## 5. Capacity Intelligence
Acts as an optimization pre-filter to prevent impossible mathematical solving.
- **STRICT_HARD_CAP**: Verifies `Sum(Supplier Capacities) >= Demand`. If false, fails immediately to save computation time.
- **PROPORTIONAL**: Disqualifies candidates unable to fulfill a fractional threshold (e.g., `Demand / # Candidates`) to encourage multi-sourcing supply chain resilience.

## 6. Dashboard Architecture
Constructed natively within Streamlit `app.py` utilizing Plotly Express.
- Tab 1: Executive Overview
- Tab 2: Procurement Plan (Data table and Pie Chart distributions)
- Tab 3: Demand & Inventory (Forecast models and stock risk indicators)
- Tab 4: Supplier Analysis (Unit Cost vs. Lead Time Scatter Plot)
- Tab 5: Capacity Intelligence (Solver candidate reduction tracking)
- Tab 6: Requirements & Provenance (Audit trails distinguishing LLM vs Dataset logic)
- Tab 7: Constraint Validation (Pass/Fail mathematical boolean matrices)
- Tab 8: Optimization Analytics (Concentration histograms)
- Tab 9: Hypothesis Testing (Paired T-Tests validating average baseline cost vs. optimized cost using Scipy)
- Tab 10: Grounded Explanation (LLM textual response bounded by strict disclaimers)

## 7. Dataset Schemas
1. **Sales History**: `sale_id`, `date`, `region`, `store_id`, `product_id`, `quantity_sold`, `unit_selling_price`.
2. **Inventory**: `inventory_id`, `region`, `store_id`, `product_id`, `current_stock`, `reserved_stock`, `incoming_quantity`, `safety_stock`, `storage_capacity`.
3. **Suppliers**: `supplier_id`, `supplier_name`, `region`, `product_id`, `unit_cost`, `moq`, `capacity`, `lead_time_days`, `reliability_score`, `transport_cost_per_km`.

## 8. Edge Cases Validated
The system was verified against a large array of failure vectors:
- Data Layer: Duplicate records, schema breaches, missing region headers.
- Supplier Scarcity: Strict Cap insufficiency, Proportional mode target unfeasibility.
- Inventory Integrity: Perfect identical `Current Stock == Demand` states, 0-demand states.
- Stats Handling: T-Test edge cases where sample size < 2, or where optimized cost variance relative to market baseline is exactly zero (`NaN` resolution).
- Execution Errors: LangGraph handles all internal `Exceptions` cleanly, defaulting the UI to an `ERROR` state with associated warnings rather than generating fake allocations.

## 9. Testing Results
- Over 80 distinct integration and unit tests passing.
- Total structural UI preservation confirmed.
- Deterministic capacity boundaries confirmed.

## 10. Safety Guarantees & Human-in-the-Loop Governance
The system operates securely as an analytic intermediary:
1. **No direct LLM Execution**: The MILP operates on strictly structured Pydantic parameters.
2. **Immutable Provenance**: Every constraint applied in the Dashboard can trace its origin back to either the User's explicit prompt, the uploaded CSVs, or a defined mathematical system default.
3. **Hard Validation Barriers**: The `PostValidator` ensures no hallucinated LLM variables manipulate the final optimization return structure.
4. **Required Disclosure**: Every explanation permanently requires the prefix: *"This is a recommendation. Procurement execution requires human approval."*
