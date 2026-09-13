"""
Domain Guard — Extrapolation Detection
=======================================

PRD FR-47: Warn users when a scenario is outside the model's training domain.

USES Mahalanobis distance: measures how "far" a new feature vector is from
the training data cloud, accounting for feature correlations.

If distance > threshold → the model has never seen anything like this →
predictions are unreliable → SHOW WARNING.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial.distance import mahalanobis
from scipy.stats import chi2

TRAINING_PARQUET = Path("data/tables/nagpur_master_2024.parquet")
FEATURES = ["frac_built", "frac_tree", "frac_water", "frac_crop", "frac_grass"]

# Cache for computed statistics
_stats_cache = None


def _get_training_stats():
    """Compute mean and covariance of training features (cached)."""
    global _stats_cache
    if _stats_cache is not None:
        return _stats_cache

    df = pd.read_parquet(TRAINING_PARQUET)
    X = df[FEATURES].values

    mean = X.mean(axis=0)
    cov = np.cov(X, rowvar=False)

    # Regularize covariance for numerical stability
    cov += np.eye(cov.shape[0]) * 1e-6

    inv_cov = np.linalg.inv(cov)

    _stats_cache = {
        "mean": mean,
        "cov": cov,
        "inv_cov": inv_cov,
        "n_features": len(FEATURES),
    }
    return _stats_cache


def check_domain(features: dict | list | np.ndarray) -> dict:
    """
    Check if a feature vector is inside the training domain.

    Args:
        features: dict {feature_name: value} OR array of values in FEATURES order

    Returns:
        {
            "mahalanobis_distance": float,
            "chi2_pvalue": float,  # probability this is "normal"
            "extrapolation_warning": bool,
            "verdict": str,
            "confidence": str,  # "high" | "medium" | "low"
        }
    """
    stats = _get_training_stats()

    # Convert input to array
    if isinstance(features, dict):
        x = np.array([features[f] for f in FEATURES])
    else:
        x = np.array(features)

    # Compute Mahalanobis distance
    dist = mahalanobis(x, stats["mean"], stats["inv_cov"])

    # Chi-squared p-value: probability of seeing this distance under null
    # (i.e. if x IS from the training distribution)
    # Small p-value = unusual point = warning
    dof = stats["n_features"]
    pvalue = 1 - chi2.cdf(dist**2, df=dof)

    # Thresholds (tunable)
    if pvalue > 0.10:
        warning = False
        confidence = "high"
        verdict = "✅ Inside training distribution — high confidence"
    elif pvalue > 0.01:
        warning = False
        confidence = "medium"
        verdict = "⚠️  Edge of training distribution — medium confidence"
    else:
        warning = True
        confidence = "low"
        verdict = "🚨 Outside training distribution — low confidence, extrapolation warning"

    return {
        "mahalanobis_distance": round(float(dist), 3),
        "chi2_pvalue": round(float(pvalue), 4),
        "extrapolation_warning": warning,
        "verdict": verdict,
        "confidence": confidence,
    }


if __name__ == "__main__":
    print("=" * 65)
    print("  🛡️  Domain Guard Self-Test")
    print("=" * 65)

    # Test 1: Typical Nagpur cell (should be INSIDE)
    typical = {
        "frac_built": 0.60, "frac_tree": 0.15, "frac_water": 0.02,
        "frac_crop": 0.10, "frac_grass": 0.13,
    }
    print(f"\n[TEST 1] Typical urban cell:")
    print(f"   Features: {typical}")
    result = check_domain(typical)
    print(f"   {result['verdict']}")
    print(f"   Confidence: {result['confidence']}")

    # Test 2: Extreme cell (all built)
    extreme = {
        "frac_built": 1.0, "frac_tree": 0.0, "frac_water": 0.0,
        "frac_crop": 0.0, "frac_grass": 0.0,
    }
    print(f"\n[TEST 2] Extreme cell (100% built):")
    print(f"   Features: {extreme}")
    result = check_domain(extreme)
    print(f"   {result['verdict']}")
    print(f"   Confidence: {result['confidence']}")

    # Test 3: Impossible cell (100% water)
    impossible = {
        "frac_built": 0.0, "frac_tree": 0.0, "frac_water": 1.0,
        "frac_crop": 0.0, "frac_grass": 0.0,
    }
    print(f"\n[TEST 3] Impossible cell (100% water):")
    print(f"   Features: {impossible}")
    result = check_domain(impossible)
    print(f"   {result['verdict']}")
    print(f"   Confidence: {result['confidence']}")

    print("\n✅ Domain guard tests complete")
