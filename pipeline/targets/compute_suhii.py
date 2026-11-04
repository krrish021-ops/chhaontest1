"""
Multi-year SUHII computation + per-cell trend estimation.

SUHII = Cell_LST − Rural_Reference_LST  (per year-month, day and night)

Trend: Theil-Sen slope on annual-mean SUHII (2020→2024), robust to outliers.
       Mann-Kendall p-value for significance.

Outputs:
  data/tables/nagpur_suhii_multiyear.parquet   (cell × year-month)
  data/tables/nagpur_suhii_trends.parquet      (cell × trend)
"""

import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats

DATA_DIR = Path("data/tables")


def theil_sen_trend(years, values):
    """
    Compute Theil-Sen slope and Mann-Kendall p-value.
    Robust to outliers — preferred over OLS for climate data.
    Returns (slope_per_year, p_value, n_valid).
    """
    mask = ~np.isnan(values)
    y_clean = years[mask]
    v_clean = values[mask]
    n = len(v_clean)

    if n < 3:
        return np.nan, np.nan, n

    # Theil-Sen slope
    slope, intercept, lo, hi = stats.theilslopes(v_clean, y_clean, alpha=0.9)

    # Mann-Kendall significance (simplified: Kendall tau)
    tau, p_value = stats.kendalltau(y_clean, v_clean)

    return round(slope, 4), round(p_value, 4), n


def main():
    print("=" * 60)
    print("  MULTI-YEAR SUHII COMPUTATION + TREND")
    print("=" * 60)

    # Load urban LST
    lst_path = DATA_DIR / "nagpur_monthly_lst_multiyear.parquet"
    print(f"\n[1/5] Loading urban LST from {lst_path}...")
    df_lst = pd.read_parquet(lst_path)
    print(f"  ✓ {len(df_lst)} rows, {df_lst['cell_id'].nunique()} cells,"
          f" {df_lst['year'].nunique()} years")

    # Load rural reference
    rural_path = DATA_DIR / "nagpur_rural_reference_multiyear.parquet"
    print(f"\n[2/5] Loading rural reference from {rural_path}...")
    df_rural = pd.read_parquet(rural_path)
    print(f"  ✓ {len(df_rural)} year-months")

    # Merge on year + month
    print(f"\n[3/5] Computing SUHII (urban − rural)...")
    df = df_lst.merge(
        df_rural[["year", "month", "rural_lst_day", "rural_lst_night"]],
        on=["year", "month"],
        how="left",
    )

    # SUHII = Cell − Rural
    df["suhii_day"] = df["lst_day"] - df["rural_lst_day"]
    df["suhii_night"] = df["lst_night"] - df["rural_lst_night"]

    # Round
    df["suhii_day"] = df["suhii_day"].round(2)
    df["suhii_night"] = df["suhii_night"].round(2)

    valid_day = df["suhii_day"].notna().sum()
    valid_night = df["suhii_night"].notna().sum()
    print(f"  ✓ SUHII computed: {valid_day} day, {valid_night} night values")

    # Quick stats for non-monsoon months
    df_peak = df[(df["is_monsoon"] == 0) & df["suhii_night"].notna()]
    if len(df_peak) > 0:
        print(f"\n  Peak-season (Mar-May) night SUHII stats:")
        print(f"    Mean:  {df_peak['suhii_night'].mean():+.2f} °C")
        print(f"    Max:   {df_peak['suhii_night'].max():+.2f} °C")
        print(f"    Min:   {df_peak['suhii_night'].min():+.2f} °C")

    # Save full SUHII table
    suhii_path = DATA_DIR / "nagpur_suhii_multiyear.parquet"
    df.to_parquet(suhii_path, index=False)
    print(f"\n  ✓ Saved {len(df)} rows to {suhii_path}")

    # ── Per-cell trend estimation ────────────────────────────────────
    print(f"\n[4/5] Computing per-cell SUHII trends (Theil-Sen)...")

    # Annual mean SUHII per cell (Mar-May only, exclude monsoon June)
    df_trend_input = df[(df["is_monsoon"] == 0)].copy()
    annual = (
        df_trend_input.groupby(["cell_id", "year"])[["suhii_day", "suhii_night"]]
        .mean()
        .reset_index()
    )

    trends = []
    for cell_id, group in annual.groupby("cell_id"):
        years = group["year"].values.astype(float)

        day_slope, day_p, day_n = theil_sen_trend(
            years, group["suhii_day"].values
        )
        night_slope, night_p, night_n = theil_sen_trend(
            years, group["suhii_night"].values
        )

        trends.append(
            {
                "cell_id": cell_id,
                "suhii_day_trend_c_per_year": day_slope,
                "suhii_day_trend_p_value": day_p,
                "suhii_day_trend_n_years": day_n,
                "suhii_night_trend_c_per_year": night_slope,
                "suhii_night_trend_p_value": night_p,
                "suhii_night_trend_n_years": night_n,
                # Decadal rate (×10) for reporting
                "suhii_night_trend_c_per_decade": round(night_slope * 10, 3)
                if night_slope and not np.isnan(night_slope)
                else np.nan,
            }
        )

    df_trends = pd.DataFrame(trends)
    trend_path = DATA_DIR / "nagpur_suhii_trends.parquet"
    df_trends.to_parquet(trend_path, index=False)

    # Trend summary
    sig_night = df_trends[
        (df_trends["suhii_night_trend_p_value"] < 0.1)
        & df_trends["suhii_night_trend_c_per_year"].notna()
    ]
    warming = sig_night[sig_night["suhii_night_trend_c_per_year"] > 0]
    cooling = sig_night[sig_night["suhii_night_trend_c_per_year"] < 0]

    print(f"\n[5/5] Trend summary:")
    print(f"  Cells with trend data: {len(df_trends)}")
    print(f"  Significant night trends (p<0.1): {len(sig_night)}")
    print(f"    Warming: {len(warming)} cells")
    print(f"    Cooling: {len(cooling)} cells")
    if len(sig_night) > 0:
        print(
            f"    Median night trend: "
            f"{sig_night['suhii_night_trend_c_per_decade'].median():+.2f} °C/decade"
        )

    print(f"\n  ✓ Saved trends to {trend_path}")
    print("=" * 60)
    print("  SUHII MULTI-YEAR COMPLETE")
    print("=" * 60)
    print(f"  Full data:  {suhii_path} ({len(df)} rows)")
    print(f"  Trends:     {trend_path} ({len(df_trends)} cells)")
    print("=" * 60)


if __name__ == "__main__":
    main()
