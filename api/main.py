"""
Chhaon (छांव) — FastAPI Backend Service.
Entry point for REST APIs, ML inference, scenario painter, and report generator.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from api.routers import cities, layers, cells, scenarios, reports

app = FastAPI(
    title="Chhaon (छांव) API",
    description="Urban Heat Intelligence & Thermal Forecasting API for Indian Cities",
    version="1.0.0",
)

# CORS configuration for Next.js frontend
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
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
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
