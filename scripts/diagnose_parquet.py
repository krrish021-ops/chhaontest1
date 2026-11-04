"""
Diagnostic script to inspect generated Parquet files.
Checks shape, dtypes, and null counts of each step in the pipeline.
"""

from pathlib import Path
import pandas as pd

DATA_DIR = Path("data/tables")

files = [
    "nagpur_monthly_lst_multiyear.parquet",
    "nagpur_rural_reference_multiyear.parquet",
    "nagpur_suhii_multiyear.parquet",
    "nagpur_era5_monthly.parquet",
    "nagpur_suhii_weather_normalized.parquet",
]


def diagnose_file(filename):
    path = DATA_DIR / filename
    print("\n" + "=" * 65)
    print(f"  FILE: {filename}")
    print("=" * 65)

    if not path.exists():
        print("  ❌ FILE DOES NOT EXIST")
        return

    try:
        df = pd.read_parquet(path)
        print(f"  Shape: {df.shape}")
        print("\n  Columns & Null Counts:")
        for col in df.columns:
            null_count = int(df[col].isna().sum())
            pct_null = (null_count / len(df)) * 100 if len(df) > 0 else 0
            dtype_str = str(df[col].dtype)
            sample_vals = df[col].dropna().head(3).tolist()
            print(
                f"    - {col:<32} {dtype_str:<12} | Nulls: {null_count:<5} ({pct_null:>5.1f}%) | Samples: {sample_vals}"
            )
    except Exception as e:
        print(f"  ⚠ Error reading file: {e}")


def main():
    print("=" * 65)
    print("  CHHAON PIPELINE PARQUET DIAGNOSTIC")
    print("=" * 65)

    for f in files:
        diagnose_file(f)


if __name__ == "__main__":
    main()
