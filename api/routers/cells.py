"""
Cells & Explainability Router.
==============================
Endpoints for cell rankings and SHAP driver explanations.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List
from api.schemas.heat import CellSummary, CellExplanation
from api.services.heat_service import get_ranked_cells_service, get_cell_explanation_service

router = APIRouter(prefix="/api/v1", tags=["Cells & Rankings"])


@router.get("/cells/{city_id}", response_model=List[CellSummary])
async def get_ranked_cells(
    city_id: str,
    sort_by: str = Query("suhii_night", description="Sort metric: suhii_night, suhii_day, frac_built, etc."),
    limit: int = Query(50, ge=1, le=500, description="Max rows to return")
):
    """
    Get ranked list of cells for a city.
    Powers the Ward/Cell Ranking Table in the UI.
    """
    try:
        return get_ranked_cells_service(city_id, sort_by=sort_by, limit=limit)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"City '{city_id}' not found.")
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/cell/{cell_id}/explain", response_model=CellExplanation)
async def explain_cell_endpoint(cell_id: str):
    """
    Get SHAP explainability for a specific cell (FR-61).
    Answers: 'Why is this cell hot?'
    """
    try:
        return get_cell_explanation_service(cell_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
