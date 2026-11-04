"""
SHAP Explainability Module (FR-61) — Pan-India Support.
========================================================
Calculates real feature contributions (via LightGBM TreeExplainer) for
any specific grid cell in any ingested Indian city, and translates them
into plain language for municipal planners.
"""

from pathlib import Path
import lightgbm as lgb
import pandas as pd
import shap

from config.loader import get_all_cities

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
    """Load the per-cell feature table for any ingested Indian city."""
    city = city.lower().strip()
    candidates = [
        TABLE_DIR / f"{city}_feature_matrix.parquet",
        TABLE_DIR / f"{city}_suhii_2024.parquet",
        TABLE_DIR / f"{city}_master_2024.parquet",
    ]
    path = next((p for p in candidates if p.exists()), None)
    if path is None:
        raise FileNotFoundError(
            f"Feature table not found for city '{city}'. "
            f"Run: python -m pipeline.ingest.ingest_city {city}"
        )

    df = pd.read_parquet(path)
    if "year" in df.columns and "month" in df.columns:
        snap = df[(df["year"] == 2024) & (df["month"] == 5)]
        if snap.empty:
            snap = (
                df.sort_values(["year", "month"])
                .groupby("cell_id", as_index=False)
                .tail(1)
            )
        return snap
    return df


def _discover_available_cities() -> list[str]:
    """Return all city IDs that have feature tables on disk."""
    configured = list(get_all_cities().keys())
    found = []
    for p in TABLE_DIR.glob("*_feature_matrix.parquet"):
        c = p.name.replace("_feature_matrix.parquet", "")
        if c not in configured:
            configured.append(c)
    for c in configured:
        if any(
            (TABLE_DIR / f"{c}_{suffix}.parquet").exists()
            for suffix in ("feature_matrix", "suhii_2024", "master_2024")
        ):
            found.append(c)
    return found or ["nagpur", "pune"]


def explain_cell(cell_id: str, city: str = None) -> dict:
    """
    Explain why a specific cell is hot using real SHAP values.
    If `city` is not given, searches all ingested Indian cities on disk.
    """
    cities_to_try = [city.lower()] if city else _discover_available_cities()
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
        actual_suhii = (
            float(cell_data["suhii_night"].values[0])
            if "suhii_night" in cell_data.columns
            else float(booster.predict(X_cell)[0])
        )

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

    if last_error is not None and city is not None:
        raise last_error
    raise KeyError(f"Cell '{cell_id}' not found in any ingested city dataset.")


def main():
    print("=" * 55)
    print("  Chhaon — SHAP Explainability Engine (Pan-India)")
    print("=" * 55)

    df = _load_city_table("nagpur")
    hottest_cell = df.loc[df["suhii_night"].idxmax(), "cell_id"]
    res = explain_cell(hottest_cell, city="nagpur")

    print(f"\n🔥 Analyzing Hottest Cell in Nagpur ({res['cell_id']}):")
    print(f"   Night Heat Anomaly: +{res['night_suhii_degC']} °C above rural")
    print("-" * 55)
    for d in res["drivers"]:
        print(f"     • {d['text']}")
    print("=" * 55)


if __name__ == "__main__":
    main()
