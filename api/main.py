"""
Chhaon (छांव) — FastAPI Backend Service.
Entry point for REST APIs, ML inference, scenario painter, and report generator.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.routers import cities, layers, cells, scenarios, reports

# Load environment variables from .env at repo root
load_dotenv()

app = FastAPI(
    title="Chhaon (छांव) API",
    description="Urban Heat Intelligence & Thermal Forecasting API for Indian Cities",
    version="1.0.0",
)

# CORS configuration for the frontend.
# Reads a comma-separated list from the CORS_ORIGINS env var (see .env).
# Falls back to local dev origins if the env var is not set, so nothing
# breaks for anyone running this without a configured .env yet.
_default_origins = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000"
origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", _default_origins).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static directories for report downloads
REPORTS_DIR = Path("data/reports")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/files/reports", StaticFiles(directory=str(REPORTS_DIR)), name="reports")

# Include all routers
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
    return {"status": "healthy"}
