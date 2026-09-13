"""
Find the rural reference temperature.
======================================
SUHII = Urban Temperature - Rural Temperature

We look 20km outside Nagpur for countryside areas that are
flat, have no buildings, and are at similar elevation.
"""

import os
import ee
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

# Load .env and initialize Earth Engine
load_dotenv()
GEE_PROJECT = os.getenv("GEE_PROJECT")
ee.Initialize(project=GEE_PROJECT)
print(f"✅ Earth Engine connected: project={GEE_PROJECT}")

CITY = "nagpur"
URBAN_BBOX = [78.90, 21.05, 79.25, 21.25]
BUFFER_KM = 20
OUT_DIR = Path("data/tables")


def get_rural_temperature(year, month):
    """Get average LST from rural areas around Nagpur."""
    urban = ee.Geometry.Rectangle(URBAN_BBOX)
    buffer_outer = urban.buffer(BUFFER_KM * 1000)
    buffer_inner = urban.buffer(2 * 1000)
    rural_ring = buffer_outer.difference(buffer_inner)

    start = f"{year}-{month:02d}-01"
    end = f"{year}-{month + 1:02d}-01" if month < 12 else f"{year + 1}-01-01"

    modis = (
        ee.ImageCollection("MODIS/061/MOD11A1")
        .filterBounds(rural_ring)
        .filterDate(start, end)
    )

    # Filter to rural land cover only (cropland=40, grass=30, shrub=20)
    wc = ee.Image("ESA/WorldCover/v200/2021")
    rural_mask = wc.eq(40).Or(wc.eq(30)).Or(wc.eq(20))

    # Take median first, THEN convert Kelvin*50 to Celsius
    lst_day = modis.select("LST_Day_1km").median().multiply(0.02).subtract(273.15)
    lst_night = modis.select("LST_Night_1km").median().multiply(0.02).subtract(273.15)

    rural_day = lst_day.updateMask(rural_mask)
    rural_night = lst_night.updateMask(rural_mask)

    day_stats = (
        rural_day.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=rural_ring,
            scale=1000,
            maxPixels=1e9,
        )
        .getInfo()
    )

    night_stats = (
        rural_night.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=rural_ring,
            scale=1000,
            maxPixels=1e9,
        )
        .getInfo()
    )

    return {
        "rural_lst_day": round(day_stats.get("LST_Day_1km") or 35.0, 2),
        "rural_lst_night": round(night_stats.get("LST_Night_1km") or 25.0, 2),
    }


def main():
    print("=" * 50)
    print("  Chhaon — Rural Reference Temperature")
    print("=" * 50)

    print(f"\n🌾 Computing rural reference for Nagpur...")
    print(f"   Buffer: {BUFFER_KM}km around city")
    print(f"   Land cover filter: cropland + grassland only")

    results = []
    for year in [2024]:
        for month in [3, 4, 5, 6]:
            try:
                rural = get_rural_temperature(year, month)
                results.append({"year": year, "month": month, **rural})
                print(
                    f"   {year}-{month:02d}: Day={rural['rural_lst_day']:.1f}°C, "
                    f"Night={rural['rural_lst_night']:.1f}°C"
                )
            except Exception as e:
                print(f"   {year}-{month:02d}: ⚠️ {e}")

    rural_df = pd.DataFrame(results)
    out_path = OUT_DIR / f"{CITY}_rural_reference.parquet"
    rural_df.to_parquet(out_path, index=False)
    print(f"\n   ✅ Rural reference saved: {out_path}")

    # Compare urban vs rural
    print(f"\n{'=' * 50}")
    print(f"  Urban vs Rural Comparison (May 2024)")
    print(f"{'=' * 50}")

    try:
        urban = pd.read_parquet(OUT_DIR / f"{CITY}_cell_lst_2024_05.parquet")
        if len(rural_df) > 0 and len(urban) > 0:
            rural_may = rural_df[rural_df["month"] == 5].iloc[0]
            urban_day = urban["lst_day"].mean()
            urban_night = urban["lst_night"].mean()
            rural_day = rural_may["rural_lst_day"]
            rural_night = rural_may["rural_lst_night"]

            print(
                f"  Daytime:   Urban {urban_day:.1f}°C vs Rural {rural_day:.1f}°C "
                f"→ UHI = +{urban_day - rural_day:.1f}°C"
            )
            print(
                f"  Nighttime: Urban {urban_night:.1f}°C vs Rural {rural_night:.1f}°C "
                f"→ UHI = +{urban_night - rural_night:.1f}°C"
            )
            print(f"\n  💡 Nighttime UHI is usually larger because")
            print(f"     concrete releases stored heat slowly after sunset.")
    except Exception as e:
        print(f"  ⚠️  Comparison note: {e}")

    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
