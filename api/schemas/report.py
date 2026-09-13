"""
Pydantic Schemas for PDF Reports and Data Export Endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class ReportGenerateRequest(BaseModel):
    city_id: str = Field(default="nagpur", description="Target city identifier (e.g. nagpur, pune)")
    include_scenarios: bool = Field(default=True, description="Include simulated intervention counterfactuals")
    officer_name: Optional[str] = Field(default=None, description="Name of drafting town planner")
    department: Optional[str] = Field(default="Town Planning & GIS Cell", description="Municipal Department")


class ReportGenerateResponse(BaseModel):
    status: str
    city_id: str
    report_url: str
    filename: str
    file_size_kb: float
    generated_at: str


class ExportRequest(BaseModel):
    city_id: str
    format: str = Field(default="geojson", description="geojson, csv, or json")
    layer: Optional[str] = Field(default="suhii_night", description="Layer to filter")
