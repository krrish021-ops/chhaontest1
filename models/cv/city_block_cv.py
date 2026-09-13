"""
City-Block Cross-Validation (TRD §7.4 V3).

Splits:
  Fold 1: Train on Nagpur  → Test on Pune
  Fold 2: Train on Pune    → Test on Nagpur

Verifies true out-of-sample generalisation to an unseen city.
Outputs:
  models/registry/CARD_city_block.json
"""

import pandas as pd
import numpy as np
import lightgbm as lgb
from pathlib import Path
import json

DATA_DIR = Path("data/tables")
MODEL_DIR = Path("models/registry")
MODEL_DIR.mkdir(parents=True, exist_ok=True)

FEATURES = [
    "frac_built", "frac_tree", "frac_water", "frac_crop", "frac_grass",
    "ndvi", "ndbi", "mndwi", "albedo",
    "building_height_mean", "svf_proxy", "night_lights_mean",
    "era5_t2m_c_anomaly", "era5_dewpoint_depression_anomaly",
    "era5_wind_speed_anomaly", "era5_precip_mm_anomaly",
    "era5_solar_mj_anomaly", "era5_soil_moist_anomaly",
    "month"
]

MONOTONE = [+1, -1, -1, 0, -1, -1, +1, -1, -1, +1, -1, +1, 0, 0, 0, 0, 0, 0, 0]


def run_city_fold(train_df, test_df, train_name, test_name, target="suhii_night_normalized"):
    features = [f for f in FEATURES if f in train_df.columns and f in test_df.columns]
    monotone = [MONOTONE[FEATURES.index(f)] for f in features]

    tr_clean = train_df.dropna(subset=features + [target])
    te_clean = test_df.dropna(subset=features + [target])

    X_train, y_train = tr_clean[features].values, tr_clean[target].values
    X_test, y_test = te_clean[features].values, te_clean[target].values

    model = lgb.LGBMRegressor(
        n_estimators=400,
        learning_rate=0.03,
        num_leaves=31,
        min_child_samples=30,
        monotone_constraints=monotone,
        random_state=42,
        verbose=-1,
    )
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mae = float(np.mean(np.abs(y_test - preds)))
    rmse = float(np.sqrt(np.mean((y_test - preds) ** 2)))
    
    ss_res = np.sum((y_test - preds) ** 2)
    ss_tot = np.sum((y_test - np.mean(y_test)) ** 2)
    r2 = float(1 - ss_res / ss_tot if ss_tot > 0 else 0)

    print(f"\n  City-Block: Train on {train_name:<8} ({len(tr_clean)} rows) → Test on {test_name:<8} ({len(te_clean)} rows)")
    print(f"    Held-Out MAE:  {mae:.3f} °C")
    print(f"    Held-Out RMSE: {rmse:.3f} °C")
    print(f"    Held-Out R²:   {r2:.3f}")

    return {
        "train_city": train_name,
        "test_city": test_name,
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "r2": round(r2, 4),
        "test_rows": len(te_clean),
    }


def main():
    print("=" * 65)
    print("  CITY-BLOCK CROSS-VALIDATION (TRD §7.4 V3)")
    print("=" * 65)

    nagpur_path = DATA_DIR / "nagpur_feature_matrix.parquet"
    pune_path = DATA_DIR / "pune_feature_matrix.parquet"

    df_nagpur = pd.read_parquet(nagpur_path)
    df_pune = pd.read_parquet(pune_path)

    df_nagpur["city"] = "nagpur"
    df_pune["city"] = "pune"

    # Fold 1: Train Nagpur -> Test Pune
    res1 = run_city_fold(df_nagpur, df_pune, "Nagpur", "Pune")

    # Fold 2: Train Pune -> Test Nagpur
    res2 = run_city_fold(df_pune, df_nagpur, "Pune", "Nagpur")

    avg_mae = round((res1["mae"] + res2["mae"]) / 2, 4)
    avg_r2 = round((res1["r2"] + res2["r2"]) / 2, 4)

    print("\n" + "=" * 65)
    print("  SUMMARY: CITY-BLOCK GENERALISATION")
    print("=" * 65)
    print(f"  Mean Held-Out City MAE: {avg_mae:.3f} °C")
    print(f"  Mean Held-Out City R²:  {avg_r2:.3f}")

    card = {
        "protocol": "City-Block Cross-Validation (TRD §7.4 V3)",
        "folds": [res1, res2],
        "mean_held_out_mae": avg_mae,
        "mean_held_out_r2": avg_r2,
        "features": FEATURES,
        "monotone_constraints": True,
        "interpretation": "Evaluates model on cities it has never seen during training.",
    }

    out_file = MODEL_DIR / "CARD_city_block.json"
    with open(out_file, "w") as f:
        json.dump(card, f, indent=2)

    print(f"  ✓ Saved results to {out_file}")
    print("=" * 65)


if __name__ == "__main__":
    main()
