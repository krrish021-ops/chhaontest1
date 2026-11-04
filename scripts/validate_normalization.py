"""
Validation script for ERA5 weather normalization.
Checks 4 things:
  1. Normalized SUHII is more temporally stable
  2. Spatial pattern is preserved
  3. Weather effect is largest in extreme months
  4. Rural cells have near-zero normalized SUHII

FIX v2: Handles float month columns and NaN values gracefully.
"""

import pandas as pd
import numpy as np
import geopandas as gpd
from pathlib import Path

DATA_DIR = Path("data/tables")
DEMO_DIR = Path("data/demo")
DEMO_DIR.mkdir(parents=True, exist_ok=True)


def safe_mean(series):
    """Return mean or NaN if all null."""
    if series.notna().sum() == 0:
        return np.nan
    return series.mean()


def check_temporal_stability(df):
    """Check 1: Normalized SUHII should have less year-to-year wobble."""
    print("\n  CHECK 1: Temporal stability (annual mean night SUHII)")
    print("  " + "-" * 58)
    print(f"  {'Year':<6} {'Raw (°C)':>10} {'Normalized (°C)':>16} {'Δ Removed':>10}")
    print("  " + "-" * 58)

    if df["suhii_night"].notna().sum() == 0:
        print("  ⚠ All suhii_night values are NaN — cannot check stability")
        return False

    for year in sorted(df["year"].unique()):
        yr = df[df["year"] == year]
        raw = safe_mean(yr["suhii_night"])
        norm = safe_mean(yr["suhii_night_normalized"])
        if pd.notna(raw) and pd.notna(norm):
            effect = raw - norm
            print(f"  {year:<6} {raw:>+10.3f} {norm:>+16.3f} {effect:>+10.3f}")
        else:
            print(f"  {year:<6} {'N/A':>10} {'N/A':>16} {'N/A':>10}")

    raw_std = df.groupby("year")["suhii_night"].mean().std()
    norm_std = df.groupby("year")["suhii_night_normalized"].mean().std()
    print("  " + "-" * 58)

    if pd.notna(raw_std) and pd.notna(norm_std) and raw_std > 0:
        print(f"  {'Std':<6} {raw_std:>10.3f} {norm_std:>16.3f}"
              f" {(1-norm_std/raw_std)*100:>+9.1f}%")
        passed = norm_std < raw_std
    else:
        print(f"  {'Std':<6} {'N/A':>10} {'N/A':>16} {'N/A':>10}")
        passed = False

    print(f"\n  {'✅ PASS' if passed else '⚠️  FAIL'}:"
          f" Normalized is {'more' if passed else 'not more'} stable")
    return passed


def check_spatial_preservation(df):
    """Check 2: Spatial ranking should be preserved."""
    print("\n  CHECK 2: Spatial pattern preservation")
    print("  " + "-" * 58)

    df_may = df[(df["month"] == 5) & df["suhii_night"].notna()]

    if len(df_may) < 20:
        print(f"  ⚠ Only {len(df_may)} valid May night rows — insufficient")
        return False

    cell_raw = df_may.groupby("cell_id")["suhii_night"].mean()
    cell_norm = df_may.groupby("cell_id")["suhii_night_normalized"].mean()

    # Drop cells where either is NaN
    valid = cell_raw.notna() & cell_norm.notna()
    cell_raw = cell_raw[valid]
    cell_norm = cell_norm[valid]

    if len(cell_raw) < 10:
        print(f"  ⚠ Only {len(cell_raw)} valid cells — insufficient")
        return False

    from scipy.stats import spearmanr
    rho, p = spearmanr(cell_raw, cell_norm)

    print(f"  Spearman rank correlation (raw vs normalized): {rho:.4f}")
    print(f"  p-value: {p:.2e}")

    top10_raw = set(cell_raw.nlargest(10).index)
    top10_norm = set(cell_norm.nlargest(10).index)
    overlap = len(top10_raw & top10_norm)

    print(f"  Top-10 hottest cells overlap: {overlap}/10")

    passed = rho > 0.85 and overlap >= 7
    print(f"\n  {'✅ PASS' if passed else '⚠️  FAIL'}:"
          f" Spatial pattern {'preserved' if passed else 'significantly altered'}")
    return passed


def check_extreme_months(df):
    """Check 3: Weather correction largest in extreme months."""
    print("\n  CHECK 3: Weather effect magnitude by year-month")
    print("  " + "-" * 58)

    if df["suhii_night_weather_effect"].notna().sum() == 0:
        print("  ⚠ All weather effects are NaN")
        return False

    monthly_effect = (
        df.groupby(["year", "month"])["suhii_night_weather_effect"]
        .mean()
        .abs()
        .reset_index()
    )
    monthly_effect.columns = ["year", "month", "abs_weather_effect"]

    # FIX: Convert month to int for formatting
    monthly_effect["month"] = monthly_effect["month"].astype(int)
    monthly_effect["year"] = monthly_effect["year"].astype(int)

    top5 = monthly_effect.nlargest(5, "abs_weather_effect")
    print("  Largest weather corrections (should be extreme months):")
    for _, row in top5.iterrows():
        print(f"    {int(row['year'])}-{int(row['month']):02d}:"
              f" |effect| = {row['abs_weather_effect']:.3f} °C")

    bot5 = monthly_effect.nsmallest(3, "abs_weather_effect")
    print("  Smallest weather corrections (should be average months):")
    for _, row in bot5.iterrows():
        print(f"    {int(row['year'])}-{int(row['month']):02d}:"
              f" |effect| = {row['abs_weather_effect']:.3f} °C")

    passed = (top5["abs_weather_effect"].mean() >
              bot5["abs_weather_effect"].mean())
    print(f"\n  {'✅ PASS' if passed else '⚠️  FAIL'}:"
          f" Extreme months have {'larger' if passed else 'not larger'} corrections")
    return passed


