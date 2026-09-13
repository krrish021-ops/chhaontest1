export type LayerSource = "observed" | "ml_fit" | "forecast_2031" | "forecast_2041";
export type BasemapStyle = "dark" | "streets" | "satellite";

export interface CityInfo {
  id: string;
  name: string;
  state: string;
  lat: number;
  lon: number;
  zoom: number;
  description?: string;
}

export interface UncertaintyBand {
  p10: number;
  p50: number;
  p90: number;
}

export interface CellSummary {
  cell_id: string;
  suhii_day: number;
  suhii_night: number;
  lst_day: number;
  lst_night: number;
  frac_built: number;
  frac_tree: number;
  frac_water: number;
  frac_crop: number;
  frac_grass: number;
  frac_bare?: number;
  ndvi?: number;
  ndbi?: number;
  building_height?: number;
  night_lights?: number;
  vulnerability_index?: number;
  rank?: number;
}

export interface ShapDriver {
  feature: string;
  contribution_degC: number;
  direction: "+" | "-";
  description: string;
}

export interface CellExplanation {
  cell_id: string;
  suhii_night: number;
  base_temperature: number;
  drivers: ShapDriver[];
}

export interface ScenarioRequest {
  cell_id: string;
  action: "add_trees" | "add_concrete" | "restore_water" | "cool_roofs";
  area_pct_change: number;
  cost_overrides?: Record<string, number>;
}

export interface ScenarioResponse {
  cell_id: string;
  action: string;
  area_pct_change: number;
  original_suhii_night: UncertaintyBand;
  new_suhii_night: UncertaintyBand;
  delta_T_degC: UncertaintyBand;
  estimated_cost_inr: number;
  estimated_cost_formatted: string;
  extrapolation_warning: boolean;
  confidence: "high" | "medium" | "low";
  domain_verdict?: string;
}
