from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import health, regions, ingestion, optimization, analytics, approval
import os

app = FastAPI(
    title="AEMIIF Backend API",
    description="Backend API for the Agentic Explainable Multi-Agent Inventory Intelligence Framework",
    version="1.0.0"
)

# CORS Configuration
# We use environment variable to allow origins, fallback to localhost:5173 for local React dev
origins = os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(regions.router, prefix="/api/v1")
app.include_router(ingestion.router, prefix="/api/v1/ingestion")
app.include_router(optimization.router, prefix="/api/v1/optimization")
app.include_router(analytics.router, prefix="/api/v1/analytics")
app.include_router(approval.router, prefix="/api/v1/approval")

@app.on_event("startup")
async def startup_event():
    # Setup global database connection pool or other resources if necessary
    pass
