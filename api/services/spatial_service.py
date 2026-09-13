"""
Spatial Data Service.
======================
Reads city configurations and GeoJSON map files.
"""

import json
from pathlib import Path
from typing import Dict, Any
from config.loader import get_all_cities, get_city


def list_cities_service() -> list:
    """Return list of configured cities."""
    cities = get_all_cities()
    result = []
    for city_id, config in cities.items():
        result.append({"id": city_id, **config})
    return result


def get_city_aoi_service(city_id: str) -> Dict[str, Any]:
    """Get boundary GeoJSON for a city."""
    city = get_city(city_id)
    boundary_path = Path("data/boundaries/nagpur_boundary.geojson")

    if boundary_path.exists():
        with open(boundary_path, "r") as f:
            boundary_geojson = json.load(f)
    else:
        boundary_geojson = None

    return {
        "city_id": city_id,
        "config": city,
        "boundary": boundary_geojson
    }


def get_heatmap_geojson_service(city_id: str) -> Dict[str, Any]:
    """Get web-ready heat map GeoJSON for a city."""
    # Verify city exists
    get_city(city_id)

    heatmap_path = Path("data/demo/nagpur_heatmap.geojson")
    if not heatmap_path.exists():
        raise FileNotFoundError(f"Heat map for {city_id} not found. Run pipeline first.")

    with open(heatmap_path, "r") as f:
        return json.load(f)
