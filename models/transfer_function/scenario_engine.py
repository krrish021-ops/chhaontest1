"""
Scenario Simulation Engine — WITH UNCERTAINTY BANDS & DOMAIN GUARD (v3).

Every prediction now returns:
  - Uncertainty bands (P10, P50, P90)
  - Extrapolation warnings (Mahalanobis distance domain check)

This lets the frontend show: "-1.15°C (range: -0.6 to -1.7°C)"
AND warn the user if they painted an unrealistic scenario (e.g. 100% water).
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

MASTER_PARQUET = Path("data/tables/nagpur_master_2024.parquet")

FEATURES = ["frac_built", "frac_tree", "frac_water", "frac_crop", "frac_grass"]

# Cost rates (₹). USER-OVERRIDABLE per PRD FR-43.
COST_RATES = {
    "tree_canopy_per_tree": 800,           # ₹ per tree
    "trees_per_hectare": 100,              # planting density
    "cool_roof_per_m2": 150,               # ₹ per m²
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

    # Try to load quantile models
    if MODEL_P50.exists() and MODEL_P10.exists() and MODEL_P90.exists():
        _models_cache = {
            "p10": lgb.Booster(model_file=str(MODEL_P10)),
            "p50": lgb.Booster(model_file=str(MODEL_P50)),
            "p90": lgb.Booster(model_file=str(MODEL_P90)),
            "has_uncertainty": True,
        }
    elif FALLBACK_MODEL.exists():
        # Fallback to single model
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


def _load_master() -> pd.DataFrame:
    return pd.read_parquet(MASTER_PARQUET)


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
    """
    delta = area_pct_change / 100.0  # convert to fraction

    new_features = features.copy()

    if action == "add_trees":
        # Convert built land into tree canopy
        built_available = min(delta, new_features["frac_built"])
        new_features["frac_tree"] += built_available
        new_features["frac_built"] -= built_available

    elif action == "add_concrete":
        # Convert tree land into built
        tree_available = min(delta, new_features["frac_tree"])
        new_features["frac_built"] += tree_available
        new_features["frac_tree"] -= tree_available

    elif action == "restore_water":
        # Convert built land into water
        built_available = min(delta, new_features["frac_built"])
        new_features["frac_water"] += built_available
        new_features["frac_built"] -= built_available

    else:
        raise ValueError(f"Unknown action: {action}")

    # Clip to [0, 1]
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
    cost_overrides: dict | None = None,
) -> dict:
    """
    Simulate a land-use intervention on a cell. Returns temperature change,
    cost, uncertainty range, and domain warning.
    """
    models = _load_models()
    master = _load_master()

    # Find the cell
    matches = master[master["cell_id"] == cell_id]
    if len(matches) == 0:
        raise ValueError(f"Cell {cell_id} not found in {MASTER_PARQUET}")
    original_features = matches.iloc[0][FEATURES]

    # Apply intervention
    new_features = _apply_intervention(
        original_features, action, area_pct_change
    )

    # Predict with all three quantile models
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

    # Round all quantile predictions
    for d in [original_pred, new_pred]:
        for k in d:
            d[k] = round(d[k], 3)

    # Cost estimation
    cost = _estimate_cost(action, area_pct_change, cost_overrides)

    # Check if the new feature vector is inside training distribution
    domain_check = check_domain(new_features.to_dict())

    return {
        "cell_id": cell_id,
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
    }


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 65)
    print("  🎨 Scenario Engine Self-Test (WITH UNCERTAINTY & DOMAIN GUARD)")
    print("=" * 65)

    # Find hottest cell to use as test
    suhii = pd.read_parquet("data/tables/nagpur_suhii_2024.parquet")
    hottest = suhii.sort_values("suhii_night", ascending=False).iloc[0]
    test_cell = hottest["cell_id"]
    print(f"\nUsing hottest cell: {test_cell} "
          f"(observed SUHII_night = {hottest['suhii_night']:.2f}°C)")

    scenarios = [
        ("add_trees", 20.0),
        ("restore_water", 10.0),
        ("add_concrete", 30.0),
        ("restore_water", 90.0), # This should trigger the warning!
    ]

    for action, pct in scenarios:
        print(f"\n--- Scenario: {action} ({pct}%) ---")
        result = simulate_intervention(test_cell, action, pct)

        print(f"  ΔT:                   "
              f"P50={result['delta_T_degC']['p50']:+.2f}°C  "
              f"(range: {result['delta_T_degC']['p10']:+.2f} to "
              f"{result['delta_T_degC']['p90']:+.2f})")
        print(f"  Cost:                 {result['cost_formatted']}")
        print(f"  Domain Status:        {result['domain_verdict']}")
        if result['extrapolation_warning']:
            print(f"  🚨 WARNING TRIGGERED 🚨")

    print("\n✅ Self-test complete")
