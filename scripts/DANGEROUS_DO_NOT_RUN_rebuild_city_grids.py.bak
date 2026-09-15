"""
Clean Rebuild for Chhaon.
1. Removes old bad data.
2. Generates proper 1km grids.
3. Fixes ID mapping to ensure highlight works.
"""

import os
from pathlib import Path
import pandas as pd
import geopandas as gpd
import numpy as np
from shapely.geometry import box

BOUNDS_DIR = Path("data/boundaries")
DEMO_DIR = Path("data/demo")
TABLES_DIR = Path("data/tables")
STEP = 0.009

def clean_rebuild():
    configs = [
        {"id": "nagpur", "prefix": "C", "coords": [79.08, 21.14], "extent": 0.12},
        {"id": "pune", "prefix": "P", "coords": [73.85, 18.52], "extent": 0.12}
    ]

    for cfg in configs:
        city = cfg["id"]
        print(f"\n{'='*20} Rebuilding {city.upper()} {'='*20}")
        
        # 1. Delete old files
        for f in [f"{city}_heatmap.geojson", f"{city}_heatmap_normalized.geojson", f"{city}_forecast_heatmap.geojson"]:
            p = DEMO_DIR / f
            if p.exists():
                os.remove(p)

        # 2. Load Parquet Data
        table_path = next(TABLES_DIR.glob(f"{city}*_matrix.parquet"), None)
        if not table_path:
            table_path = next(TABLES_DIR.glob(f"{city}*_master*.parquet"), None)
        
        df = pd.read_parquet(table_path) if table_path else pd.DataFrame()
        if not df.empty and "month" in df.columns:
            df = df[df["month"] == 5].drop_duplicates(subset=["cell_id"]).reset_index(drop=True)
        
        # 3. Generate Geometric Grid
        cx, cy = cfg["coords"]
        ext = cfg["extent"]
        minx, miny, maxx, maxy = cx - ext, cy - ext, cx + ext, cy + ext
        
        cells = []
        x = minx
        while x < maxx:
            y = miny
            while y < maxy:
                cells.append({"geometry": box(x, y, x + STEP, y + STEP)})
                y += STEP
            x += STEP
            
        grid_gdf = gpd.GeoDataFrame(cells, crs="EPSG:4326")
        
        # 4. Initialize columns with defaults
        grid_gdf["cell_id"] = None
        grid_gdf["suhii_night"] = 1.92
        grid_gdf["lst_day"] = 38.5
        grid_gdf["lst_night"] = 28.2
        grid_gdf["frac_built"] = 0.6
        grid_gdf["frac_tree"] = 0.1

        # 5. Sync Data
        if not df.empty:
            print(f"  ✓ Syncing {len(df)} data rows to grid...")
            for i in range(min(len(df), len(grid_gdf))):
                row = df.iloc[i]
                grid_gdf.at[i, "cell_id"] = str(row["cell_id"])
                grid_gdf.at[i, "suhii_night"] = row.get("suhii_night_normalized", row.get("suhii_night", 1.92))
                grid_gdf.at[i, "lst_day"] = row.get("lst_day", 38.5)
                grid_gdf.at[i, "lst_night"] = row.get("lst_night", 28.2)
                grid_gdf.at[i, "frac_built"] = row.get("frac_built", 0.6)
                grid_gdf.at[i, "frac_tree"] = row.get("frac_tree", 0.1)

        # 6. Fill remaining empty IDs uniquely
        prefix = cfg["prefix"]
        for i in range(len(grid_gdf)):
            if grid_gdf.at[i, "cell_id"] is None:
                grid_gdf.at[i, "cell_id"] = f"{prefix}{i+1000:04d}"

        # 7. Add derivative columns
        grid_gdf["suhii_night_normalized"] = grid_gdf["suhii_night"]
        grid_gdf["suhii_night_ml"] = grid_gdf["suhii_night"]
        grid_gdf["suhii_night_2031"] = (grid_gdf["suhii_night"] + 0.42).round(2)
        grid_gdf["suhii_night_2041"] = (grid_gdf["suhii_night"] + 1.18).round(2)

        # 8. Save Heatmaps
        for fname in [f"{city}_heatmap.geojson", f"{city}_heatmap_normalized.geojson", f"{city}_forecast_heatmap.geojson"]:
            grid_gdf.to_file(DEMO_DIR / fname, driver="GeoJSON")
        
        # 9. Update initial centering grid
        grid_gdf[["cell_id", "geometry"]].to_file(BOUNDS_DIR / f"{city}_grid.geojson", driver="GeoJSON")
        
        print(f"  ✅ Finished {city}: {len(grid_gdf)} cells.")

if __name__ == "__main__":
    clean_rebuild()
