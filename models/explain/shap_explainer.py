"""
SHAP Explainability Module (FR-61).
=====================================
Calculates real feature contributions (via LightGBM TreeExplainer) for
any specific grid cell in Nagpur or Pune, and translates them into
plain language for planners.

Uses the v1 5-feature model (lightgbm_suhii_night.txt) since it is the
only booster whose feature schema (frac_built/tree/water/crop/grass)
matches both cities' tables.
"""

from pathlib import Path
import lightgbm as lgb
import pandas as pd
import shap

TABLE_DIR = Path("data/tables")
MODEL_DIR = Path("models/registry")

FEATURES = ["frac_built", "frac_tree", "frac_water", "frac_crop", "frac_grass"]

_EXPLAINER_CACHE: dict = {}

_TEMPLATES = {
    "frac_built": "{val:.0%} sealed surface adds +{shap:.2f}°C",
    "frac_tree": "{val:.0%} tree canopy subtracts {shap:.2f}°C",
    "frac_water": "{val:.0%} water coverage subtracts {shap:.2f}°C",
    "frac_crop": "Farmland presence effect: {shap:+.2f}°C",
    "frac_grass": "Open grass/park effect: {shap:+.2f}°C",
}


def _get_explainer(model_name: str = "lightgbm_suhii_night.txt"):
    """Load + cache the LightGBM booster and its SHAP TreeExplainer."""
    if model_name not in _EXPLAINER_CACHE:
        model_path = MODEL_DIR / model_name
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        booster = lgb.Booster(model_file=str(model_path))
        _EXPLAINER_CACHE[model_name] = (booster, shap.TreeExplainer(booster))
    return _EXPLAINER_CACHE[model_name]


def _load_city_table(city: str) -> pd.DataFrame:
    """Load the per-cell feature table for a given city."""
    city = city.lower()

    if city == "nagpur":
        path = TABLE_DIR / "nagpur_suhii_2024.parquet"
        if not path.exists():
            raise FileNotFoundError(f"Nagpur SUHII table not found: {path}")
        return pd.read_parquet(path)

    if city == "pune":
        path = TABLE_DIR / "pune_feature_matrix.parquet"
        if not path.exists():
            raise FileNotFoundError(f"Pune feature matrix not found: {path}")
        df = pd.read_parquet(path)
        snap = df[(df["year"] == 2024) & (df["month"] == 5)]
        if snap.empty:
            # Fallback: most recent available record per cell
            snap = (
                df.sort_values(["year", "month"])
                .groupby("cell_id", as_index=False)
                .tail(1)
            )
        return snap

    raise ValueError(f"Unsupported city for explanation: {city}")


def explain_cell(cell_id: str, city: str = None) -> dict:
    """
    Explain why a specific cell is hot using real SHAP values.

    If `city` is not given, tries Nagpur then Pune (first match wins).
    Raises FileNotFoundError if required data/model files are missing.
    Raises KeyError if the cell is not found in any supported dataset.
    """
    cities_to_try = [city] if city else ["nagpur", "pune"]
    last_error = None

    for c in cities_to_try:
        try:
            df = _load_city_table(c)
        except FileNotFoundError as e:
            last_error = e
            continue

        match = df[df["cell_id"].astype(str).str.upper() == str(cell_id).upper()]
        if len(match) == 0:
            continue

        cell_data = match.iloc[[0]]
        booster, explainer = _get_explainer()
        X_cell = cell_data[FEATURES]

        shap_values = explainer.shap_values(X_cell)[0]
        actual_suhii = float(cell_data["suhii_night"].values[0])

        explanation = []
        for feature, shap_val in zip(FEATURES, shap_values):
            val = float(X_cell[feature].values[0])
            tmpl = _TEMPLATES.get(feature, "{feature}: {shap:+.2f}°C")
            explanation.append(
                {
                    "feature": feature,
                    "value": val,
                    "shap_contribution_degC": round(float(shap_val), 2),
                    "text": tmpl.format(val=val, shap=abs(shap_val)),
                }
            )

        explanation.sort(key=lambda x: abs(x["shap_contribution_degC"]), reverse=True)

        return {
            "cell_id": str(cell_id).upper(),
            "night_suhii_degC": round(actual_suhii, 2),
            "drivers": explanation,
            "_source_city": c,
        }

    if last_error is not None:
        raise last_error
    raise KeyError(f"Cell '{cell_id}' not found in any supported city dataset.")


def main():
    print("=" * 55)
    print("  Chhaon — SHAP Explainability Engine (FR-61)")
    print("=" * 55)

    df = pd.read_parquet(TABLE_DIR / "nagpur_suhii_2024.parquet")
    hottest_cell = df.loc[df["suhii_night"].idxmax(), "cell_id"]

    res = explain_cell(hottest_cell, city="nagpur")

    print(f"\n🔥 Analyzing Hottest Cell in Nagpur ({res['cell_id']}):")
    print(f"   Night Heat Anomaly: +{res['night_suhii_degC']} °C above rural")
    print("-" * 55)
    print("   Primary Thermal Drivers:")
    for d in res["drivers"]:
        print(f"     • {d['text']}")
    print("=" * 55)


if __name__ == "__main__":
    main()
