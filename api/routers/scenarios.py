"""Scenario evaluation endpoint."""

from fastapi import APIRouter, HTTPException

from api.schemas.scenario import ScenarioRequest, ScenarioResponse
from models.transfer_function.scenario_engine import simulate_intervention

router = APIRouter(prefix="/api/v1", tags=["scenarios"])


@router.post("/scenario/evaluate", response_model=ScenarioResponse)
async def evaluate_scenario(request: ScenarioRequest):
    """
    Simulate a land-use intervention and return ΔT (°C), cost (₹),
    and uncertainty bands (P10/P50/P90).
    """
    try:
        result = simulate_intervention(
            cell_id=request.cell_id,
            action=request.action,
            area_pct_change=request.area_pct_change,
            cost_overrides=request.cost_overrides,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")
