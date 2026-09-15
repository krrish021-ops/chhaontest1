"""
Scenario Simulator & Multi-Scenario Comparison Router.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from models.transfer_function.scenario_engine import simulate_intervention
from models.transfer_function.comparison_engine import compare_scenarios
from api.schemas.scenario import ScenarioRequest, ScenarioResponse

router = APIRouter(prefix="/api/v1", tags=["Scenarios"])


class ScenarioOption(BaseModel):
    name: str = Field(description="Scenario name (e.g. Option A - 30% Canopy)")
    action: str = Field(description="add_trees, add_concrete, or restore_water")
    area_pct: float = Field(ge=1, le=80, description="Intervention percentage (1-80%)")


class CompareScenariosRequest(BaseModel):
    city_id: str = Field(default="nagpur")
    cell_id: str = Field(default="C0426")
    scenarios: List[ScenarioOption]


@router.post("/scenario/evaluate", response_model=ScenarioResponse)
async def evaluate_scenario(req: ScenarioRequest):
    """Single-cell counterfactual intervention simulation."""
    try:
        res = simulate_intervention(
            cell_id=req.cell_id,
            action=req.action,
            area_pct_change=req.area_pct_change,
            city_id=req.city_id,
            cost_overrides=req.cost_overrides,
        )
        return ScenarioResponse(**res)
    except FileNotFoundError as e:
        # City has no scenario-capable data at all (e.g. Mumbai, Aurangabad)
        raise HTTPException(status_code=501, detail=str(e))
    except ValueError as e:
        # Cell not found for this city
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scenario/compare")
async def evaluate_multi_scenario_comparison(req: CompareScenariosRequest):
    """
    Evaluates 2 to 4 planning options side-by-side on a target cell.
    """
    try:
        scenario_dicts = [s.model_dump() for s in req.scenarios]
        result = compare_scenarios(
            city_id=req.city_id,
            cell_id=req.cell_id,
            scenarios=scenario_dicts
        )
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")
