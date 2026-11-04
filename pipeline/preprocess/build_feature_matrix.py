"""
Feature matrix assembly — merges all data sources into a single
training-ready Parquet file with ~18 features per pixel-month.

Sources merged:
  1. SUHII (multi-year, weather-normalized) — target variable
  2. Land cover fractions (WorldCover 2021) — 5 features
  3. Sentinel-2 indices (May 2024) — 4 features
  4. GHSL height + VIIRS (static) — 4 features
  5. ERA5 weather anomalies (multi-year) — 6 features
  6. Temporal context — 1 feature (month)

Output: data/tables/nagpur_feature_matrix.parquet
"""

import pandas as pd
import numpy as np
from pathlib import Path
import lightgbm as lgb
from sklearn.model_selection import GroupKFold
import json
import warnings

warnings.filterwarnings("ignore")

DATA_DIR = Path("data/tables")
MODEL_DIR = Path("models/registry")
MODEL_DIR.mkdir(parents=True, exist_ok=True)


def load_and_merge():
    """Load all data sources and merge cleanly without duplicate columns."""
    print("\n[1/5] Loading data sources...")

    # 1. SUHII (weather-normalized, multi-year)
    suhii_path = DATA_DIR / "nagpur_suhii_weather_normalized.parquet"
    df = pd.read_parquet(suhii_path)
    print(f"  ✓ Base table (SUHII + Weather): {len(df)} rows, {df['cell_id'].nunique()} cells")

    # 2. Check if land cover is already present in df; if not, merge from master
    lc_cols = ["frac_built", "frac_tree", "frac_water", "frac_crop", "frac_grass", "frac_bare"]
    has_lc = all(c in df.columns for c in lc_cols)
    
    if not has_lc:
        lc_path = DATA_DIR / "nagpur_master_2024.parquet"
        if lc_path.exists():
            df_lc = pd.read_parquet(lc_path)
            cols_to_add = ["cell_id"] + [c for c in lc_cols if c in df_lc.columns and c not in df.columns]
            df = df.merge(df_lc[cols_to_add], on="cell_id", how="left")
            print(f"  ✓ Merged land cover: {len(cols_to_add)-1} features")
    else:
        print(f"  ✓ Land cover already present in base table: {len(lc_cols)} features")

    # 3. Sentinel-2 indices
    s2_path = DATA_DIR / "nagpur_sentinel2_indices.parquet"
    if s2_path.exists():
        df_s2 = pd.read_parquet(s2_path)
        s2_cols = ["cell_id", "ndvi", "ndbi", "mndwi", "albedo"]
        cols_to_add = ["cell_id"] + [c for c in s2_cols if c in df_s2.columns and c not in df.columns]
        df = df.merge(df_s2[cols_to_add], on="cell_id", how="left")
        print(f"  ✓ Merged Sentinel-2: {len(cols_to_add)-1} indices")
    else:
        print("  ⚠ Sentinel-2 not found — skipping")

    # 4. GHSL + VIIRS
    gv_path = DATA_DIR / "nagpur_ghsl_viirs.parquet"
    if gv_path.exists():
        df_gv = pd.read_parquet(gv_path)
        gv_cols = ["cell_id", "building_height_mean", "night_lights_mean", "svf_proxy", "height_to_width_ratio"]
        cols_to_add = ["cell_id"] + [c for c in gv_cols if c in df_gv.columns and c not in df.columns]
        df = df.merge(df_gv[cols_to_add], on="cell_id", how="left")
        print(f"  ✓ Merged GHSL+VIIRS: {len(cols_to_add)-1} features")
    else:
        print("  ⚠ GHSL+VIIRS not found — skipping")

    # Ensure month and year are int
    df["month"] = df["month"].astype(int)
    df["year"] = df["year"].astype(int)

    print(f"  ✓ Merged table: {len(df)} rows × {len(df.columns)} columns")
    return df


