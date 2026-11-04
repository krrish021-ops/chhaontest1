"""
Extract land cover fractions for Nagpur grid cells.
====================================================
Uses ESA WorldCover 2021 (10m) server-side batch reduction.
"""

import os
import ee
import pandas as pd
import geopandas as gpd
import shapely.geometry
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
GEE_PROJECT = os.getenv("GEE_PROJECT")
ee.Initialize(project=GEE_PROJECT)
print(f"✅ Earth Engine connected: project={GEE_PROJECT}")

CITY = "nagpur"
OUT_DIR = Path("data/tables")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def geodf_to_ee_fc(gdf):
    """Convert GeoDataFrame grid to Earth Engine FeatureCollection safely."""
    features = []
    for idx, row in gdf.iterrows():
        geo_dict = shapely.geometry.mapping(row.geometry)
        ee_geo = ee.Geometry(geo_dict)
        props = {
            "cell_id": str(row["cell_id"]),
            "lon_center": float(row["lon_center"]),
            "lat_center": float(row["lat_center"])
        }
        features.append(ee.Feature(ee_geo, props))
    return ee.FeatureCollection(features)


def main():
    print("=" * 50)
    print("  Chhaon — Land Cover Batch Extraction")
    print("=" * 50)

    grid = gpd.read_file("data/boundaries/nagpur_grid.geojson")
    fc = geodf_to_ee_fc(grid)

    print(f"\n🌳 Running batch land cover extraction for {len(grid)} cells...")
    wc = ee.Image("ESA/WorldCover/v200/2021")

    # Create multi-band boolean image for each land class
    img_built = wc.eq(50).rename("frac_built")
    img_tree = wc.eq(10).rename("frac_tree")
    img_water = wc.eq(80).rename("frac_water")
    img_crop = wc.eq(40).rename("frac_crop")
    img_grass = wc.eq(30).rename("frac_grass")
    img_bare = wc.eq(60).rename("frac_bare")

    combined = img_built.addBands([img_tree, img_water, img_crop, img_grass, img_bare])

    # Server-side spatial reduction
    reduced = combined.reduceRegions(
        collection=fc,
        reducer=ee.Reducer.mean(),
        scale=10
    ).getInfo()

    records = []
    for feat in reduced["features"]:
        props = feat["properties"]
        records.append({
            "cell_id": props.get("cell_id"),
            "lon": props.get("lon_center"),
            "lat": props.get("lat_center"),
            "frac_built": round(props.get("frac_built") or 0.0, 4),
            "frac_tree": round(props.get("frac_tree") or 0.0, 4),
            "frac_water": round(props.get("frac_water") or 0.0, 4),
            "frac_crop": round(props.get("frac_crop") or 0.0, 4),
            "frac_grass": round(props.get("frac_grass") or 0.0, 4),
            "frac_bare": round(props.get("frac_bare") or 0.0, 4),
        })

    lc_df = pd.DataFrame(records)
    lc_path = OUT_DIR / f"{CITY}_landcover_2021.parquet"
    lc_df.to_parquet(lc_path, index=False)

    print(f"   ✅ Land cover saved: {lc_path}")
    print(f"   Cells processed: {len(lc_df)}")

    if len(lc_df) > 0:
        print(f"\n{'=' * 50}")
        print(f"  Land Cover Summary — Nagpur 2021")
        print(f"{'=' * 50}")
        for col in ["frac_built", "frac_tree", "frac_crop", "frac_water", "frac_bare", "frac_grass"]:
            avg = lc_df[col].mean() * 100
            print(f"  {col.replace('frac_', '').title():>8}: {avg:5.1f}% avg")
        print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
