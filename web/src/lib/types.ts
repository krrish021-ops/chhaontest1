export type LayerSource = "observed" | "ml_fit" | "forecast_2031" | "forecast_2041";
export type BasemapStyle = "dark" | "streets";

// Matches api/schemas/heat.py::CityInfo exactly.
export interface CityInfo {
  id: string;
  name: string;
  name_mr: string;
  state: string;
  bbox: [number, number, number, number];
  buffer_km: number;
  priority: number;
  notes: string;
  lat: number;
  lon: number;
  zoom: number;
  data_available: boolean;
}

export interface UncertaintyBand {
  p10: number;
  p50: number;
  p90: number;
}

export interface CellSummary {
  cell_id: string;
  rank?: number;
  lon: number;
  lat: number;
  suhii_day: number;
  suhii_night: number;
  lst_day: number;
  lst_night: number;
  heat_level_day?: string;
  heat_level_night?: string;
  frac_built: number;
  frac_tree: number;
  frac_water: number;
  frac_crop?: number;
  frac_grass?: number;
  frac_bare?: number;
  ndvi?: number;
  ndbi?: number;
  building_height?: number;
  night_lights?: number;
  vulnerability_index?: number;
}

export interface ShapDriver {
  feature: string;
  value: number;
  shap_contribution_degC: number;
  text: string;
}

export interface CellExplanation {
  cell_id: string;
  night_suhii_degC: number;
  drivers: ShapDriver[];
}

// Matches api/schemas/scenario.py::ScenarioRequest exactly.
// NOTE: "cool_roofs" is NOT a valid action — the underlying model has
// no albedo feature to represent it.
export interface ScenarioRequest {
  city_id: string;
  cell_id: string;
  action: "add_trees" | "add_concrete" | "restore_water";
  area_pct_change: number;
  cost_overrides?: Record<string, number>;
}

// Matches api/schemas/scenario.py::ScenarioResponse exactly.
export interface ScenarioResponse {
  cell_id: string;
  city_id: string;
  action: string;
  applied_change_pct: number;
  original_suhii_night: UncertaintyBand;
  new_suhii_night: UncertaintyBand;
  delta_T_degC: UncertaintyBand;
  estimated_cost_inr: number;
  cost_formatted: string;
  has_uncertainty: boolean;
  extrapolation_warning: boolean;
  confidence: "high" | "medium" | "low" | string;
  domain_verdict?: string;
  cross_city_model: boolean;
  model_source_city: string;
}
