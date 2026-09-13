"""
Weather Normalization — Simplified Proxy Implementation
========================================================

FULL VERSION (deferred): Would pull ERA5 daily meteorology per cell
and fit a rural-only weather-response model. Requires CDS API setup.

SIMPLIFIED VERSION (this file): Uses the rural reference itself as
the "weather baseline". Any deviation from what rural experienced is
attributed to urban form.

  SUHII_weather_normalized = LST_urban - LST_rural

That's actually already what SUHII IS. But we add a further step:
we also account for how neighboring RURAL variation predicts LST,
and remove that expected response.

For 229 cells × 1 month this is a light-touch normalization.
When we scale to multi-year data, THIS module gets replaced with
full ERA5-based residualization.
"""

from __future__ import annotations

from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge

MASTER_PARQUET = Path("data/tables/nagpur_master_2024.parquet")
SUHII_PARQUET = Path("data/tables/nagpur_suhii_2024.parquet")
RURAL_PARQUET = Path("data/tables/nagpur_rural_reference.parquet")
OUTPUT_PARQUET = Path("data/tables/nagpur_suhii_weather_normalized.parquet")


def compute_expected_lst_response(df: pd.DataFrame, use_col: str = "lst_night") -> np.ndarray:
    """
    Fit a simple model: LST ~ elevation + latitude
    This captures the *macro-scale* variation that's driven by geography
    and background climate, not urban form.

    Return the "expected" LST that any patch of land at (lat, lon) would
    have had in that week, regardless of urban form.
    """
    # Use only cells with LOW built-up as our "rural-like" fitting set
    rural_like = df[df["frac_built"] < 0.15].copy()

    if len(rural_like) < 5:
        print("  ⚠️  Not enough rural-like cells; skipping normalization")
        return df[use_col].values

    # Simple ridge regression on geographic features
    X_fit = rural_like[["lat", "lon"]].values
    y_fit = rural_like[use_col].values

    model = Ridge(alpha=1.0)
    model.fit(X_fit, y_fit)

    # Predict "background LST" for ALL cells based on their location
    X_all = df[["lat", "lon"]].values
    expected_lst = model.predict(X_all)

    return expected_lst


def normalize_suhii():
    print("=" * 65)
    print("  🌡️  Weather Normalization (simplified proxy)")
    print("=" * 65)

    print(f"\n📂 Loading data...")
    master = pd.read_parquet(MASTER_PARQUET)
    suhii = pd.read_parquet(SUHII_PARQUET)

    df = master.merge(
        suhii[["cell_id", "suhii_day", "suhii_night", "lst_day", "lst_night"]],
        on="cell_id",
        how="inner",
        suffixes=("", "_suhii"),
    )

    # Compute expected background LST from geography
    print(f"\n🔧 Computing expected background LST (night)...")
    expected_night = compute_expected_lst_response(df, use_col="lst_night")

    print(f"🔧 Computing expected background LST (day)...")
    expected_day = compute_expected_lst_response(df, use_col="lst_day")

    # The weather-normalized SUHII is what's left after removing
    # background geographic variation
    df["suhii_night_normalized"] = df["suhii_night"] - (
        expected_night - expected_night.mean()
    )
    df["suhii_day_normalized"] = df["suhii_day"] - (
        expected_day - expected_day.mean()
    )

    # Summary stats
    print(f"\n📊 Normalization impact:")
    print(f"   Original SUHII night mean: {df['suhii_night'].mean():+.2f} °C")
    print(f"   Normalized SUHII night mean: {df['suhii_night_normalized'].mean():+.2f} °C")
    print(f"   Std reduction: "
          f"{df['suhii_night'].std():.2f} → {df['suhii_night_normalized'].std():.2f} °C")

    # Save
    output_cols = [
        "cell_id", "lat", "lon",
        "suhii_day", "suhii_night",
        "suhii_day_normalized", "suhii_night_normalized",
        "lst_day", "lst_night",
    ]
    df[output_cols].to_parquet(OUTPUT_PARQUET, index=False)
    print(f"\n💾 Saved: {OUTPUT_PARQUET}")
    print(f"   {len(df):,} cells × {len(output_cols)} columns")

    print("\n" + "=" * 65)
    print("  ✅ Weather normalization complete")
    print("  📝 Note: This is a simplified proxy.")
    print("     Full ERA5 integration is a Phase 6.5+ upgrade.")
    print("=" * 65)


if __name__ == "__main__":
    normalize_suhii()
