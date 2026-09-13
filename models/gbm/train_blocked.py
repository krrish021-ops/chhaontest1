"""
Retrain M2 (LightGBM) with BLOCKED cross-validation.

REPLACES the old KFold-based validation in models/gbm/train.py.
Reports honest MAE per spatial fold and runs the null-hypothesis test.
"""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.metrics import mean_absolute_error, r2_score

from models.cv.blocked_split import (
    spatial_block_split,
    null_hypothesis_test,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MASTER_PARQUET = Path("data/tables/nagpur_master_2024.parquet")
SUHII_PARQUET = Path("data/tables/nagpur_suhii_2024.parquet")
REGISTRY_DIR = Path("models/registry")
REGISTRY_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = REGISTRY_DIR / "lightgbm_suhii_night.txt"
CARD_PATH = REGISTRY_DIR / "CARD.json"

FEATURES = ["frac_built", "frac_tree", "frac_water", "frac_crop", "frac_grass"]
TARGET = "suhii_night"

# Monotone constraints (physics rules) — order MUST match FEATURES
MONOTONE = [+1, -1, -1, 0, -1]

MODEL_PARAMS = {
    "n_estimators": 300,
    "learning_rate": 0.03,
    "num_leaves": 15,
    "monotone_constraints": MONOTONE,
    "random_state": 42,
    "verbosity": -1,
}


def load_data() -> pd.DataFrame:
    """Merge master features with SUHII target."""
    print(f"📂 Loading data...")
    master = pd.read_parquet(MASTER_PARQUET)
    suhii = pd.read_parquet(SUHII_PARQUET)

    df = master.merge(
        suhii[["cell_id", "suhii_day", "suhii_night"]],
        on="cell_id",
        how="inner",
    )
    print(f"   Loaded {len(df):,} rows × {len(df.columns)} columns")
    return df


def run_blocked_cv(df: pd.DataFrame) -> dict:
    """Run spatial blocked CV and return per-fold metrics."""
    print(f"\n🧪 Running spatial blocked CV (5 folds)...")

    fold_metrics = []
    for fold_id, train_df, test_df in spatial_block_split(df, n_blocks=5):
        if len(test_df) < 5:
            print(f"   ⚠️  {fold_id}: too few test rows ({len(test_df)}), skipping")
            continue

        X_train, y_train = train_df[FEATURES].values, train_df[TARGET].values
        X_test, y_test = test_df[FEATURES].values, test_df[TARGET].values

        model = lgb.LGBMRegressor(**MODEL_PARAMS)
        model.fit(X_train, y_train)
        preds = model.predict(X_test)

        mae = float(mean_absolute_error(y_test, preds))
        r2 = float(r2_score(y_test, preds)) if len(y_test) > 1 else float("nan")

        fold_metrics.append({
            "fold": fold_id,
            "n_train": len(train_df),
            "n_test": len(test_df),
            "mae_c": round(mae, 3),
            "r2": round(r2, 3) if not np.isnan(r2) else None,
        })
        print(
            f"   {fold_id}: train={len(train_df):3d}  test={len(test_df):3d}  "
            f"MAE={mae:.3f}°C  R²={r2:.3f}"
        )

    valid_maes = [f["mae_c"] for f in fold_metrics]
    return {
        "folds": fold_metrics,
        "mean_mae_c": round(float(np.mean(valid_maes)), 3),
        "std_mae_c": round(float(np.std(valid_maes)), 3),
        "n_folds": len(fold_metrics),
    }


def train_final_model(df: pd.DataFrame) -> lgb.LGBMRegressor:
    """Train the final production model on ALL data."""
    print(f"\n🏗️  Training final production model on ALL {len(df):,} rows...")
    X, y = df[FEATURES].values, df[TARGET].values
    model = lgb.LGBMRegressor(**MODEL_PARAMS)
    model.fit(X, y)
    train_mae = float(mean_absolute_error(y, model.predict(X)))
    print(f"   In-sample MAE: {train_mae:.3f}°C  (this is optimistic — see CV MAE)")
    return model, train_mae


def run_null_test(df: pd.DataFrame) -> dict:
    """Leakage detection."""
    print(f"\n🎲 Running null-hypothesis test...")
    result = null_hypothesis_test(
        df,
        feature_cols=FEATURES,
        target_col=TARGET,
        model_params=MODEL_PARAMS,
        n_shuffles=3,
    )
    print(f"   Real MAE:        {result['real_mae']:.3f} °C")
    print(f"   Shuffled MAE:    {result['shuffled_mae_mean']:.3f} °C")
    print(f"   Climatology MAE: {result['climatology_mae']:.3f} °C")
    print(f"   Leakage ratio:   {result['leakage_ratio']:.2%}")
    print(f"   {result['verdict']}")
    return result


def save_model_card(cv_metrics: dict, null_result: dict, train_mae: float, n_rows: int):
    """Update CARD.json with honest metrics."""
    card = {
        "model_id": "lightgbm_suhii_night_v2",
        "model_family": "LightGBM Gradient Boosting",
        "target": TARGET,
        "target_unit": "degrees Celsius",
        "target_description": "Nighttime Surface Urban Heat Island Intensity",
        "features": FEATURES,
        "monotone_constraints": dict(zip(FEATURES, MONOTONE)),
        "training_data": {
            "source": str(MASTER_PARQUET),
            "n_rows": n_rows,
            "cities": ["nagpur"],
            "time_period": "May 2024 (single month)",
        },
        "validation": {
            "method": "spatial_blocked_cv",
            "n_folds": cv_metrics["n_folds"],
            "cv_mae_mean_c": cv_metrics["mean_mae_c"],
            "cv_mae_std_c": cv_metrics["std_mae_c"],
            "in_sample_mae_c": round(train_mae, 3),
            "per_fold": cv_metrics["folds"],
            "note": (
                "In-sample MAE is optimistic. Trust the CV MAE. "
                "Small dataset (229 rows, 1 month) means these numbers "
                "will change substantially when we scale to multi-year, multi-city."
            ),
        },
        "leakage_test": {
            "real_mae_c": round(null_result["real_mae"], 3),
            "shuffled_mae_c": round(null_result["shuffled_mae_mean"], 3),
            "climatology_mae_c": round(null_result["climatology_mae"], 3),
            "leakage_ratio": round(null_result["leakage_ratio"], 3),
            "verdict": null_result["verdict"],
        },
        "hyperparameters": {
            k: v for k, v in MODEL_PARAMS.items() if k != "monotone_constraints"
        },
        "known_limitations": [
            "Trained on only 229 cells × 1 month × 1 city (see Gap #1 in docs)",
            "No uncertainty bands yet (see Set 2 — coming next)",
            "No weather normalization (see Set 3 — coming next)",
            "Sprawl forecast uses flat growth rates, not cellular automaton",
        ],
        "trained_at": datetime.utcnow().isoformat() + "Z",
        "trained_by": "models/gbm/train_blocked.py",
    }

    with open(CARD_PATH, "w") as f:
        json.dump(card, f, indent=2)
    print(f"\n📇 Model card saved: {CARD_PATH}")


def main():
    print("=" * 65)
    print("  🏗️  M2 LightGBM Training with BLOCKED CV")
    print("=" * 65)

    df = load_data()

    # Honest validation
    cv_metrics = run_blocked_cv(df)

    # Leakage detection
    null_result = run_null_test(df)

    # Train final production model on all data
    model, train_mae = train_final_model(df)
    model.booster_.save_model(str(MODEL_PATH))
    print(f"\n💾 Model saved: {MODEL_PATH}")

    # Update model card
    save_model_card(cv_metrics, null_result, train_mae, len(df))

    # Summary
    print("\n" + "=" * 65)
    print("  📊 HONEST VALIDATION SUMMARY")
    print("=" * 65)
    print(f"  Spatial CV MAE:  {cv_metrics['mean_mae_c']:.3f} ± "
          f"{cv_metrics['std_mae_c']:.3f} °C")
    print(f"  In-sample MAE:   {train_mae:.3f} °C  (optimistic)")
    print(f"  Leakage test:    {null_result['verdict']}")
    print("=" * 65)


if __name__ == "__main__":
    main()

