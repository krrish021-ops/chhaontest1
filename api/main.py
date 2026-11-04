"""
Chhaon (छांव) — FastAPI Backend Service.
Entry point for REST APIs, ML inference, scenario painter, and report generator.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from api.routers import cities, layers, cells, scenarios, reports

load_dotenv()

app = FastAPI(
    title="Chhaon (छांव) API",
    description="Urban Heat Intelligence & Thermal Forecasting API for Indian Cities",
    version="1.0.0",
)

# CORS
_default_origins = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000"
origins = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", _default_origins).split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add version header to every response
@app.middleware("http")
async def add_version_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Chhaon-Version"] = "1.0.0"
    return response

# Static files for report downloads
REPORTS_DIR = Path("data/reports")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/files/reports", StaticFiles(directory=str(REPORTS_DIR)), name="reports")

# Routers
app.include_router(cities.router)
app.include_router(layers.router)
app.include_router(cells.router)
app.include_router(scenarios.router)
app.include_router(reports.router)


@app.get("/")
def root():
    return {
        "app": "Chhaon (छांव) — Urban Heat Intelligence",
        "version": "1.0.0",
        "status": "online",
        "docs": "/docs",
        "cors_origins": origins,
    }


@app.get("/health")
def health():
    """
    Health check — reports what is available on this deployment.
    A fresh clone will show demo_data=true but parquet_tables=false.
    That is honest and expected — the demo map still works.
    """
    demo_dir   = Path("data/demo")
    tables_dir = Path("data/tables")
    models_dir = Path("models/registry")

    demo_files    = list(demo_dir.glob("*.geojson"))   if demo_dir.exists()   else []
    parquet_files = list(tables_dir.glob("*.parquet")) if tables_dir.exists() else []
    model_files   = list(models_dir.glob("*.txt"))     if models_dir.exists() else []

    return {
        "status": "healthy",
        "version": "1.0.0",
        "capabilities": {
            "demo_map":       len(demo_files) > 0,
            "parquet_tables": len(parquet_files) > 0,
            "ml_models":      len(model_files) > 0,
            "shap":           len(model_files) > 0 and len(parquet_files) > 0,
            "scenarios":      len(parquet_files) > 0,
            "pdf_reports":    len(parquet_files) > 0,
        },
        "counts": {
            "demo_geojson_files": len(demo_files),
            "parquet_tables":     len(parquet_files),
            "model_boosters":     len(model_files),
        },
        "cors_origins": origins,
    }
