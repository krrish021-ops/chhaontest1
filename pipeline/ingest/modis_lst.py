"""
Multi-year MODIS LST extraction for Nagpur (or any configured city).
Extracts monthly composites for 2020-2024, March-June (pre-monsoon peak heat).
Uses server-side batch reduceRegions — all grid cells per call, ~3 sec each.

FIX v2: Relaxed QA mask — mandatory QA <= 1 (accepts "other quality" pixels
that are standard over India at night). Previous mask required == 0 which
rejected 100% of night observations.

Outputs:
  data/tables/nagpur_monthly_lst_multiyear.parquet
"""

import ee
import pandas as pd
import geopandas as gpd
import json
import numpy as np
from pathlib import Path

ee.Initialize(project="chhaon-508513")

DATA_DIR = Path("data/tables")
DATA_DIR.mkdir(parents=True, exist_ok=True)

CITY_NAME = "Nagpur"
GRID_PATH = "data/boundaries/nagpur_grid.geojson"

YEARS = [2020, 2021, 2022, 2023, 2024]
MONTHS = [3, 4, 5, 6]
MONTH_NAMES = {3: "Mar", 4: "Apr", 5: "May", 6: "Jun"}
SEASON_TAG = "pre_monsoon"
MONSOON_MONTHS = {6, 7, 8, 9}


def qa_mask_day(img):
    """
    QA mask for MODIS daytime LST.
    Bits 0-1 (mandatory quality): <= 1 (good OR acceptable)
    Bits 2-3 (data quality): <= 1 (good or acceptable)

    FIX: Changed mandatory from .eq(0) to .lte(1).
    Over India, mandatory QA 01 ("produced, other quality") is common
    due to atmospheric dust/haze. Rejecting it loses most observations.
    """
    qc = img.select("QC_Day")
    mandatory = qc.bitwiseAnd(0b11)
    quality = qc.bitwiseAnd(0b1100).rightShift(2)
    good = mandatory.lte(1).And(quality.lte(1))

    lst_k = img.select("LST_Day_1km").multiply(0.02)
    lst_c = lst_k.subtract(273.15)
    return lst_c.updateMask(good).rename("lst_day")


def qa_mask_night(img):
    """
    QA mask for MODIS nighttime LST.
    Same relaxed criteria as day.

    FIX: This is the critical change. Night LST over India almost always
    has mandatory QA = 01, not 00. The old mask (.eq(0)) rejected 100%
    of night pixels. The new mask (.lte(1)) accepts them.
    """
    qc = img.select("QC_Night")
    mandatory = qc.bitwiseAnd(0b11)
    quality = qc.bitwiseAnd(0b1100).rightShift(2)
    good = mandatory.lte(1).And(quality.lte(1))

    lst_k = img.select("LST_Night_1km").multiply(0.02)
    lst_c = lst_k.subtract(273.15)
    return lst_c.updateMask(good).rename("lst_night")


def extract_month(year, month, grid_fc):
    """Extract day + night LST for one month across all grid cells."""
    start = ee.Date.fromYMD(year, month, 1)
    end = start.advance(1, "month")

    collection = (
        ee.ImageCollection("MODIS/061/MOD11A1")
        .filterBounds(grid_fc.geometry())
        .filterDate(start, end)
    )

    day_images = collection.map(qa_mask_day)
    day_composite = day_images.median()

    night_images = collection.map(qa_mask_night)
    night_composite = night_images.median()

    day_count = day_images.count().rename("n_valid_day")
    night_count = night_images.count().rename("n_valid_night")

    combined = (
        day_composite
        .addBands(night_composite)
        .addBands(day_count)
        .addBands(night_count)
    )

    extracted = combined.reduceRegions(
        collection=grid_fc,
        reducer=ee.Reducer.mean(),
        scale=1000,
    )

    is_monsoon = 1 if month in MONSOON_MONTHS else 0

    extracted = extracted.map(
        lambda f: f.set(
            {
                "year": year,
                "month": month,
                "month_name": MONTH_NAMES.get(month, str(month)),
                "season": SEASON_TAG,
                "is_monsoon": is_monsoon,
                "data_confidence": "high" if month not in MONSOON_MONTHS else "low_cloud_risk",
            }
        )
    )

    return extracted


