"""
Generate the heat map GeoJSON for the web frontend.
====================================================
Combines grid geometry + SUHII values into a single GeoJSON
ready to render on MapLibre / Leaflet.
"""

import geopandas as gpd
import pandas as pd
from pathlib import Path

CITY = "nagpur"


def main():
    print("🗺️  Generating heat map GeoJSON...")

    grid_path = Path("data/boundaries/nagpur_grid.geojson")
    suhii_path = Path(f"data/tables/{CITY}_suhii_2024.parquet")

    if not grid_path.exists() or not suhii_path.exists():
        print("⚠️  Required data not found. Run pipeline steps first.")
        return

    grid = gpd.read_file(grid_path)
    suhii = pd.read_parquet(suhii_path)

    # Merge spatial polygons with calculated heat data
    heatmap = grid.merge(suhii, on="cell_id", how="inner")

    cols_to_keep = [
        "cell_id",
        "lon_center",
        "lat_center",
        "suhii_day",
        "suhii_night",
        "heat_level_day",
        "heat_level_night",
        "lst_day",
        "lst_night",
        "frac_built",
        "frac_tree",
        "frac_water",
        "geometry",
    ]
    available = [c for c in cols_to_keep if c in heatmap.columns]
    heatmap = heatmap[available]

    out_path = Path("data/demo/nagpur_heatmap.geojson")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    heatmap.to_file(out_path, driver="GeoJSON")

    print(f"   ✅ Heat map saved: {out_path}")
    print(f"   Cells with heat data: {len(heatmap)}")
    print(f"   File size: {out_path.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