def define_features_and_targets(df):
    """Define the feature list, monotone constraints, and targets."""
    print("\n[3/5] Defining features and targets...")

    # Group 1: Land cover
    lc_features = [f for f in ["frac_built", "frac_tree", "frac_water", "frac_crop", "frac_grass"] if f in df.columns]

    # Group 2: Spectral indices
    spectral_features = [f for f in ["ndvi", "ndbi", "mndwi", "albedo"] if f in df.columns]

    # Group 3: Morphology
    morph_features = [f for f in ["building_height_mean", "svf_proxy", "night_lights_mean"] if f in df.columns]

    # Group 4: Weather anomalies
    weather_features = [f for f in [
        "era5_t2m_c_anomaly", "era5_dewpoint_depression_anomaly",
        "era5_wind_speed_anomaly", "era5_precip_mm_anomaly",
        "era5_solar_mj_anomaly", "era5_soil_moist_anomaly"
    ] if f in df.columns]

    # Group 5: Temporal
    temporal_features = ["month"]

    all_features = lc_features + spectral_features + morph_features + weather_features + temporal_features

    print(f"  Total features ({len(all_features)}):")
    print(f"    Land cover:  {lc_features}")
    print(f"    Spectral:    {spectral_features}")
    print(f"    Morphology:  {morph_features}")
    print(f"    Weather:     {weather_features}")
    print(f"    Temporal:    {temporal_features}")

    # Monotone mapping (+1 = heats, -1 = cools, 0 = unconstrained)
    monotone_map = {
        "frac_built": +1,
        "frac_tree": -1,
        "frac_water": -1,
        "frac_crop": 0,
        "frac_grass": -1,
        "ndvi": -1,
        "ndbi": +1,
        "mndwi": -1,
        "albedo": -1,
        "building_height_mean": +1,
        "svf_proxy": -1,
        "night_lights_mean": +1,
    }

    monotone_constraints = [monotone_map.get(f, 0) for f in all_features]

    print(f"\n  Monotone constraints:")
    for f, c in zip(all_features, monotone_constraints):
        direction = {+1: "→ hotter", -1: "→ cooler", 0: "free"}[c]
        print(f"    {f:<32} {direction}")

    target_day = "suhii_day_normalized" if "suhii_day_normalized" in df.columns else "suhii_day"
    target_night = "suhii_night_normalized" if "suhii_night_normalized" in df.columns else "suhii_night"

    print(f"\n  Targets: {target_day}, {target_night}")

    return all_features, monotone_constraints, target_day, target_night


def train_model(df, features, monotone_constraints, target, model_name):
    """Train LightGBM with spatial block CV and report honest metrics."""
    print(f"\n  Training {model_name} (target: {target})...")

    df_clean = df.dropna(subset=features + [target]).copy()
    print(f"    Clean rows: {len(df_clean)} / {len(df)}")

    if len(df_clean) < 100:
        print(f"    ⚠ Too few rows for reliable training")
        return None, {}

    X = df_clean[features].values
    y = df_clean[target].values

    # Spatial blocking: group by cell_id to ensure a cell's entire time-series
    # is strictly held out in the validation split (prevents memorization)
    cell_groups = df_clean["cell_id"].astype("category").cat.codes.values

    # 5 spatial folds
    gkf = GroupKFold(n_splits=5)
    cv_maes = []
    cv_r2s = []

    for fold, (train_idx, val_idx) in enumerate(gkf.split(X, y, groups=cell_groups)):
        m = lgb.LGBMRegressor(
            n_estimators=500,
            learning_rate=0.03,
            num_leaves=31,
            max_depth=6,
            min_child_samples=30,
            feature_fraction=0.8,
            bagging_fraction=0.8,
            bagging_freq=5,
            monotone_constraints=monotone_constraints,
            random_state=42,
            verbose=-1,
        )
        m.fit(
            X[train_idx], y[train_idx],
            eval_set=[(X[val_idx], y[val_idx])],
            callbacks=[lgb.early_stopping(30, verbose=False)],
        )
        pred = m.predict(X[val_idx])
        mae = np.mean(np.abs(y[val_idx] - pred))
        ss_res = np.sum((y[val_idx] - pred) ** 2)
        ss_tot = np.sum((y[val_idx] - np.mean(y[val_idx])) ** 2)
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0
        cv_maes.append(mae)
        cv_r2s.append(r2)

    mean_mae = float(np.mean(cv_maes))
    std_mae = float(np.std(cv_maes))
    mean_r2 = float(np.mean(cv_r2s))

    print(f"    Spatial CV MAE: {mean_mae:.3f} ± {std_mae:.3f} °C")
    print(f"    Spatial CV R²:  {mean_r2:.3f}")

    # Null hypothesis test (shuffled targets)
    m_null = lgb.LGBMRegressor(
        n_estimators=100, learning_rate=0.05,
        num_leaves=15, random_state=42, verbose=-1,
    )
    shuffled_idx = np.random.permutation(len(y))
    m_null.fit(X[:1000], y[shuffled_idx][:1000])
    null_pred = m_null.predict(X[1000:2000] if len(X) > 2000 else X[:500])
    null_y = y[1000:2000] if len(y) > 2000 else y[:500]
    null_mae = float(np.mean(np.abs(null_y - null_pred)))
    leakage = bool(null_mae < mean_mae * 1.15)
    print(f"    Null test MAE:  {null_mae:.3f} °C {'⚠ LEAKAGE' if leakage else '✅ No leakage'}")

    # Train final champion model on full dataset
    final_model = lgb.LGBMRegressor(
        n_estimators=500,
        learning_rate=0.03,
        num_leaves=31,
        max_depth=6,
        min_child_samples=30,
        feature_fraction=0.8,
        bagging_fraction=0.8,
        bagging_freq=5,
        monotone_constraints=monotone_constraints,
        random_state=42,
        verbose=-1,
    )
    final_model.fit(X, y)

    # Feature importance
    importance = dict(zip(features, final_model.feature_importances_))
    top5 = sorted(importance.items(), key=lambda x: -x[1])[:5]
    print(f"    Top 5 features:")
    for f, imp in top5:
        print(f"      {f:<32} {imp}")

    # Save model binary
    model_path = MODEL_DIR / f"{model_name}.txt"
    final_model.booster_.save_model(str(model_path))
    print(f"    ✓ Saved to {model_path}")

    metrics = {
        "target": target,
        "n_features": len(features),
        "features": features,
        "n_training_rows": len(df_clean),
        "spatial_cv_mae": round(mean_mae, 4),
        "spatial_cv_mae_std": round(std_mae, 4),
        "spatial_cv_r2": round(mean_r2, 4),
        "null_test_mae": round(null_mae, 4),
        "leakage_detected": leakage,
        "monotone_constraints": dict(zip(features, monotone_constraints)),
        "top5_features": {f: int(v) for f, v in top5},
    }

    return final_model, metrics


