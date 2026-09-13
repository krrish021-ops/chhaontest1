"""
ERA5-based weather normalization of SUHII.

Method (TRD §4.6):
  1. Merge SUHII with ERA5 weather features on (cell_id, year, month)
  2. Identify "rural-like" cells (frac_built < 0.20, frac_crop+grass > 0.50)
  3. Compute weather anomalies (deviation from month-of-year mean)
  4. Train LightGBM on RURAL cells: SUHII ~ weather_anomalies
     → This learns E[SUHII | weather], the weather-driven component
  5. Predict E[SUHII | weather] for ALL cells
  6. Subtract: SUHII_normalized = SUHII − E[SUHII | weather]
     → What remains is the urban-form signal, purged of heatwave effects

Outputs:
  data/tables/nagpur_suhii_weather_normalized.parquet
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


def compute_weather_anomalies(df_era5):
    """
    Convert absolute weather values to anomalies (deviation from the
    long-term mean for that calendar month). This removes the seasonal
    cycle so the model learns the inter-annual weather variation.

    Example: May 2023 T2m was 35.2°C, May average is 33.8°C
             → T2m anomaly = +1.4°C (unusually hot May)
    """
    df = df_era5.copy()

    weather_cols = [
        "era5_t2m_c", "era5_dewpoint_c", "era5_skin_temp_c",
        "era5_wind_speed", "era5_dewpoint_depression",
        "era5_precip_mm", "era5_solar_mj", "era5_soil_moist",
    ]

    # Compute month-of-year mean across all years
    month_means = df.groupby("month")[weather_cols].mean()

    # Subtract to get anomalies
    for col in weather_cols:
        anomaly_col = f"{col}_anomaly"
        df[anomaly_col] = df.apply(
            lambda row: row[col] - month_means.loc[row["month"], col],
            axis=1,
        )

    return df


def identify_rural_cells(df_master):
    """
    Identify rural-like grid cells for training the weather response model.
    Criteria: < 20% built-up, > 50% crop+grass combined.
    These cells have minimal urban-form signal, so their SUHII variation
    is dominated by weather — exactly what we want to model.
    """
    rural_mask = (
        (df_master["frac_built"] < 0.20)
        & ((df_master["frac_crop"] + df_master["frac_grass"]) > 0.50)
    )
    rural_cells = df_master.loc[rural_mask, "cell_id"].unique()
    return rural_cells


def train_weather_model(df_merged, rural_cells, target_col):
    """
    Train LightGBM on rural cells to learn E[SUHII | weather].
    Uses GroupKFold by year to prevent temporal leakage.
    """
    # Filter to rural cells only
    df_rural = df_merged[df_merged["cell_id"].isin(rural_cells)].copy()

    if len(df_rural) < 50:
        print(f"    ⚠ Only {len(df_rural)} rural rows — using all cells with"
              f" frac_built < 0.40 as fallback")
        df_rural = df_merged[df_merged["frac_built"] < 0.40].copy()

    # Features: weather anomalies + month (seasonal baseline)
    feature_cols = [
        "era5_t2m_c_anomaly",
        "era5_dewpoint_c_anomaly",
        "era5_skin_temp_c_anomaly",
        "era5_wind_speed_anomaly",
        "era5_dewpoint_depression_anomaly",
        "era5_precip_mm_anomaly",
        "era5_solar_mj_anomaly",
        "era5_soil_moist_anomaly",
        "month",  # captures seasonal baseline
    ]

    # Drop rows with missing features or target
    df_clean = df_rural.dropna(subset=feature_cols + [target_col])

    if len(df_clean) < 30:
        print(f"    ⚠ Too few clean rural rows ({len(df_clean)})."
              f" Returning zero-correction model.")
        return None, feature_cols

    X = df_clean[feature_cols].values
    y = df_clean[target_col].values
    groups = df_clean["year"].values

    # Train with year-blocked CV (no temporal leakage)
    model = lgb.LGBMRegressor(
        n_estimators=100,
        learning_rate=0.05,
        num_leaves=8,       # small — weather response is smooth
        max_depth=3,
        min_child_samples=10,
        random_state=42,
        verbose=-1,
    )

    # Fit on all rural data (CV is for reporting, not selection)
    model.fit(X, y)

    # Report blocked CV performance
    if len(np.unique(groups)) >= 3:
        gkf = GroupKFold(n_splits=min(3, len(np.unique(groups))))
        cv_scores = []
        for train_idx, val_idx in gkf.split(X, y, groups):
            m = lgb.LGBMRegressor(
                n_estimators=100, learning_rate=0.05,
                num_leaves=8, max_depth=3,
                min_child_samples=10, random_state=42, verbose=-1,
            )
            m.fit(X[train_idx], y[train_idx])
            pred = m.predict(X[val_idx])
            mae = np.mean(np.abs(y[val_idx] - pred))
            cv_scores.append(mae)
        print(f"    Weather model CV MAE ({target_col}):"
              f" {np.mean(cv_scores):.3f} ± {np.std(cv_scores):.3f} °C")

    # Feature importance
    importance = dict(zip(feature_cols, model.feature_importances_))
    top_features = sorted(importance.items(), key=lambda x: -x[1])[:3]
    top_str = ", ".join([f"{f} ({v})" for f, v in top_features])
    print(f"    Top weather drivers: {top_str}")

    return model, feature_cols


def main():
    print("=" * 65)
    print("  ERA5-BASED WEATHER NORMALIZATION OF SUHII")
    print("  Method: TRD §4.6 — subtract E[SUHII | weather] trained on"
          " rural cells")
    print("=" * 65)

    # ── Load data ────────────────────────────────────────────────────
    print(f"\n[1/6] Loading datasets...")

    suhii_path = DATA_DIR / "nagpur_suhii_multiyear.parquet"
    df_suhii = pd.read_parquet(suhii_path)
    print(f"  ✓ SUHII: {len(df_suhii)} rows")

    era5_path = DATA_DIR / "nagpur_era5_monthly.parquet"
    df_era5 = pd.read_parquet(era5_path)
    print(f"  ✓ ERA5: {len(df_era5)} rows")

    # Load land cover for rural cell identification
    master_path = DATA_DIR / "nagpur_master_2024.parquet"
    df_master = pd.read_parquet(master_path)
    print(f"  ✓ Master (land cover): {len(df_master)} cells")

    # ── Compute weather anomalies ────────────────────────────────────
    print(f"\n[2/6] Computing weather anomalies (deviation from"
          f" month-of-year mean)...")
    df_era5_anom = compute_weather_anomalies(df_era5)

    # Quick check: anomalies should be centered near zero
    for col in ["era5_t2m_c_anomaly", "era5_precip_mm_anomaly"]:
        mean_anom = df_era5_anom[col].mean()
        print(f"  {col}: mean = {mean_anom:+.3f} (should be ~0)")

    # ── Merge SUHII + ERA5 ──────────────────────────────────────────
    print(f"\n[3/6] Merging SUHII with ERA5 weather...")
    df_merged = df_suhii.merge(
        df_era5_anom,
        on=["cell_id", "year", "month"],
        how="left",
    )

    # Add land cover fractions (static — same for all years)
    lc_cols = ["cell_id", "frac_built", "frac_tree", "frac_water",
               "frac_crop", "frac_grass", "frac_bare"]
    available_lc = [c for c in lc_cols if c in df_master.columns]
    df_merged = df_merged.merge(
        df_master[available_lc],
        on="cell_id",
        how="left",
    )

    matched = df_merged["era5_t2m_c_anomaly"].notna().sum()
    print(f"  ✓ {matched}/{len(df_merged)} rows matched with weather data")

    # ── Identify rural cells ─────────────────────────────────────────
    print(f"\n[4/6] Identifying rural-like cells for weather model...")
    rural_cells = identify_rural_cells(df_master)
    print(f"  ✓ {len(rural_cells)} rural cells"
          f" (frac_built < 20%, crop+grass > 50%)")

    # ── Train weather models (day + night separately) ────────────────
    print(f"\n[5/6] Training weather response models...")

    print(f"\n  Day SUHII weather model:")
    model_day, features_day = train_weather_model(
        df_merged, rural_cells, "suhii_day"
    )

    print(f"\n  Night SUHII weather model:")
    model_night, features_night = train_weather_model(
        df_merged, rural_cells, "suhii_night"
    )

    # ── Apply normalization to ALL cells ─────────────────────────────
    print(f"\n[6/6] Applying weather normalization to all cells...")

    df_out = df_merged.copy()

    if model_day is not None:
        X_all_day = df_out[features_day].fillna(0).values
        weather_effect_day = model_day.predict(X_all_day)
        df_out["suhii_day_weather_effect"] = np.round(weather_effect_day, 3)
        df_out["suhii_day_normalized"] = np.round(
            df_out["suhii_day"] - weather_effect_day, 3
        )
    else:
        df_out["suhii_day_weather_effect"] = 0.0
        df_out["suhii_day_normalized"] = df_out["suhii_day"]

    if model_night is not None:
        X_all_night = df_out[features_night].fillna(0).values
        weather_effect_night = model_night.predict(X_all_night)
        df_out["suhii_night_weather_effect"] = np.round(weather_effect_night, 3)
        df_out["suhii_night_normalized"] = np.round(
            df_out["suhii_night"] - weather_effect_night, 3
        )
    else:
        df_out["suhii_night_weather_effect"] = 0.0
        df_out["suhii_night_normalized"] = df_out["suhii_night"]

    # ── Before/after comparison ──────────────────────────────────────
    print("\n" + "=" * 65)
    print("  NORMALIZATION RESULTS (before → after)")
    print("=" * 65)

    for period, day_col_raw, day_col_norm, night_col_raw, night_col_norm in [
        ("Day", "suhii_day", "suhii_day_normalized",
         "suhii_night", "suhii_night_normalized"),
    ]:
        raw_std = df_out[day_col_raw].std()
        norm_std = df_out[day_col_norm].std()
        reduction = (1 - norm_std / raw_std) * 100 if raw_std > 0 else 0
        print(f"\n  {period} SUHII:")
        print(f"    Raw variance (std):       {raw_std:.3f} °C")
        print(f"    Normalized variance (std): {norm_std:.3f} °C")
        print(f"    Weather variance removed:  {reduction:.1f}%")

    # Year-to-year stability check: normalized SUHII should be more
    # stable across years (weather spikes removed)
    print(f"\n  Year-to-year stability (night SUHII std across annual means):")
    annual_raw = (
        df_out.groupby("year")["suhii_night"].mean().std()
    )
    annual_norm = (
        df_out.groupby("year")["suhii_night_normalized"].mean().std()
    )
    print(f"    Raw annual mean std:       {annual_raw:.3f} °C")
    print(f"    Normalized annual mean std: {annual_norm:.3f} °C")
    if annual_norm < annual_raw:
        print(f"    ✓ Normalization improved inter-annual stability"
              f" ({(1-annual_norm/annual_raw)*100:.0f}% reduction)")
    else:
        print(f"    ℹ Normalization did not reduce inter-annual variance"
              f" (weather may not be the dominant driver)")

    # ── Save ─────────────────────────────────────────────────────────
    out_path = DATA_DIR / "nagpur_suhii_weather_normalized.parquet"
    df_out.to_parquet(out_path, index=False)

    # Save model metadata
    meta = {
        "method": "ERA5-based weather normalization (TRD §4.6)",
        "training_data": "rural-like cells (frac_built < 0.20, crop+grass > 0.50)",
        "n_rural_cells": len(rural_cells),
        "features": features_day if features_day else [],
        "target": "SUHII (day and night, separate models)",
        "interpretation": (
            "suhii_*_normalized = SUHII with weather-driven variation removed. "
            "What remains is the urban-form signal (built surface, canopy, water) "
            "that planners control. Use normalized values for trend analysis "
            "and cross-year comparison."
        ),
    }
    meta_path = DATA_DIR / "weather_normalization_meta.json"
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    print(f"\n  ✓ Saved normalized SUHII to {out_path}")
    print(f"  ✓ Saved model metadata to {meta_path}")
    print(f"  Total rows: {len(df_out)}")
    print("=" * 65)


if __name__ == "__main__":
    main()
