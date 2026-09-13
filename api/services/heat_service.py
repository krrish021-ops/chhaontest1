"""
Heat Statistics Service.
========================
Provides cell rankings and integrates with SHAP explainer.
"""

import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from config.loader import get_city
from models.explain.shap_explainer import explain_cell


def get_ranked_cells_service(
    city_id: str,
    sort_by: str = "suhii_night",
    limit: int = 50
) -> List[Dict[str, Any]]:
    """Return top hottest or coolest cells in a city."""
    get_city(city_id)  # Validate city

    table_path = Path("data/tables/nagpur_suhii_2024.parquet")
    if not table_path.exists():
        raise FileNotFoundError(f"Heat data for {city_id} not found.")

    df = pd.read_parquet(table_path)

    # Valid sort columns
    valid_sorts = ["suhii_night", "suhii_day", "lst_day", "lst_night", "frac_built", "frac_tree"]
    if sort_by not in valid_sorts:
        sort_by = "suhii_night"

    df_sorted = df.sort_values(by=sort_by, ascending=False).head(limit)

    cols = [
        "cell_id", "lon", "lat", "lst_day", "lst_night",
        "suhii_day", "suhii_night", "heat_level_day", "heat_level_night",
        "frac_built", "frac_tree", "frac_water"
    ]
    available_cols = [c for c in cols if c in df_sorted.columns]

    return df_sorted[available_cols].to_dict(orient="records")


def get_cell_explanation_service(cell_id: str) -> Dict[str, Any]:
    """Get SHAP explainability for a specific cell."""
    res = explain_cell(cell_id)
    if isinstance(res, str):  # Error message
        raise KeyError(res)
    return res
