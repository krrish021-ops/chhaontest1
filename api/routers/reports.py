"""
FastAPI Router for PDF Reports Generation and Data Exports.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pathlib import Path
from datetime import datetime
import pandas as pd
import geopandas as gpd

from api.schemas.report import ReportGenerateRequest, ReportGenerateResponse
from reports.generator import build_pdf_report

router = APIRouter(prefix="/api/v1", tags=["Reports & Exports"])

REPORTS_DIR = Path("data/reports")
TABLES_DIR = Path("data/tables")
BOUNDS_DIR = Path("data/boundaries")
DEMO_DIR = Path("data/demo")


@router.post("/report/generate", response_model=ReportGenerateResponse)
async def generate_pdf_report(req: ReportGenerateRequest):
    """
    Triggers generation of a statutory thermal audit PDF report for a city.
    """
    try:
        pdf_path = build_pdf_report(req.city_id.lower())
        file_size = pdf_path.stat().st_size / 1024
        filename = pdf_path.name

        return ReportGenerateResponse(
            status="ready",
            city_id=req.city_id,
            report_url=f"/api/v1/report/download/{filename}",
            filename=filename,
            file_size_kb=round(file_size, 1),
            generated_at=datetime.utcnow().isoformat() + "Z"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


@router.get("/report/download/{filename}")
async def download_pdf_report(filename: str):
    """Downloads a pre-generated PDF report."""
    file_path = REPORTS_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Report file not found")
    
    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=filename
    )


@router.get("/export/{city_id}")
async def export_city_data(city_id: str, format: str = "geojson"):
    """
    Exports full spatial dataset for municipal GIS ingestion.
    Supported formats: GeoJSON, CSV.
    """
    city = city_id.lower()
    
    if format.lower() == "geojson":
        # Check normalized demo GeoJSON first
        geo_path = DEMO_DIR / f"{city}_heatmap_normalized.geojson"
        if not geo_path.exists():
            geo_path = DEMO_DIR / f"{city}_forecast_heatmap.geojson"
        if not geo_path.exists():
            geo_path = DEMO_DIR / f"{city}_heatmap.geojson"
            
        if not geo_path.exists():
            raise HTTPException(status_code=404, detail=f"GeoJSON layer for {city} not found")
            
        return FileResponse(
            path=str(geo_path),
            media_type="application/geo+json",
            filename=f"chhaon_{city}_heat_layer.geojson"
        )

    elif format.lower() == "csv":
        csv_path = TABLES_DIR / f"{city}_master_2024.parquet"
        if not csv_path.exists():
            csv_path = TABLES_DIR / f"{city}_feature_matrix.parquet"
            
        if not csv_path.exists():
            raise HTTPException(status_code=404, detail=f"Data table for {city} not found")

        df = pd.read_parquet(csv_path)
        tmp_csv = REPORTS_DIR / f"chhaon_{city}_data.csv"
        df.to_csv(tmp_csv, index=False)

        return FileResponse(
            path=str(tmp_csv),
            media_type="text/csv",
            filename=f"chhaon_{city}_data.csv"
        )
    else:
        raise HTTPException(status_code=400, detail="Unsupported format. Use 'geojson' or 'csv'")
