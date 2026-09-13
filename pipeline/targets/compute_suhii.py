"""
Compute Surface Urban Heat Island Intensity (SUHII) per cell.
==============================================================
SUHII = Cell Temperature - Rural Reference Temperature
"""

import pandas as pd
from pathlib import Path

CITY = "nagpur"
TABLE_DIR = Path("data/tables")


def heat_label(suhii):
    if suhii >= 6.0:
        return "Extreme 🔴"
    if suhii >= 4.0:
        return "High 🟧"
    if suhii >= 2.0:
        return "Moderate 🟨"
    if suhii >= 0.0:
        return "Low ⬜"
    return "Cool 🟦"


def main():
    print("🌡️  Computing SUHII per grid cell...")

    master_path = TABLE_DIR / f"{CITY}_master_2024.parquet"
    rural_path = TABLE_DIR / f"{CITY}_rural_reference.parquet"

    if not master_path.exists() or not rural_path.exists():
        print("⚠️  Input files not found. Run previous steps first.")
        return

    master = pd.read_parquet(master_path)
    rural = pd.read_parquet(rural_path)

    # Use May rural reference
    rural_may = rural[rural["month"] == 5].iloc[0]
    rural_day = rural_may["rural_lst_day"]
    rural_night = rural_may["rural_lst_night"]

    print(
        f"   Rural reference (May): Day={rural_day:.1f}°C, Night={rural_night:.1f}°C"
    )

    # Compute SUHII = Urban - Rural
    master["suhii_day"] = master["lst_day"] - rural_day
    master["suhii_night"] = master["lst_night"] - rural_night

    master["heat_level_day"] = master["suhii_day"].apply(heat_label)
    master["heat_level_night"] = master["suhii_night"].apply(heat_label)

    out_path = TABLE_DIR / f"{CITY}_suhii_2024.parquet"
    master.to_parquet(out_path, index=False)
    print(f"   ✅ SUHII dataset saved: {out_path}")

    print(f"\n{'=' * 55}")
    print(f"  SUHII Results — Nagpur, May 2024")
    print(f"{'=' * 55}")
    print(f"  {'Metric':<25} {'Day':>8} {'Night':>8}")
    print(f"  {'-' * 45}")
    print(
        f"  {'Mean SUHII':<25} {master['suhii_day'].mean():>+7.1f}°C {master['suhii_night'].mean():>+7.1f}°C"
    )
    print(
        f"  {'Max SUHII (hottest)':<25} {master['suhii_day'].max():>+7.1f}°C {master['suhii_night'].max():>+7.1f}°C"
    )
    print(
        f"  {'Min SUHII (coolest)':<25} {master['suhii_day'].min():>+7.1f}°C {master['suhii_night'].min():>+7.1f}°C"
    )
    print(f"{'=' * 55}")


if __name__ == "__main__":
    main()
