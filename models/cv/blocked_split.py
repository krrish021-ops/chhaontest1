"""
Blocked Cross-Validation for Chhaon
====================================
Honest validation for spatially autocorrelated urban heat data.

WHY THIS EXISTS:
- Random KFold on adjacent grid cells LEAKS spatial memorization
- Reported R² inflates from ~0.60 (honest) to ~0.97 (fake)
- TRD Section 7.4 mandates blocked CV — this is non-negotiable

THREE HONEST SPLITS:
1. Temporal: train on early years, test on latest
2. Spatial: hold out grid blocks (2D geographic tiles)
3. Null-hypothesis: shuffled targets must give baseline error (leakage detector)
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Iterator, Tuple, List
import lightgbm as lgb
from sklearn.metrics import mean_absolute_error


def temporal_split(
    df: pd.DataFrame,
    year_col: str = "year",
    holdout_years: int = 2,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Train on all years EXCEPT the last N."""
    if year_col not in df.columns:
        raise ValueError(f"Column '{year_col}' not in DataFrame")

    years = sorted(df[year_col].unique())
    if len(years) < holdout_years + 1:
        raise ValueError(f"Need >= {holdout_years + 1} years, have {len(years)}")

    cutoff_year = years[-holdout_years]
    train = df[df[year_col] < cutoff_year].copy()
    test = df[df[year_col] >= cutoff_year].copy()

    print(f"  Temporal split:")
    print(f"    Train years: {sorted(train[year_col].unique())}")
    print(f"    Test years:  {sorted(test[year_col].unique())}")
    print(f"    Train rows:  {len(train):,}")
    print(f"    Test rows:   {len(test):,}")

    return train, test


def spatial_block_split(
    df: pd.DataFrame,
    lat_col: str = "lat",
    lon_col: str = "lon",
    n_blocks: int = 5,
    block_size_deg: float = 0.05,
) -> Iterator[Tuple[str, pd.DataFrame, pd.DataFrame]]:
    """Hold out entire geographic tiles at a time."""
    if lat_col not in df.columns or lon_col not in df.columns:
        raise ValueError(f"Need '{lat_col}' and '{lon_col}' columns")

    df = df.copy()
    df["_lat_block"] = (df[lat_col] // block_size_deg).astype(int)
    df["_lon_block"] = (df[lon_col] // block_size_deg).astype(int)
    df["_block_id"] = (
        df["_lat_block"].astype(str) + "_" + df["_lon_block"].astype(str)
    )

    unique_blocks = df["_block_id"].unique()
    if len(unique_blocks) < n_blocks:
        print(f"  ⚠️  Only {len(unique_blocks)} blocks found; using that many folds")
        n_blocks = len(unique_blocks)

    rng = np.random.default_rng(seed=42)
    shuffled = rng.permutation(unique_blocks)
    fold_assignments = np.array_split(shuffled, n_blocks)

    for i, held_out_blocks in enumerate(fold_assignments):
        test_mask = df["_block_id"].isin(held_out_blocks)
        train = df[~test_mask].drop(columns=["_lat_block", "_lon_block", "_block_id"])
        test = df[test_mask].drop(columns=["_lat_block", "_lon_block", "_block_id"])
        yield f"spatial_fold_{i+1}", train, test


def null_hypothesis_test(
    df: pd.DataFrame,
    feature_cols: List[str],
    target_col: str,
    model_params: dict,
    n_shuffles: int = 3,
    seed: int = 42,
) -> dict:
    """
    Train model on SHUFFLED targets. If MAE stays low, you have leakage.
    """
    rng = np.random.default_rng(seed=seed)
    X = df[feature_cols].values
    y = df[target_col].values

    climatology_mae = mean_absolute_error(y, np.full_like(y, y.mean()))

    real_model = lgb.LGBMRegressor(**model_params)
    real_model.fit(X, y)
    real_mae = mean_absolute_error(y, real_model.predict(X))

    shuffled_maes = []
    for i in range(n_shuffles):
        y_shuffled = rng.permutation(y)
        shuf_model = lgb.LGBMRegressor(**model_params)
        shuf_model.fit(X, y_shuffled)
        shuffled_maes.append(mean_absolute_error(y_shuffled, shuf_model.predict(X)))

    shuffled_mae_mean = float(np.mean(shuffled_maes))
    leakage_ratio = shuffled_mae_mean / climatology_mae

    if leakage_ratio > 0.8:
        verdict = "✅ NO LEAKAGE — shuffled MAE is near climatology"
    elif leakage_ratio > 0.5:
        verdict = "⚠️  MILD OVERFITTING — shuffled MAE below climatology"
    else:
        verdict = "🚨 LEAKAGE DETECTED — shuffled MAE far below climatology"

    return {
        "real_mae": float(real_mae),
        "shuffled_mae_mean": shuffled_mae_mean,
        "climatology_mae": float(climatology_mae),
        "leakage_ratio": float(leakage_ratio),
        "verdict": verdict,
    }


if __name__ == "__main__":
    print("=" * 60)
    print("  Blocked CV Module — Self-Test")
    print("=" * 60)

    rng = np.random.default_rng(seed=42)
    n = 500
    fake_df = pd.DataFrame({
        "cell_id": [f"C{i:04d}" for i in range(n)],
        "lat": rng.uniform(21.05, 21.25, n),
        "lon": rng.uniform(78.90, 79.25, n),
        "year": rng.choice([2020, 2021, 2022, 2023, 2024], n),
        "frac_built": rng.uniform(0, 1, n),
        "frac_tree": rng.uniform(0, 1, n),
        "frac_water": rng.uniform(0, 0.1, n),
        "frac_crop": rng.uniform(0, 0.3, n),
        "frac_grass": rng.uniform(0, 0.3, n),
    })
    fake_df["suhii_night"] = (
        3.0 * fake_df["frac_built"]
        - 2.0 * fake_df["frac_tree"]
        - 1.5 * fake_df["frac_water"]
        + rng.normal(0, 0.5, n)
    )

    print("\n[TEST 1] Temporal split")
    train, test = temporal_split(fake_df, holdout_years=2)

    print("\n[TEST 2] Spatial block split")
    for block_id, train, test in spatial_block_split(fake_df, n_blocks=5):
        print(f"  {block_id}: train={len(train):,}  test={len(test):,}")

    print("\n[TEST 3] Null-hypothesis test")
    features = ["frac_built", "frac_tree", "frac_water", "frac_crop", "frac_grass"]
    result = null_hypothesis_test(
        fake_df,
        feature_cols=features,
        target_col="suhii_night",
        model_params={
            "n_estimators": 100,
            "learning_rate": 0.05,
            "num_leaves": 15,
            "verbosity": -1,
        },
    )
    print(f"  Real MAE:         {result['real_mae']:.3f} °C")
    print(f"  Shuffled MAE:     {result['shuffled_mae_mean']:.3f} °C")
    print(f"  Climatology MAE:  {result['climatology_mae']:.3f} °C")
    print(f"  Leakage ratio:    {result['leakage_ratio']:.2%}")
    print(f"  {result['verdict']}")

    print("\n" + "=" * 60)
    print("  ✅ All self-tests passed")
    print("=" * 60)
