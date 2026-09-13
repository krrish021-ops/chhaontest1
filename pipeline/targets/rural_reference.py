"""
Multi-year rural reference LST computation.
For each year-month, computes the mean LST of qualifying rural pixels
in a 20km buffer around Nagpur (excluding 2km peri-urban ring).

FIX v2: Relaxed QA mask to match modis_lst.py (mandatory <= 1).

Output: data/tables/nagpur_rural_reference_multiyear.parquet
"""

import ee
import pandas as pd
import numpy as np
from pathlib import Path

ee.Initialize(project="chhaon-508513")

DATA_DIR = Path("data/tables")
BOUNDARY_PATH = "data/boundaries/nagpur_boundary.geojson"

YEARS = [2020, 2021, 2022, 2023, 2024]
MONTHS = [3, 4, 5, 6]
MONTH_NAMES = {3: "Mar", 4: "Apr", 5: "May", 6: "Jun"}
MONSOON_MONTHS = {6, 7, 8, 9}


def build_rural_mask(urban_boundary_fc):
    """Build the rural reference region and pixel mask."""
    urban_geom = urban_boundary_fc.geometry()

    outer = urban_geom.buffer(20000)
    inner = urban_geom.buffer(2000)
    rural_ring = outer.difference(inner)

    wc = ee.Image("ESA/WorldCover/v200/2021")
    rural_lc = wc.eq(30).Or(wc.eq(40))

    dem = ee.Image("USGS/SRTMGL1_003")
    urban_elev = dem.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=urban_geom,
        scale=30,
        maxPixels=1e9,
    ).get("elevation")
    elev_ok = dem.subtract(ee.Number(urban_elev)).abs().lt(100)

    rural_mask = rural_lc.And(elev_ok).selfMask()

    return rural_mask, rural_ring


def extract_rural_lst(year, month, rural_mask, rural_ring):
    """Extract mean rural LST for one month."""
    start = ee.Date.fromYMD(year, month, 1)
    end = start.advance(1, "month")

    collection = (
        ee.ImageCollection("MODIS/061/MOD11A1")
        .filterBounds(rural_ring)
        .filterDate(start, end)
    )

    # FIX: Relaxed QA mask — mandatory <= 1 (same as modis_lst.py v2)
    def qa_day(img):
        qc = img.select("QC_Day")
        good = qc.bitwiseAnd(0b11).lte(1).And(
            qc.bitwiseAnd(0b1100).rightShift(2).lte(1)
        )
        return img.select("LST_Day_1km").multiply(0.02).subtract(273.15).updateMask(good)

    def qa_night(img):
        qc = img.select("QC_Night")
        good = qc.bitwiseAnd(0b11).lte(1).And(
            qc.bitwiseAnd(0b1100).rightShift(2).lte(1)
        )
        return img.select("LST_Night_1km").multiply(0.02).subtract(273.15).updateMask(good)

    day_median = collection.map(qa_day).median().updateMask(rural_mask)
    night_median = collection.map(qa_night).median().updateMask(rural_mask)

    day_stats = day_median.reduceRegion(
        reducer=ee.Reducer.mean().combine(ee.Reducer.stdDev(), "", True)
        .combine(ee.Reducer.count(), "", True),
        geometry=rural_ring,
        scale=1000,
        maxPixels=1e9,
    )

    night_stats = night_median.reduceRegion(
        reducer=ee.Reducer.mean().combine(ee.Reducer.stdDev(), "", True)
        .combine(ee.Reducer.count(), "", True),
        geometry=rural_ring,
        scale=1000,
        maxPixels=1e9,
    )

    return day_stats, night_stats


def main():
    print("=" * 60)
    print("  MULTI-YEAR RURAL REFERENCE LST (v2 — relaxed QA)")
    print("=" * 60)

    print(f"\n[1/3] Loading urban boundary...")
    boundary_gdf = __import__("geopandas").read_file(BOUNDARY_PATH)
    boundary_geojson = __import__("json").loads(boundary_gdf.to_json())
    urban_fc = ee.FeatureCollection(boundary_geojson)

    print("  Building rural reference mask (20km buffer, cropland+grass)...")
    rural_mask, rural_ring = build_rural_mask(urban_fc)
    print("  ✓ Rural mask ready")

    all_rows = []
    total = len(YEARS) * len(MONTHS)
    step = 0

    for year in YEARS:
        for month in MONTHS:
            step += 1
            label = f"{year}-{MONTH_NAMES[month]}"
            print(f"\n  [{step:2d}/{total}] {label} ...", end=" ", flush=True)

            try:
                day_stats, night_stats = extract_rural_lst(
                    year, month, rural_mask, rural_ring
                )
                d_info = day_stats.getInfo()
                n_info = night_stats.getInfo()

                d_mean = d_info.get("LST_Day_1km_mean")
                d_std = d_info.get("LST_Day_1km_stdDev")
                d_count = d_info.get("LST_Day_1km_count")
                n_mean = n_info.get("LST_Night_1km_mean")
                n_std = n_info.get("LST_Night_1km_stdDev")
                n_count = n_info.get("LST_Night_1km_count")

                all_rows.append(
                    {
                        "year": year,
                        "month": month,
                        "month_name": MONTH_NAMES[month],
                        "is_monsoon": 1 if month in MONSOON_MONTHS else 0,
                        "rural_lst_day": round(d_mean, 2) if d_mean else np.nan,
                        "rural_lst_day_std": round(d_std, 2) if d_std else np.nan,
                        "rural_n_day_pixels": int(d_count) if d_count else 0,
                        "rural_lst_night": round(n_mean, 2) if n_mean else np.nan,
                        "rural_lst_night_std": round(n_std, 2) if n_std else np.nan,
                        "rural_n_night_pixels": int(n_count) if n_count else 0,
                    }
                )

                d_str = f"{d_mean:.1f}±{d_std:.1f}" if d_mean and d_std else "N/A"
                n_str = f"{n_mean:.1f}±{n_std:.1f}" if n_mean and n_std else "N/A"
                print(f"Day {d_str}°C | Night {n_str}°C  ✓")

            except Exception as e:
                print(f"⚠ ERROR: {e}")

    df = pd.DataFrame(all_rows)
    out_path = DATA_DIR / "nagpur_rural_reference_multiyear.parquet"
    df.to_parquet(out_path, index=False)

    print(f"\n[3/3] Saved to {out_path}")
    print("=" * 60)
    print("  RURAL REFERENCE SUMMARY")
    print("=" * 60)
    print(f"  Rows: {len(df)}")
    print(f"  Day coverage:   {df['rural_lst_day'].notna().sum()}/{len(df)}")
    print(f"  Night coverage: {df['rural_lst_night'].notna().sum()}/{len(df)}")
    if df["rural_lst_day"].notna().any():
        print(f"  Day range:   {df['rural_lst_day'].min():.1f} to"
              f" {df['rural_lst_day'].max():.1f} °C")
    if df["rural_lst_night"].notna().any():
        print(f"  Night range: {df['rural_lst_night'].min():.1f} to"
              f" {df['rural_lst_night'].max():.1f} °C")
    else:
        print(f"  ⚠ Night still 100% null")
    print("=" * 60)


if __name__ == "__main__":
    main()
