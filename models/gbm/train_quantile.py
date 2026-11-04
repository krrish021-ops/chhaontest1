"""
Train QUANTILE LightGBM models for uncertainty bands.

TRD FR-32: Every forecast MUST show uncertainty.
PRD: "No forecast ever shown as a single bare number."

Trains three models:
  - P10 (low estimate  — "best case")
  - P50 (median        — "most likely")
  - P90 (high estimate — "worst case")

Note: LightGBM does not support monotone_constraints with objective='quantile',
so monotone_constraints are omitted for these quantile models while keeping
the hyperparameter structure identical to M2.
"""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.metrics import mean_absolute_error

from models.cv.blocked_split import spatial_block_split

# ---------------------------------------------------------------------------
MASTER_PARQUET = Path("data/tables/nagpur_master_2024.parquet")
SUHII_PARQUET = Path("data/tables/nagpur_suhii_2024.parquet")
REGISTRY_DIR = Path("models/registry")

FEATURES = ["frac_built", "frac_tree", "frac_water", "frac_crop", "frac_grass"]
TARGET = "suhii_night"

QUANTILES = [0.10, 0.50, 0.90]

# Note: monotone_constraints omitted because LightGBM quantile objective doesn't support them
BASE_PARAMS = {
    "n_estimators": 300,
    "learning_rate": 0.03,
    "num_leaves": 15,
    "random_state": 42,
    "verbosity": -1,
}


def load_data() -> pd.DataFrame:
    master = pd.read_parquet(MASTER_PARQUET)
    suhii = pd.read_parquet(SUHII_PARQUET)
    return master.merge(
        suhii[["cell_id", "suhii_day", "suhii_night"]],
        on="cell_id", how="inner"
    )


def train_quantile_model(X, y, alpha: float) -> lgb.LGBMRegressor:
    """Train a single quantile regressor."""
    params = {
        **BASE_PARAMS,
        "objective": "quantile",
        "alpha": alpha,
    }
    model = lgb.LGBMRegressor(**params)
    model.fit(X, y)
    return model


def evaluate_calibration(df: pd.DataFrame, models: dict) -> dict:
    """
    Check calibration: does the P10-P90 band contain ~80% of truth?
    """
    print(f"\n📏 Checking calibration via spatial CV...")

    all_truths = []
    all_p10 = []
    all_p90 = []

    for fold_id, train_df, test_df in spatial_block_split(df, n_blocks=5):
        if len(test_df) < 5:
            continue

        X_train, y_train = train_df[FEATURES].values, train_df[TARGET].values
        X_test, y_test = test_df[FEATURES].values, test_df[TARGET].values

        # Train fresh quantile models on this fold's training data
        m10 = train_quantile_model(X_train, y_train, 0.10)
        m90 = train_quantile_model(X_train, y_train, 0.90)

        all_truths.extend(y_test.tolist())
        all_p10.extend(m10.predict(X_test).tolist())
        all_p90.extend(m90.predict(X_test).tolist())

    truths = np.array(all_truths)
    p10 = np.array(all_p10)
    p90 = np.array(all_p90)

    inside = (truths >= p10) & (truths <= p90)
    coverage = float(inside.mean())
    mean_width = float((p90 - p10).mean())

    if coverage > 0.75 and coverage < 0.85:
        verdict = "✅ WELL CALIBRATED — coverage near 80%"
    elif coverage > 0.85:
        verdict = "⚠️  UNDERCONFIDENT — bands too wide"
    else:
        verdict = "🚨 OVERCONFIDENT — bands too narrow"

    print(f"   Target coverage (P10-P90): 80%")
    print(f"   Actual coverage:           {coverage:.1%}")
    print(f"   Mean band width:           ±{mean_width/2:.2f}°C")
    print(f"   {verdict}")

    return {
        "target_coverage": 0.80,
        "actual_coverage": round(coverage, 3),
        "mean_band_width_c": round(mean_width, 3),
        "verdict": verdict,
    }


def main():
    print("=" * 65)
    print("  🎲 Training QUANTILE Models for Uncertainty Bands")
    print("=" * 65)

    df = load_data()
    print(f"📂 Loaded {len(df):,} rows")

    X, y = df[FEATURES].values, df[TARGET].values

    # Train all three quantile models on ALL data (production)
    models = {}
    for q in QUANTILES:
        print(f"\n🏗️  Training P{int(q*100)} model (alpha={q})...")
        model = train_quantile_model(X, y, q)
        preds = model.predict(X)
        mae = mean_absolute_error(y, preds)

        model_path = REGISTRY_DIR / f"lightgbm_suhii_night_p{int(q*100)}.txt"
        model.booster_.save_model(str(model_path))
        print(f"   In-sample MAE: {mae:.3f}°C")
        print(f"   💾 Saved: {model_path}")
        models[f"p{int(q*100)}"] = model

    # Calibration check (uses spatial CV)
    calibration = evaluate_calibration(df, models)

    # Save quantile card
    quantile_card = {
        "model_id": "lightgbm_suhii_night_quantiles_v1",
        "quantiles": {f"p{int(q*100)}": q for q in QUANTILES},
        "features": FEATURES,
        "calibration": calibration,
        "usage_example": {
            "python": (
                "import lightgbm as lgb\n"
                "p10 = lgb.Booster(model_file='models/registry/lightgbm_suhii_night_p10.txt')\n"
                "p50 = lgb.Booster(model_file='models/registry/lightgbm_suhii_night_p50.txt')\n"
                "p90 = lgb.Booster(model_file='models/registry/lightgbm_suhii_night_p90.txt')\n"
            ),
        },
        "trained_at": datetime.utcnow().isoformat() + "Z",
    }

    card_path = REGISTRY_DIR / "CARD_quantiles.json"
    with open(card_path, "w") as f:
        json.dump(quantile_card, f, indent=2)
    print(f"\n📇 Quantile card saved: {card_path}")

    print("\n" + "=" * 65)
    print("  ✅ All three quantile models trained")
    print("=" * 65)


if __name__ == "__main__":
    main()
