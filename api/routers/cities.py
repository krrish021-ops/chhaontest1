"""
Cities & Boundaries API Router.
===============================
Endpoints for listing cities and fetching boundary geometries.
"""

from fastapi import APIRouter, HTTPException
from typing import List
from api.schemas.heat import CityInfo
from api.services.spatial_service import list_cities_service, get_city_aoi_service

router = APIRouter(prefix="/api/v1", tags=["Cities & Boundaries"])


@router.get("/cities", response_model=List[CityInfo])
async def list_cities():
    """List all available pilot cities."""
    return list_cities_service()


@router.get("/aoi/{city_id}")
async def get_city_aoi(city_id: str):
    """Get boundary geometry and config for a city."""
    try:
        return get_city_aoi_service(city_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"City '{city_id}' not found.")

