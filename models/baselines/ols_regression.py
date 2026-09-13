"""
OLS Panel Regression Baseline Model (M1 from TRD).
===================================================
Fits an interpretable linear formula:
  SUHII = β1·frac_built + β2·frac_tree + β3·frac_water + intercept

Produces the exact transparent sentence needed for official reports:
"Every 10 percentage-point increase in sealed surface raises night heat by X°C,
 while every 10 pp increase in tree canopy lowers it by Y°C."
"""

import pandas as pd
import statsmodels.api as sm
from pathlib import Path

CITY = "nagpur"
TABLE_DIR = Path("data/tables")


def main():
    print("=" * 55)
    print("  Chhaon — M1 OLS Panel Regression Model")
    print("=" * 55)

    data_path = TABLE_DIR / f"{CITY}_suhii_2024.parquet"
    if not data_path.exists():
        print("⚠️ Data not found. Complete Phase 2 first.")
        return

    df = pd.read_parquet(data_path)

    # Features (predictors) and Target
    feature_cols = ["frac_built", "frac_tree", "frac_water"]
    X = df[feature_cols]
    X = sm.add_constant(X)  # Add intercept

    # 1. Fit Nighttime SUHII Model
    y_night = df["suhii_night"]
    model_night = sm.OLS(y_night, X).fit()

    print("\n🌙 Nighttime Thermal Coefficients (M1):")
    print("-" * 55)
    for col in feature_cols:
        coef = model_night.params[col]
        pval = model_night.pvalues[col]
        print(f"  {col:<12}: {coef:>+6.2f} °C shift per 100% change (p={pval:.4f})")

    r2_night = model_night.rsquared
    print(f"\n  Model R² Score: {r2_night:.3f}")

    # Quote generator for PDF reports
    b_built = model_night.params["frac_built"] * 0.10
    b_tree = model_night.params["frac_tree"] * 0.10

    print("\n📜 Official Report Quote:")
    print(f'  "In {CITY.title()}, every 10 percentage-point increase in concrete')
    print(f'   raises nighttime heat by {abs(b_built):.2f}°C, while every 10 pp')
    print(f'   increase in tree canopy cools it by {abs(b_tree):.2f}°C."')
    print("=" * 55)


if __name__ == "__main__":
    main()

