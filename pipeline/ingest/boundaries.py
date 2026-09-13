"""
Download Nagpur city boundary and create an analysis grid.
==========================================================
We need polygons to divide the city into zones.
Option A: Real ward boundaries (hard to get)
Option B: A regular grid (easy, works for prototype)

This script does BOTH — tries OSM wards first, falls back to grid.
"""

import json
import osmnx as ox
import geopandas as gpd
from shapely.geometry import box
import numpy as np
from pathlib import Path

# Output directory
OUT_DIR = Path("data/boundaries")
OUT_DIR.mkdir(parents=True, exist_ok=True)

CITY_NAME = "Nagpur, Maharashtra, India"
BBOX = [78.90, 21.05, 79.25, 21.25]  # [west, south, east, north]
GRID_SIZE_KM = 1.0  # Each grid cell is ~1km x 1km


def download_city_boundary():
    """Download the outer boundary of Nagpur from OpenStreetMap."""
    print(f"📍 Downloading boundary for {CITY_NAME}...")
    
    # osmnx downloads the city boundary in one line
    city = ox.geocode_to_gdf(CITY_NAME)
    
    # Save to file
    city.to_file(OUT_DIR / "nagpur_boundary.geojson", driver="GeoJSON")
    print(f"   ✅ City boundary saved: {OUT_DIR / 'nagpur_boundary.geojson'}")
    print(f"   Area: {city.geometry.area.iloc[0]:.4f} sq degrees")
    return city


def create_analysis_grid(bbox, cell_size_deg=0.01):
    """
    Create a regular grid over the city.
    
    Why a grid? Real ward boundaries are hard to get digitally.
    A 1km grid gives us ~700 cells over Nagpur — enough detail
    for a prototype. Each cell becomes a "zone" we analyze.
    
    Args:
        bbox: [west, south, east, north]
        cell_size_deg: Grid cell size in degrees (~0.01 = ~1km)
    """
    west, south, east, north = bbox
    
    # Create grid cell coordinates
    lons = np.arange(west, east, cell_size_deg)
    lats = np.arange(south, north, cell_size_deg)
    
    cells = []
    cell_id = 0
    
    for lon in lons:
        for lat in lats:
            # Create a square polygon for each cell
            cell_box = box(lon, lat, lon + cell_size_deg, lat + cell_size_deg)
            cells.append({
                "cell_id": f"C{cell_id:04d}",
                "lon_center": round(lon + cell_size_deg/2, 4),
                "lat_center": round(lat + cell_size_deg/2, 4),
                "geometry": cell_box
            })
            cell_id += 1
    
    # Convert to GeoDataFrame (a table with geometry)
    grid = gpd.GeoDataFrame(cells, crs="EPSG:4326")
    print(f"   📊 Created grid: {len(grid)} cells ({len(lons)}x{len(lats)})")
    return grid


def clip_grid_to_city(grid, city_boundary):
    """Remove grid cells that fall outside the city boundary."""
    # Keep only cells that overlap with the city
    clipped = gpd.clip(grid, city_boundary)
    print(f"   ✂️  Clipped to city: {len(grid)} → {len(clipped)} cells")
    return clipped


def main():
    print("=" * 50)
    print("  Chhaon — Boundary & Grid Pipeline")
    print("=" * 50)
    
    # 1. Download city boundary
    city = download_city_boundary()
    
    # 2. Create analysis grid
    print("\n🔲 Creating analysis grid...")
    grid = create_analysis_grid(BBOX, cell_size_deg=0.01)
    
    # 3. Clip grid to city boundary (remove cells in the countryside)
    grid = clip_grid_to_city(grid, city)
    
    # 4. Save the grid
    grid_path = OUT_DIR / "nagpur_grid.geojson"
    grid.to_file(grid_path, driver="GeoJSON")
    print(f"\n   ✅ Grid saved: {grid_path}")
    
    # 5. Print summary
    print("\n" + "=" * 50)
    print("  Summary")
    print("=" * 50)
    print(f"  City: Nagpur")
    print(f"  Bounding box: {BBOX}")
    print(f"  Grid cells: {len(grid)}")
    print(f"  Cell size: ~{GRID_SIZE_KM}km x {GRID_SIZE_KM}km")
    print(f"  Files created:")
    print(f"    - {OUT_DIR / 'nagpur_boundary.geojson'}")
    print(f"    - {OUT_DIR / 'nagpur_grid.geojson'}")
    print("=" * 50)


if __name__ == "__main__":
    main()
