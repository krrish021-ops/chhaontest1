"""
Merge temperature and land cover into one master dataset.
==========================================================
"""

import pandas as pd
from pathlib import Path

CITY = "nagpur"
TABLE_DIR = Path("data/tables")


def main():
    print("🔗 Merging temperature + land cover data...")

    lst_path = TABLE_DIR / f"{CITY}_cell_lst_2024_05.parquet"
    lc_path = TABLE_DIR / f"{CITY}_landcover_2021.parquet"

    if not lst_path.exists() or not lc_path.exists():
        print("⚠️  Input files not found. Run modis_lst and landcover first.")
        return

    lst = pd.read_parquet(lst_path)
    lc = pd.read_parquet(lc_path)

    print(f"   Temperature: {len(lst)} cells")
    print(f"   Land cover:  {len(lc)} cells")

    # Merge on cell_id, lon, lat
    merged = lst.merge(lc, on=["cell_id", "lon", "lat"], how="inner")
    print(f"   Merged:      {len(merged)} cells with complete data")

    out_path = TABLE_DIR / f"{CITY}_master_2024.parquet"
    merged.to_parquet(out_path, index=False)
    print(f"   ✅ Saved master dataset: {out_path}")


if __name__ == "__main__":
    main()

