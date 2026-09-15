import { CityInfo, CellSummary, CellExplanation, ScenarioRequest, ScenarioResponse } from "./types";

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export async function fetchCities(): Promise<CityInfo[]> {
  const res = await fetch(`${API_BASE}/api/v1/cities`);
  if (!res.ok) throw new Error("Failed to fetch cities");
  return res.json();
}

export async function fetchAoi(cityId: string) {
  const res = await fetch(`${API_BASE}/api/v1/aoi/${cityId}`);
  if (!res.ok) throw new Error(`Failed to fetch AOI for ${cityId}`);
  return res.json();
}

export async function fetchHeatmapGeoJSON(cityId: string = "nagpur") {
  const res = await fetch(`${API_BASE}/api/v1/layers/${cityId}`);
  if (!res.ok) throw new Error(`Failed to fetch layers for ${cityId}`);
  return res.json();
}

// Alias for backwards compatibility
export const fetchHeatmap = fetchHeatmapGeoJSON;

export async function fetchCellRankings(
  cityId: string = "nagpur",
  sortBy: string = "suhii_night",
  limit: number = 50
): Promise<CellSummary[]> {
  const res = await fetch(
    `${API_BASE}/api/v1/cells/${cityId}?sort_by=${sortBy}&limit=${limit}&ascending=false`
  );
  if (!res.ok) throw new Error(`Failed to fetch rankings for ${cityId}`);
  return res.json();
}

// Alias for backwards compatibility
export const fetchCells = fetchCellRankings;

export async function fetchCellExplanation(cellId: string): Promise<CellExplanation> {
  const res = await fetch(`${API_BASE}/api/v1/cell/${cellId}/explain`);
  if (!res.ok) throw new Error(`Failed to fetch SHAP explanation for ${cellId}`);
  return res.json();
}

export async function evaluateScenario(payload: ScenarioRequest): Promise<ScenarioResponse> {
  const res = await fetch(`${API_BASE}/api/v1/scenario/evaluate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Scenario evaluation failed");
  return res.json();
}
