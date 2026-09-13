"""
SHAP Explainability Module (FR-61).
=====================================
Calculates feature contributions for any specific grid cell
and translates them into plain language for planners.
"""

import json
import lightgbm as lgb
import pandas as pd
import shap
from pathlib import Path

CITY = "nagpur"
TABLE_DIR = Path("data/tables")
MODEL_DIR = Path("models/registry")


def explain_cell(cell_id):
    """Explain why a specific cell is hot using SHAP values."""
    # Load model and data
    model = lgb.Booster(model_file=str(MODEL_DIR / "lightgbm_suhii_night.txt"))
    df = pd.read_parquet(TABLE_DIR / f"{CITY}_suhii_2024.parquet")

    cell_data = df[df["cell_id"] == cell_id]
    if len(cell_data) == 0:
        return f"Cell {cell_id} not found."

    features = ["frac_built", "frac_tree", "frac_water", "frac_crop", "frac_grass"]
    X_cell = cell_data[features]

    # Compute SHAP values
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_cell)[0]

    actual_suhii = cell_data["suhii_night"].values[0]

    # Form human-readable explanation
    explanation = []
    templates = {
        "frac_built": "{val:.0%} sealed surface adds +{shap:.2f}°C",
        "frac_tree": "{val:.0%} tree canopy subtracts {shap:.2f}°C",
        "frac_water": "{val:.0%} water coverage subtracts {shap:.2f}°C",
        "frac_crop": "Farmland presence effect: {shap:+.2f}°C",
        "frac_grass": "Open grass/park effect: {shap:+.2f}°C"
    }

    for feature, shap_val in zip(features, shap_values):
        val = X_cell[feature].values[0]
        tmpl = templates.get(feature, "{feature}: {shap:+.2f}°C")
        explanation.append({
            "feature": feature,
            "value": float(val),
            "shap_contribution_degC": round(float(shap_val), 2),
            "text": tmpl.format(val=val, shap=abs(shap_val))
        })

    # Sort by impact
    explanation.sort(key=lambda x: abs(x["shap_contribution_degC"]), reverse=True)

    return {
        "cell_id": cell_id,
        "night_suhii_degC": round(float(actual_suhii), 2),
        "drivers": explanation
    }


def main():
    print("=" * 55)
    print("  Chhaon — SHAP Explainability Engine (FR-61)")
    print("=" * 55)

    df = pd.read_parquet(TABLE_DIR / f"{CITY}_suhii_2024.parquet")
    hottest_cell = df.loc[df["suhii_night"].idxmax(), "cell_id"]

    res = explain_cell(hottest_cell)

    print(f"\n🔥 Analyzing Hottest Cell in Nagpur ({res['cell_id']}):")
    print(f"   Night Heat Anomaly: +{res['night_suhii_degC']} °C above rural")
    print("-" * 55)
    print("   Primary Thermal Drivers:")
    for d in res["drivers"]:
        print(f"     • {d['text']}")
    print("=" * 55)


if __name__ == "__main__":
    main()