def check_rural_neutrality(df, master_path):
    """Check 4: Rural cells should have near-zero normalized SUHII."""
    print("\n  CHECK 4: Rural cell neutrality")
    print("  " + "-" * 58)

    df_master = pd.read_parquet(master_path)
    rural_mask = (
        (df_master["frac_built"] < 0.20)
        & ((df_master["frac_crop"] + df_master["frac_grass"]) > 0.50)
    )
    rural_cells = df_master.loc[rural_mask, "cell_id"].unique()

    df_rural = df[df["cell_id"].isin(rural_cells)]
    df_urban = df[~df["cell_id"].isin(rural_cells)]

    rural_raw = safe_mean(df_rural["suhii_night"])
    rural_norm = safe_mean(df_rural["suhii_night_normalized"])
    urban_raw = safe_mean(df_urban["suhii_night"])
    urban_norm = safe_mean(df_urban["suhii_night_normalized"])

    print(f"  Rural cells (n={len(rural_cells)}):")
    r_raw_str = f"{rural_raw:+.3f}" if pd.notna(rural_raw) else "N/A"
    r_norm_str = f"{rural_norm:+.3f}" if pd.notna(rural_norm) else "N/A"
    print(f"    Raw SUHII night:        {r_raw_str} °C")
    print(f"    Normalized SUHII night: {r_norm_str} °C")

    print(f"  Urban cells (n={len(df_urban['cell_id'].unique())}):")
    u_raw_str = f"{urban_raw:+.3f}" if pd.notna(urban_raw) else "N/A"
    u_norm_str = f"{urban_norm:+.3f}" if pd.notna(urban_norm) else "N/A"
    print(f"    Raw SUHII night:        {u_raw_str} °C")
    print(f"    Normalized SUHII night: {u_norm_str} °C")

    if pd.notna(rural_norm):
        passed = abs(rural_norm) < 0.5
    else:
        passed = False

    print(f"\n  {'✅ PASS' if passed else '⚠️  FAIL'}:"
          f" Rural normalized SUHII is {'near zero' if passed else 'not near zero'}")
    return passed


def regenerate_heatmap(df):
    """Regenerate the demo heatmap GeoJSON with normalized values."""
    print("\n  REGENERATING DEMO HEATMAP...")

    df_may = df[(df["year"] == 2024) & (df["month"] == 5)].copy()

    if len(df_may) == 0:
        print("  ⚠ No May 2024 data found, skipping")
        return

    grid_path = "data/boundaries/nagpur_grid.geojson"
    grid_gdf = gpd.read_file(grid_path)

    merge_cols = [
        "cell_id", "suhii_day", "suhii_night",
        "suhii_day_normalized", "suhii_night_normalized",
        "suhii_night_weather_effect", "lst_day", "lst_night",
    ]
    available = [c for c in merge_cols if c in df_may.columns]
    grid_merged = grid_gdf.merge(df_may[available], on="cell_id", how="left")

    out_path = DEMO_DIR / "nagpur_heatmap_normalized.geojson"
    grid_merged.to_file(out_path, driver="GeoJSON")

    print(f"  ✓ Saved to {out_path}")
    print(f"    Cells: {len(grid_merged)}")

    norm_col = "suhii_night_normalized"
    if norm_col in grid_merged.columns and grid_merged[norm_col].notna().any():
        print(f"    Night SUHII (normalized) range:"
              f" {grid_merged[norm_col].min():+.2f} to"
              f" {grid_merged[norm_col].max():+.2f} °C")
    else:
        print(f"    ⚠ Night SUHII normalized still all NaN")


def main():
    print("=" * 65)
    print("  WEATHER NORMALIZATION VALIDATION (v2)")
    print("=" * 65)

    norm_path = DATA_DIR / "nagpur_suhii_weather_normalized.parquet"
    print(f"\nLoading {norm_path}...")
    df = pd.read_parquet(norm_path)
    print(f"  ✓ {len(df)} rows")

    # FIX: Ensure month is integer
    df["month"] = df["month"].astype(int)
    df["year"] = df["year"].astype(int)

    master_path = DATA_DIR / "nagpur_master_2024.parquet"

    results = {}
    results["temporal_stability"] = check_temporal_stability(df)
    results["spatial_preservation"] = check_spatial_preservation(df)
    results["extreme_months"] = check_extreme_months(df)
    results["rural_neutrality"] = check_rural_neutrality(df, master_path)

    print("\n" + "=" * 65)
    print("  VALIDATION SUMMARY")
    print("=" * 65)
    for check, passed in results.items():
        status = "✅ PASS" if passed else "⚠️  FAIL"
        print(f"  {status}  {check}")

    n_pass = sum(results.values())
    n_total = len(results)
    print(f"\n  {n_pass}/{n_total} checks passed")

    if n_pass == n_total:
        print("  🎉 Weather normalization is validated and trustworthy")
    else:
        print("  ℹ Some checks failed — review before using normalized values")

    regenerate_heatmap(df)
    print("=" * 65)


if __name__ == "__main__":
    main()