def main():
    print("=" * 65)
    print("  FEATURE MATRIX ASSEMBLY + MODEL RETRAIN (v2)")
    print("  Expanding from 5 → ~18 features")
    print("=" * 65)

    df = load_and_merge()
    features, monotone, target_day, target_night = define_features_and_targets(df)

    print("\n[4/5] Saving feature matrix...")
    matrix_path = DATA_DIR / "nagpur_feature_matrix.parquet"
    df.to_parquet(matrix_path, index=False)
    print(f"  ✓ Saved {len(df)} rows × {len(df.columns)} cols to {matrix_path}")

    print("\n[5/5] Training expanded models...")

    _, metrics_night = train_model(
        df, features, monotone, target_night, "lightgbm_suhii_night_v2"
    )

    _, metrics_day = train_model(
        df, features, monotone, target_day, "lightgbm_suhii_day_v2"
    )

    print("\n" + "=" * 65)
    print("  MODEL COMPARISON")
    print("=" * 65)

    if metrics_night:
        print(f"  New M2 Night ({metrics_night['n_features']} features):")
        print(f"    Spatial CV MAE: {metrics_night['spatial_cv_mae']:.3f} ± {metrics_night['spatial_cv_mae_std']:.3f} °C")
        print(f"    Spatial CV R²:  {metrics_night['spatial_cv_r2']:.3f}")

    # Save updated model card
    card = {
        "model": "LightGBM v2 (expanded features)",
        "version": "v2",
        "features_count": len(features),
        "features": features,
        "night": metrics_night,
        "day": metrics_day,
        "data": {
            "city": "Nagpur",
            "years": sorted(df["year"].unique().tolist()),
            "months": sorted(df["month"].unique().tolist()),
            "n_cells": int(df["cell_id"].nunique()),
            "n_rows": len(df),
        },
        "monotone_constraints_applied": True,
        "weather_normalized": "suhii_night_normalized" in df.columns,
    }

    card_path = MODEL_DIR / "CARD_v2.json"
    with open(card_path, "w") as f:
        json.dump(card, f, indent=2, default=str)
    print(f"\n  ✓ Model card saved to {card_path}")
    print("=" * 65)


if __name__ == "__main__":
    main()
