"""
Pydantic Schemas for Heat Data and Cities.
==========================================
Defines request and response structures for API validation.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class CityInfo(BaseModel):
    id: str = Field(..., example="nagpur")
    name: str = Field(..., example="Nagpur")
    name_mr: str = Field(..., example="नागपूर")
    state: str = Field(..., example="Maharashtra")
    bbox: List[float] = Field(..., example=[78.90, 21.05, 79.25, 21.25])
    buffer_km: int = Field(..., example=20)
    priority: int = Field(..., example=1)
    notes: str = Field(..., example="Hottest city in Maharashtra.")
    lat: float = Field(..., example=21.15, description="Bbox centroid latitude, for map centering")
    lon: float = Field(..., example=79.07, description="Bbox centroid longitude, for map centering")
    zoom: int = Field(11, example=11, description="Suggested map zoom level")
    data_available: bool = Field(
        ..., example=True,
        description="True only if this city has real ingested heatmap/boundary data on disk today"
    )


class DriverContribution(BaseModel):
    feature: str = Field(..., example="frac_built")
    value: float = Field(..., example=0.78)
    shap_contribution_degC: float = Field(..., example=2.10)
    text: str = Field(..., example="78% sealed surface adds +2.10°C")


class CellExplanation(BaseModel):
    cell_id: str = Field(..., example="C0187")
    night_suhii_degC: float = Field(..., example=4.30)
    drivers: List[DriverContribution]


class CellSummary(BaseModel):
    cell_id: str = Field(..., example="C0187")
    lon: float = Field(..., example=78.95)
    lat: float = Field(..., example=21.12)
    lst_day: float = Field(..., example=37.8)
    lst_night: float = Field(..., example=28.4)
    suhii_day: float = Field(..., example=-2.6)
    suhii_night: float = Field(..., example=2.0)
    heat_level_day: str = Field(..., example="Low ⬜")
    heat_level_night: str = Field(..., example="Moderate 🟨")
    frac_built: float = Field(..., example=0.52)
    frac_tree: float = Field(..., example=0.14)
    frac_water: float = Field(..., example=0.01)
