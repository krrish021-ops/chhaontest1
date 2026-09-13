"""
Chhaon API — Main FastAPI Application.
======================================
Connects all routers: cities, layers, cells, and scenarios.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import cities, layers, cells, scenarios

app = FastAPI(
    title="Chhaon (छांव) API",
    description="Urban Heat Intelligence API for Growing Indian Cities",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(cities.router)
app.include_router(layers.router)
app.include_router(cells.router)
app.include_router(scenarios.router)


@app.get("/", tags=["Health"])
async def root():
    """Root status endpoint."""
    return {
        "product": "Chhaon (छांव)",
        "description": "Urban Heat Intelligence for Growing Indian Cities",
        "status": "operational",
        "docs": "/docs"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for Docker / monitoring."""
    return {"status": "healthy"}
