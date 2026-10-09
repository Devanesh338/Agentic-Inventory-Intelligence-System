# AEMIIF Backend API Documentation

## Running the Backend
Ensure your environment is set up (with PostgreSQL and API keys).
Run the FastAPI application via:
```bash
python -m uvicorn backend.main:app --reload --port 8000
```
API Base URL: `http://localhost:8000/api/v1`

## CORS Configuration
CORS is configured to allow `http://localhost:5173` (Vite's default React port) for development. This can be customized via the `CORS_ORIGINS` environment variable.

## Endpoints

### 1. Health
`GET /health`
Returns the status of the API.
**Response:**
```json
{
  "status": "ok",
  "service": "AEMIIF Backend"
}
```

### 2. Regions
`GET /regions`
Fetches a list of available regions from the PostgreSQL inventory table.
**Response:** `["Chennai-Central", "Chennai-North"]`

### 3. Data Ingestion
`POST /ingestion/upload`
Accepts `sales_file`, `inventory_file`, and `suppliers_file` as multipart form data.
Validates the CSV structures, cleans duplicates, and pushes to the database if validation passes.
**Response:**
```json
{
  "status": "success",
  "tables": { "sales": {"rows": 100} },
  "validation": { "errors": [], "warnings": [] }
}
```

### 4. Optimization
`POST /optimization/run`
Triggers the LangGraph pipeline and MILP optimizer.
**Request:**
```json
{
  "user_query": "I need 50 units for ST001",
  "region": "Chennai-Central"
}
```
**Response:** `APIAnalysisResponse` containing the full result and `plan_id`.

### 5. Approval Workflow
`POST /approval/{request_id}/approve`
**Request:**
```json
{
  "decision": "APPROVE",
  "reason": "Cost is within budget"
}
```
Updates the approval state in the database. Returns `{ "plan_id": "...", "status": "APPROVED" }`.

### 6. Analytics Retrieval
To avoid rerunning optimization on every page load, use these endpoints:
- `GET /analytics/overview/{request_id}`
- `GET /analytics/procurement/{request_id}`
- `GET /analytics/demand-inventory/{request_id}`
- `GET /analytics/suppliers/{request_id}`
- `GET /analytics/capacity/{request_id}`
- `GET /analytics/requirements/{request_id}`
- `GET /analytics/constraints/{request_id}`
- `GET /analytics/optimization/{request_id}`
- `GET /analytics/hypothesis/{request_id}` (Computes paired t-test dynamically)
- `GET /analytics/explanation/{request_id}`
