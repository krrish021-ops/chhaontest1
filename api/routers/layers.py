"""
Heat Layers API Router.
=======================
Endpoints for serving spatial heat map GeoJSON layers.
"""

from fastapi import APIRouter, HTTPException
from api.services.spatial_service import get_heatmap_geojson_service

router = APIRouter(prefix="/api/v1", tags=["Heat Layers"])


@router.get("/layers/{city_id}")
async def get_heatmap_layer(city_id: str):
    """
    Get full heat map GeoJSON layer for a city.
    Returns complete feature collection ready for MapLibre rendering.
    """
    try:
        return get_heatmap_geojson_service(city_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"City '{city_id}' not found.")
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
