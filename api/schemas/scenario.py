"""Pydantic schemas for scenario evaluation with uncertainty bands and domain guard."""

from pydantic import BaseModel, Field
from typing import Literal, Dict, Optional


class ScenarioRequest(BaseModel):
    cell_id: str = Field(..., description="Cell identifier, e.g. C0187")
    action: Literal["add_trees", "add_concrete", "restore_water"]
    area_pct_change: float = Field(
        ..., ge=1.0, le=100.0,
        description="Percentage of cell area to modify (1-100)"
    )
    cost_overrides: Optional[Dict[str, float]] = Field(
        None, description="Optional overrides for ₹ cost rates"
    )


class UncertaintyBand(BaseModel):
    p10: float = Field(..., description="10th percentile — low estimate (°C)")
    p50: float = Field(..., description="Median — most likely (°C)")
    p90: float = Field(..., description="90th percentile — high estimate (°C)")


class ScenarioResponse(BaseModel):
    cell_id: str
    action: str
    applied_change_pct: float
    original_suhii_night: UncertaintyBand
    new_suhii_night: UncertaintyBand
    delta_T_degC: UncertaintyBand
    estimated_cost_inr: int
    cost_formatted: str
    has_uncertainty: bool
    
    # New domain guard fields
    extrapolation_warning: bool = Field(False, description="True if scenario is outside training domain")
    confidence: str = Field("medium", description="high, medium, or low")
    domain_verdict: str = Field("", description="Plain language explanation of domain guard result")
