from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from backend.routers import health, regions, ingestion, optimization, analytics, approval
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure tables exist and pre-seeded baseline data is loaded
    try:
        from scripts.seed_database import ensure_database_ready
        ensure_database_ready()
    except Exception as e:
        import logging
        logging.error(f"Error during lifespan startup database check: {e}")
    yield

app = FastAPI(
    title="AEMIIF Backend API",
    description="Backend API for the Agentic Explainable Multi-Agent Inventory Intelligence Framework",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
configured_origins = os.environ.get(
    "CORS_ORIGINS", 
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174,http://localhost:3000,http://localhost:8501"
).split(",")
origins = [origin.strip() for origin in configured_origins if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root status
@app.get("/")
def root():
    return {"status": "online", "message": "AEMIIF Backend API is running", "docs_url": "/docs"}

# Include Routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(regions.router, prefix="/api/v1")
app.include_router(ingestion.router, prefix="/api/v1/ingestion")
app.include_router(optimization.router, prefix="/api/v1/optimization")
app.include_router(analytics.router, prefix="/api/v1/analytics")
app.include_router(approval.router, prefix="/api/v1/approval")
