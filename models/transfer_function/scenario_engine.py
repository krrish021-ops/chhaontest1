"""
Scenario Simulation Engine — WITH UNCERTAINTY BANDS & DOMAIN GUARD (v3).

Every prediction now returns:
  - Uncertainty bands (P10, P50, P90)
  - Extrapolation warnings (Mahalanobis distance domain check)
  - Cross-city model warning (see NATIVE_MODEL_CITY below)

This lets the frontend show: "-1.15°C (range: -0.6 to -1.7°C)"
AND warn the user if they painted an unrealistic scenario (e.g. 100% water)
OR if the prediction is being made by a model trained on a different city.

SUPPORTED ACTIONS — WHY ONLY THESE THREE:
  This engine mutates land-cover FRACTION features only
  (frac_built, frac_tree, frac_water, frac_crop, frac_grass).
  The underlying model (lightgbm_suhii_night_p10/p50/p90, trained on 5
  land-cover fractions) has NO albedo/reflectivity feature dimension.

  This means levers that work by changing surface reflectivity rather
  than land-cover class — e.g. "cool roofs" — CANNOT be physically
  represented by this model today. Do not add a "cool_roofs" action
  here without first adding an albedo feature to the model (the v2
  19-feature model, lightgbm_suhii_night_v2.txt, DOES have an "albedo"
  column already — a cool-roof lever should be built on top of that
  model, not this one). See docs/PROJECT_STATE_CONTEXT.md §7 item 8.

MULTI-CITY SUPPORT — HONESTY NOTE:
  The trained quantile models (p10/p50/p90) were fit ONLY on Nagpur
  data (229 cells, May 2024). Pune has no quantile models or
  domain-guard training distribution of its own yet.

  When a Pune cell is evaluated, this engine applies the NAGPUR-TRAINED
  model to Pune's real land-cover fractions. This is a genuine
  cross-city extrapolation (the project's own city-block validation,
  see models/cv/city_block_cv.py, found this transfer performs POORLY
  — R² < 0 in both directions). We do NOT hide this: every response
  includes "cross_city_model": True for any non-Nagpur city, in
  addition to (and separate from) the feature-space domain guard.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import pandas as pd
import lightgbm as lgb

from models.cv.domain_guard import check_domain

# ---------------------------------------------------------------------------
REGISTRY_DIR = Path("models/registry")
MODEL_P50 = REGISTRY_DIR / "lightgbm_suhii_night_p50.txt"
MODEL_P10 = REGISTRY_DIR / "lightgbm_suhii_night_p10.txt"
MODEL_P90 = REGISTRY_DIR / "lightgbm_suhii_night_p90.txt"
FALLBACK_MODEL = REGISTRY_DIR / "lightgbm_suhii_night.txt"

# The city the deployed quantile models were actually trained on.
NATIVE_MODEL_CITY = "nagpur"

# Per-city source tables for original (pre-intervention) feature values.
MASTER_PARQUETS = {
    "nagpur": Path("data/tables/nagpur_master_2024.parquet"),
    "pune": Path("data/tables/pune_feature_matrix.parquet"),
}

FEATURES = ["frac_built", "frac_tree", "frac_water", "frac_crop", "frac_grass"]

# Cost rates (₹). USER-OVERRIDABLE per PRD FR-43.
# NOTE: "cool_roof_per_m2" is kept here for future use once an
# albedo-aware action is implemented on the v2 model. It is NOT
# currently wired to any action in _apply_intervention() or
# _estimate_cost() below — do not assume it is active.
COST_RATES = {
    "tree_canopy_per_tree": 800,           # ₹ per tree
    "trees_per_hectare": 100,              # planting density
    "cool_roof_per_m2": 150,               # ₹ per m² (RESERVED, unused — see note above)
    "water_body_per_hectare": 1_500_000,   # ₹ per hectare
}

CELL_AREA_HA = 100  # 1km × 1km = 100 hectares


# ---------------------------------------------------------------------------
# Model loading (cached)
# ---------------------------------------------------------------------------

_models_cache = None

def _load_models():
    global _models_cache
    if _models_cache is not None:
        return _models_cache

    if MODEL_P50.exists() and MODEL_P10.exists() and MODEL_P90.exists():
        _models_cache = {
            "p10": lgb.Booster(model_file=str(MODEL_P10)),
            "p50": lgb.Booster(model_file=str(MODEL_P50)),
            "p90": lgb.Booster(model_file=str(MODEL_P90)),
            "has_uncertainty": True,
        }
    elif FALLBACK_MODEL.exists():
        single = lgb.Booster(model_file=str(FALLBACK_MODEL))
        _models_cache = {
            "p10": single,
            "p50": single,
            "p90": single,
            "has_uncertainty": False,
        }
    else:
        raise FileNotFoundError(
            "No trained model found. Run:\n"
            "  python -m models.gbm.train_blocked\n"
            "  python -m models.gbm.train_quantile"
        )
    return _models_cache


def _load_master(city_id: str) -> pd.DataFrame:
    """
    Load the per-cell feature table for a given city, returning a
    DataFrame with at least: cell_id, suhii_night, and all FEATURES.

    Raises FileNotFoundError if the city has no scenario-capable data
    at all (e.g. Mumbai, Aurangabad — listed in config but not ingested).
    """
    city = city_id.lower()

    if city not in MASTER_PARQUETS:
        raise FileNotFoundError(
            f"No scenario data configured for city '{city_id}'. "
            f"Supported: {list(MASTER_PARQUETS.keys())}"
        )

    path = MASTER_PARQUETS[city]
    if not path.exists():
        raise FileNotFoundError(
            f"Scenario data file missing for '{city_id}': {path}. "
            f"Has the ingestion pipeline been run for this city?"
        )

    df = pd.read_parquet(path)

    if city == "nagpur":
        return df

    if city == "pune":
        # Pune's feature matrix is multi-year/multi-month; snapshot to
        # May 2024 to match Nagpur's single-snapshot convention.
        snap = df[(df["year"] == 2024) & (df["month"] == 5)]
        if snap.empty:
            snap = (
                df.sort_values(["year", "month"])
                .groupby("cell_id", as_index=False)
                .tail(1)
            )
        return snap

    return df


# ---------------------------------------------------------------------------
# Feature mutation logic (what each intervention does)
# ---------------------------------------------------------------------------

def _apply_intervention(
    features: pd.Series,
    action: Literal["add_trees", "add_concrete", "restore_water"],
    area_pct_change: float,
) -> pd.Series:
    """
    Return a modified feature vector reflecting the intervention.

    Only three actions are supported — see module docstring for why
    "cool_roofs" and other albedo-based levers are not here.
    """
    delta = area_pct_change / 100.0

    new_features = features.copy()

    if action == "add_trees":
        built_available = min(delta, new_features["frac_built"])
        new_features["frac_tree"] += built_available
        new_features["frac_built"] -= built_available

    elif action == "add_concrete":
        tree_available = min(delta, new_features["frac_tree"])
        new_features["frac_built"] += tree_available
        new_features["frac_tree"] -= tree_available

    elif action == "restore_water":
        built_available = min(delta, new_features["frac_built"])
        new_features["frac_water"] += built_available
        new_features["frac_built"] -= built_available

    else:
        raise ValueError(f"Unknown action: {action}")

    for f in FEATURES:
        new_features[f] = max(0.0, min(1.0, new_features[f]))

    return new_features


def _estimate_cost(
    action: str,
    area_pct_change: float,
    cost_overrides: dict | None = None,
) -> int:
    """Return estimated cost in INR."""
    rates = {**COST_RATES, **(cost_overrides or {})}
    area_ha = CELL_AREA_HA * (area_pct_change / 100.0)

    if action == "add_trees":
        n_trees = area_ha * rates["trees_per_hectare"]
        return int(n_trees * rates["tree_canopy_per_tree"])
    elif action == "add_concrete":
        return 0  # private development, no municipal cost
    elif action == "restore_water":
        return int(area_ha * rates["water_body_per_hectare"])
    else:
        return 0


def _format_cost_inr(cost: int) -> str:
    """Format INR with Indian conventions (Lakh, Crore)."""
    if cost >= 1_00_00_000:
        return f"₹{cost/1_00_00_000:.2f} Crore"
    elif cost >= 1_00_000:
        return f"₹{cost/1_00_000:.2f} Lakh"
    elif cost > 0:
        return f"₹{cost:,}"
    else:
        return "₹0 (private cost)"


# ---------------------------------------------------------------------------
# Main API
# ---------------------------------------------------------------------------

def simulate_intervention(
    cell_id: str,
    action: Literal["add_trees", "add_concrete", "restore_water"],
    area_pct_change: float,
    city_id: str = "nagpur",
    cost_overrides: dict | None = None,
) -> dict:
    """
    Simulate a land-use intervention on a cell in the given city.
    Returns temperature change, cost, uncertainty range, domain warning,
    and an explicit cross-city-model flag when the model's native
    training city differs from the requested city.
    """
    models = _load_models()
    master = _load_master(city_id)

    matches = master[master["cell_id"].astype(str).str.upper() == str(cell_id).upper()]
    if len(matches) == 0:
        raise ValueError(f"Cell '{cell_id}' not found for city '{city_id}'")
    original_features = matches.iloc[0][FEATURES]

    new_features = _apply_intervention(original_features, action, area_pct_change)

    X_original = original_features.values.reshape(1, -1)
    X_new = new_features.values.reshape(1, -1)

    original_pred = {
        "p10": float(models["p10"].predict(X_original)[0]),
        "p50": float(models["p50"].predict(X_original)[0]),
        "p90": float(models["p90"].predict(X_original)[0]),
    }
    new_pred = {
        "p10": float(models["p10"].predict(X_new)[0]),
        "p50": float(models["p50"].predict(X_new)[0]),
        "p90": float(models["p90"].predict(X_new)[0]),
    }

    delta_T = {
        "p10": round(new_pred["p10"] - original_pred["p10"], 3),
        "p50": round(new_pred["p50"] - original_pred["p50"], 3),
        "p90": round(new_pred["p90"] - original_pred["p90"], 3),
    }

    for d in [original_pred, new_pred]:
        for k in d:
            d[k] = round(d[k], 3)

    cost = _estimate_cost(action, area_pct_change, cost_overrides)
    domain_check = check_domain(new_features.to_dict())

    is_cross_city = city_id.lower() != NATIVE_MODEL_CITY

    return {
        "cell_id": cell_id,
        "city_id": city_id.lower(),
        "action": action,
        "applied_change_pct": round(area_pct_change, 1),
        "original_suhii_night": original_pred,
        "new_suhii_night": new_pred,
        "delta_T_degC": delta_T,
        "estimated_cost_inr": cost,
        "cost_formatted": _format_cost_inr(cost),
        "has_uncertainty": models["has_uncertainty"],
        "extrapolation_warning": domain_check["extrapolation_warning"],
        "confidence": domain_check["confidence"],
        "domain_verdict": domain_check["verdict"],
        "cross_city_model": is_cross_city,
        "model_source_city": NATIVE_MODEL_CITY,
    }


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 65)
    print("  🎨 Scenario Engine Self-Test (WITH UNCERTAINTY & DOMAIN GUARD)")
    print("=" * 65)

    suhii = pd.read_parquet("data/tables/nagpur_suhii_2024.parquet")
    hottest = suhii.sort_values("suhii_night", ascending=False).iloc[0]
    test_cell = hottest["cell_id"]
    print(f"\nUsing hottest Nagpur cell: {test_cell} "
          f"(observed SUHII_night = {hottest['suhii_night']:.2f}°C)")

    for action, pct in [("add_trees", 20.0), ("restore_water", 10.0),
                        ("add_concrete", 30.0), ("restore_water", 90.0)]:
        print(f"\n--- Nagpur scenario: {action} ({pct}%) ---")
        result = simulate_intervention(test_cell, action, pct, city_id="nagpur")
        print(f"  ΔT: P50={result['delta_T_degC']['p50']:+.2f}°C "
              f"(range: {result['delta_T_degC']['p10']:+.2f} to {result['delta_T_degC']['p90']:+.2f})")
        print(f"  Cost: {result['cost_formatted']}")
        print(f"  Domain: {result['domain_verdict']}")
        print(f"  Cross-city model: {result['cross_city_model']}")

    print("\n--- Cross-city test: Nagpur model applied to a Pune cell ---")
    pune_df = pd.read_parquet("data/tables/pune_feature_matrix.parquet")
    pune_cell = pune_df["cell_id"].iloc[0]
    result = simulate_intervention(pune_cell, "add_trees", 20.0, city_id="pune")
    print(f"  Cell: {pune_cell}")
    print(f"  ΔT: P50={result['delta_T_degC']['p50']:+.2f}°C")
    print(f"  Cross-city model: {result['cross_city_model']} (should be True)")
    print(f"  Domain: {result['domain_verdict']}")

    print("\n✅ Self-test complete")
