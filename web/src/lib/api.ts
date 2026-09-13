import type {
  HeatmapGeoJSON,
  CellSummary,
  CellExplanation,
  ScenarioRequest,
  ScenarioResponse,
  CityInfo,
} from './types';

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  console.log('[API]', init?.method || 'GET', url);

  let res: Response;
  try {
    res = await fetch(url, {
      ...init,
      headers: {
        'Content-Type': 'application/json',
        ...(init?.headers || {}),
      },
    });
  } catch (err: any) {
    console.error('[API] Network error:', err);
    throw new Error(
      `Cannot reach API at ${API_BASE_URL}. Is the backend running? (uvicorn api.main:app --port 8000)`
    );
  }

  if (!res.ok) {
    const body = await res.text().catch(() => '');
    console.error('[API] Error', res.status, body);
    throw new Error(`API ${res.status}: ${body || res.statusText}`);
  }

  return res.json();
}

export async function fetchCities(): Promise<CityInfo[]> {
  return apiFetch<CityInfo[]>('/api/v1/cities');
}

export async function fetchLayerGeoJSON(
  cityId: string
): Promise<HeatmapGeoJSON> {
  // Backend may return either a FeatureCollection directly OR wrapped
  const data = await apiFetch<any>(`/api/v1/layers/${cityId}`);

  // Normalize response shape
  if (data && data.type === 'FeatureCollection') {
    return data as HeatmapGeoJSON;
  }
  if (data && data.geojson && data.geojson.type === 'FeatureCollection') {
    return data.geojson as HeatmapGeoJSON;
  }
  if (data && data.features) {
    return { type: 'FeatureCollection', features: data.features };
  }

  console.warn('[API] Unexpected layers response shape:', data);
  throw new Error('Layers endpoint returned unexpected format');
}

export async function fetchCells(
  cityId: string,
  limit: number = 50
): Promise<CellSummary[]> {
  const data = await apiFetch<any>(
    `/api/v1/cells/${cityId}?limit=${limit}`
  );

  // Normalize: might be array or {cells: [...]}
  if (Array.isArray(data)) return data;
  if (data && Array.isArray(data.cells)) return data.cells;
  if (data && Array.isArray(data.items)) return data.items;

  console.warn('[API] Unexpected cells response shape:', data);
  return [];
}

export async function fetchCellExplanation(
  cellId: string
): Promise<CellExplanation> {
  return apiFetch<CellExplanation>(`/api/v1/cell/${cellId}/explain`);
}

export async function evaluateScenario(
  request: ScenarioRequest
): Promise<ScenarioResponse> {
  return apiFetch<ScenarioResponse>('/api/v1/scenario/evaluate', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}