def main():
    print("=" * 65)
    print("  MULTI-YEAR MODIS LST EXTRACTION (v2 — relaxed QA)")
    print(f"  City: {CITY_NAME}")
    print(f"  Years: {YEARS}")
    print(f"  Months: {[MONTH_NAMES[m] for m in MONTHS]}")
    print(f"  QA fix: mandatory <= 1 (was == 0)")
    print("=" * 65)

    print(f"\n[1/3] Loading grid from {GRID_PATH}...")
    grid_gdf = gpd.read_file(GRID_PATH)
    n_cells = len(grid_gdf)
    print(f"  ✓ {n_cells} grid cells loaded")

    grid_geojson = json.loads(grid_gdf.to_json())
    grid_fc = ee.FeatureCollection(grid_geojson)

    all_rows = []
    total = len(YEARS) * len(MONTHS)
    step = 0

    for year in YEARS:
        for month in MONTHS:
            step += 1
            label = f"{year}-{MONTH_NAMES[month]}"
            print(f"\n  [{step:2d}/{total}] {label} ...", end=" ", flush=True)

            try:
                extracted = extract_month(year, month, grid_fc)
                info = extracted.getInfo()

                for feat in info["features"]:
                    p = feat["properties"]
                    all_rows.append(
                        {
                            "cell_id": p.get("cell_id", ""),
                            "year": year,
                            "month": month,
                            "month_name": MONTH_NAMES.get(month, ""),
                            "season": SEASON_TAG,
                            "is_monsoon": p.get("is_monsoon", 0),
                            "data_confidence": p.get("data_confidence", ""),
                            "lst_day": round(p.get("lst_day", np.nan), 2)
                            if p.get("lst_day") is not None
                            else np.nan,
                            "lst_night": round(p.get("lst_night", np.nan), 2)
                            if p.get("lst_night") is not None
                            else np.nan,
                            "n_valid_day": int(p.get("n_valid_day", 0) or 0),
                            "n_valid_night": int(p.get("n_valid_night", 0) or 0),
                        }
                    )

                day_vals = [
                    r["lst_day"] for r in all_rows[-n_cells:] if pd.notna(r["lst_day"])
                ]
                night_vals = [
                    r["lst_night"]
                    for r in all_rows[-n_cells:]
                    if pd.notna(r["lst_night"])
                ]
                d_avg = f"{sum(day_vals)/len(day_vals):.1f}" if day_vals else "N/A"
                n_avg = f"{sum(night_vals)/len(night_vals):.1f}" if night_vals else "N/A"
                d_pct = f"{len(day_vals)}/{n_cells}"
                n_pct = f"{len(night_vals)}/{n_cells}"
                print(f"Day {d_avg}°C ({d_pct}) | Night {n_avg}°C ({n_pct})  ✓")

            except ee.EEException as e:
                print(f"⚠ GEE ERROR: {e}")
            except Exception as e:
                print(f"⚠ ERROR: {e}")

    df = pd.DataFrame(all_rows)

    print(f"\n[2/3] Quality check...")
    low_day = df[df["n_valid_day"] < 4]
    low_night = df[df["n_valid_night"] < 4]
    print(f"  Day:   {len(low_day)} cell-months with <4 valid obs"
          f" ({100*len(low_day)/len(df):.1f}%)")
    print(f"  Night: {len(low_night)} cell-months with <4 valid obs"
          f" ({100*len(low_night)/len(df):.1f}%)")

    monsoon_flagged = df[df["is_monsoon"] == 1]
    if len(monsoon_flagged) > 0:
        print(f"  ℹ {len(monsoon_flagged)} cell-months flagged as monsoon")

    out_path = DATA_DIR / "nagpur_monthly_lst_multiyear.parquet"
    df.to_parquet(out_path, index=False)

    print(f"\n[3/3] Saved to {out_path}")
    print("=" * 65)
    print("  RESULTS SUMMARY")
    print("=" * 65)
    print(f"  Total rows:       {len(df)}")
    print(f"  Day coverage:     {df['lst_day'].notna().sum()}/{len(df)}"
          f" ({100*df['lst_day'].notna().mean():.0f}%)")
    print(f"  Night coverage:   {df['lst_night'].notna().sum()}/{len(df)}"
          f" ({100*df['lst_night'].notna().mean():.0f}%)")
    if df["lst_day"].notna().any():
        print(f"  Day LST range:    {df['lst_day'].min():.1f} to"
              f" {df['lst_day'].max():.1f} °C")
    if df["lst_night"].notna().any():
        print(f"  Night LST range:  {df['lst_night'].min():.1f} to"
              f" {df['lst_night'].max():.1f} °C")
    else:
        print(f"  ⚠ Night LST still 100% null — QA fix may not have worked")
    print("=" * 65)


if __name__ == "__main__":
    main()

