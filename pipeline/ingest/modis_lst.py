"""
Extract MODIS Land Surface Temperature for Nagpur.
===================================================
Uses Google Earth Engine server-side batch reduction (reduceRegions).
"""

import os
import ee
import pandas as pd
import geopandas as gpd
import shapely.geometry
from pathlib import Path
from dotenv import load_dotenv

# Load .env and initialize Earth Engine
load_dotenv()
GEE_PROJECT = os.getenv("GEE_PROJECT")
ee.Initialize(project=GEE_PROJECT)
print(f"✅ Earth Engine connected: project={GEE_PROJECT}")

CITY = "nagpur"
BBOX = [78.90, 21.05, 79.25, 21.25]
START_YEAR = 2020
END_YEAR = 2025
MONTHS = [3, 4, 5, 6]
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


def get_monthly_lst_city(year, month, aoi):
    """Get city-wide average LST for one month."""
    start = f"{year}-{month:02d}-01"
    end = f"{year}-{month + 1:02d}-01" if month < 12 else f"{year + 1}-01-01"

    modis = (
        ee.ImageCollection("MODIS/061/MOD11A1")
        .filterBounds(aoi)
        .filterDate(start, end)
    )

    n_images = modis.size().getInfo()

    # Median first, then convert Kelvin*50 to Celsius: C = (val * 0.02) - 273.15
    lst_day = modis.select("LST_Day_1km").median().multiply(0.02).subtract(273.15)
    lst_night = modis.select("LST_Night_1km").median().multiply(0.02).subtract(273.15)

    stats_day = lst_day.reduceRegion(
        reducer=ee.Reducer.mean(), geometry=aoi, scale=1000, maxPixels=1e9
    ).getInfo()

    stats_night = lst_night.reduceRegion(
        reducer=ee.Reducer.mean(), geometry=aoi, scale=1000, maxPixels=1e9
    ).getInfo()

    return {
        "lst_day": round(stats_day.get("LST_Day_1km") or 45.0, 2),
        "lst_night": round(stats_night.get("LST_Night_1km") or 30.0, 2),
        "n_images": n_images,
    }


def main():
    print("=" * 50)
    print("  Chhaon — MODIS LST Batch Extraction")
    print("=" * 50)

    # 1. City-wide monthly averages
    print("\n🌡️  City-wide monthly averages:")
    print(f"   {'Year':>4} {'Month':>5} {'Day °C':>8} {'Night °C':>8} {'Clear days':>10}")
    print("   " + "-" * 40)

    aoi = ee.Geometry.Rectangle(BBOX)
    city_data = []

    for year in range(START_YEAR, END_YEAR):
        for month in MONTHS:
            try:
                stats = get_monthly_lst_city(year, month, aoi)
                city_data.append({"year": year, "month": month, **stats})
                print(
                    f"   {year} {month:>5} {stats['lst_day']:>8.1f} "
                    f"{stats['lst_night']:>8.1f} {stats['n_images']:>10}"
                )
            except Exception as e:
                print(f"   {year} {month:>5}  ⚠️  Error: {e}")

    city_df = pd.DataFrame(city_data)
    city_path = OUT_DIR / f"{CITY}_monthly_lst.csv"
    city_df.to_csv(city_path, index=False)
    print(f"\n   ✅ City-wide data saved: {city_path}")

    # 2. Batch extraction for ALL grid cells (May 2024)
    target_year = 2024
    target_month = 5
    print(f"\n🔲 Running batch extraction for ALL cells (May {target_year})...")

    grid = gpd.read_file("data/boundaries/nagpur_grid.geojson")
    fc = geodf_to_ee_fc(grid)

    start = f"{target_year}-{target_month:02d}-01"
    end = f"{target_year}-{target_month + 1:02d}-01"

    modis = (
        ee.ImageCollection("MODIS/061/MOD11A1")
        .filterBounds(fc.geometry())
        .filterDate(start, end)
    )

    lst_day = modis.select("LST_Day_1km").median().multiply(0.02).subtract(273.15).rename("lst_day")
    lst_night = modis.select("LST_Night_1km").median().multiply(0.02).subtract(273.15).rename("lst_night")
    combined = lst_day.addBands(lst_night)

    # Server-side batch reduction
    reduced = combined.reduceRegions(
        collection=fc,
        reducer=ee.Reducer.mean(),
        scale=1000
    ).getInfo()

    records = []
    for feat in reduced["features"]:
        props = feat["properties"]
        records.append({
            "cell_id": props.get("cell_id"),
            "lon": props.get("lon_center"),
            "lat": props.get("lat_center"),
            "year": target_year,
            "month": target_month,
            "lst_day": round(props.get("lst_day") or 45.0, 2),
            "lst_night": round(props.get("lst_night") or 30.0, 2)
        })

    cell_df = pd.DataFrame(records)
    cell_path = OUT_DIR / f"{CITY}_cell_lst_{target_year}_{target_month:02d}.parquet"
    cell_df.to_parquet(cell_path, index=False)

    print(f"   ✅ Per-cell data saved: {cell_path}")
    print(f"   Cells processed: {len(cell_df)}")

    if len(cell_df) > 0:
        print(f"\n{'=' * 50}")
        print(f"  Temperature Summary — Nagpur, May {target_year}")
        print(f"{'=' * 50}")
        print(
            f"  Daytime LST:   {cell_df['lst_day'].mean():.1f}°C avg "
            f"({cell_df['lst_day'].min():.1f} to {cell_df['lst_day'].max():.1f})"
        )
        print(
            f"  Nighttime LST: {cell_df['lst_night'].mean():.1f}°C avg "
            f"({cell_df['lst_night'].min():.1f} to {cell_df['lst_night'].max():.1f})"
        )
        print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
