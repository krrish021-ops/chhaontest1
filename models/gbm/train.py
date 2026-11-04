"""
[DEPRECATED] Original M2 training script with random KFold.

Kept for reference only. DO NOT USE — random KFold on spatial data leaks.

For honest training, use:
    python -m models.gbm.train_blocked
"""

import warnings

warnings.warn(
    "models.gbm.train is deprecated. Use models.gbm.train_blocked instead.",
    DeprecationWarning,
    stacklevel=2,
)

if __name__ == "__main__":
    print("⚠️  This script is deprecated.")
    print("   Run: python -m models.gbm.train_blocked")
