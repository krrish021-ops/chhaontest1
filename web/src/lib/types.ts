// TypeScript interfaces for Chhaon frontend

export type LayerSource = 'observed' | 'ml_fit' | 'forecast_2031' | 'forecast_2041';
export type TimeMode = 'day' | 'night';
export type DisplayMode = 'suhii' | 'absolute';
export type BasemapStyle = 'dark' | 'streets' | 'satellite';

export interface CityInfo {
  city_id: string;
  name: string;
  bbox: [number, number, number, number];
  priority: number;
  timezone?: string;
}

export interface CellProperties {
  cell_id: string;
  lon: number;
  lat: number;
  lst_day: number;
  lst_night: number;
  suhii_day: number;
  suhii_night: number;
  heat_level_day?: string;
  heat_level_night?: string;
  frac_built: number;
  frac_tree: number;
  frac_water: number;
  frac_crop?: number;
  frac_grass?: number;
  // Forecast fields
  suhii_night_ml_fit?: number;
  suhii_night_2031?: number;
  suhii_night_2041?: number;
  suhii_day_ml_fit?: number;
  suhii_day_2031?: number;
  suhii_day_2041?: number;
}

export interface HeatmapFeature {
  type: 'Feature';
  geometry: {
    type: 'Polygon';
    coordinates: number[][][];
  };
  properties: CellProperties;
}

export interface HeatmapGeoJSON {
  type: 'FeatureCollection';
  features: HeatmapFeature[];
}

export interface CellSummary {
  cell_id: string;
  lon: number;
  lat: number;
  suhii_day: number;
  suhii_night: number;
  frac_built: number;
  frac_tree: number;
  frac_water: number;
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

export interface UncertaintyBand {
  p10: number;
  p50: number;
  p90: number;
}

export interface ScenarioRequest {
  cell_id: string;
  action: 'add_trees' | 'add_concrete' | 'restore_water';
  area_pct_change: number;
  cost_overrides?: Record<string, number>;
}

export interface ScenarioResponse {
  cell_id: string;
  action: string;
  applied_change_pct: number;
  original_suhii_night: UncertaintyBand;
  new_suhii_night: UncertaintyBand;
  delta_T_degC: UncertaintyBand;
  estimated_cost_inr: number;
  cost_formatted: string;
  has_uncertainty: boolean;
  extrapolation_warning: boolean;
  confidence: string;
  domain_verdict: string;
}
