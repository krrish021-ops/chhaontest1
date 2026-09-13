"""
ERA5-Land monthly weather extraction for Nagpur grid cells.
Extracts 7 meteorological variables for 2020-2024, March-June.

Source: ECMWF ERA5-Land Monthly Aggregated (GEE)
Resolution: ~11 km (0.1°) — regional weather signal, same for nearby cells
Purpose: Weather normalization of SUHII (TRD §4.6)

Outputs:
  data/tables/nagpur_era5_monthly.parquet
"""

import ee
import pandas as pd
import geopandas as gpd
import json
import numpy as np
from pathlib import Path

ee.Initialize(project="chhaon-508513")

DATA_DIR = Path("data/tables")
DATA_DIR.mkdir(parents=True, exist_ok=True)
GRID_PATH = "data/boundaries/nagpur_grid.geojson"

YEARS = [2020, 2021, 2022, 2023, 2024]
MONTHS = [3, 4, 5, 6]
MONTH_NAMES = {3: "Mar", 4: "Apr", 5: "May", 6: "Jun"}

# ── ERA5-Land bands we need ─────────────────────────────────────────
# All from ECMWF/ERA5_LAND/MONTHLY_AGGR
# Temperature bands are in Kelvin; precip in meters; radiation in J/m²
BANDS = {
    "era5_t2m": "temperature_2m",                    # 2m air temp (K)
    "era5_dewpoint": "dewpoint_temperature_2m",       # dewpoint (K)
    "era5_skin_temp": "skin_temperature",              # surface skin temp (K)
    "era5_u_wind": "u_component_of_wind_10m",         # east-west wind (m/s)
    "era5_v_wind": "v_component_of_wind_10m",         # north-south wind (m/s)
    "era5_precip": "total_precipitation_sum",          # total precip (m)
    "era5_solar": "surface_solar_radiation_downwards_sum",  # insolation (J/m²)
    "era5_soil_moist": "volumetric_soil_water_layer_1",     # topsoil moisture (m³/m³)
}


def process_era5_image(img):
    """
    Rename bands, convert temperatures K→°C, compute wind speed.
    Returns a multi-band image with clean names and units.
    """
    # Select and rename
    renamed = img.select(
        list(BANDS.values()),
        list(BANDS.keys()),
    )

    # Convert temperatures from Kelvin to Celsius
    t2m_c = renamed.select("era5_t2m").subtract(273.15).rename("era5_t2m_c")
    dew_c = renamed.select("era5_dewpoint").subtract(273.15).rename("era5_dewpoint_c")
    skin_c = renamed.select("era5_skin_temp").subtract(273.15).rename("era5_skin_temp_c")

    # Compute wind speed magnitude from u and v components
    u = renamed.select("era5_u_wind")
    v = renamed.select("era5_v_wind")
    wind_speed = u.pow(2).add(v.pow(2)).sqrt().rename("era5_wind_speed")

    # Dewpoint depression (T - Td) — proxy for atmospheric dryness
    # Higher = drier air = more radiative heating of surfaces
    dewpoint_depression = t2m_c.subtract(dew_c).rename("era5_dewpoint_depression")

    # Precipitation: convert meters to mm for readability
    precip_mm = renamed.select("era5_precip").multiply(1000).rename("era5_precip_mm")

    # Solar radiation: convert J/m² to MJ/m² for readability
    solar_mj = renamed.select("era5_solar").divide(1e6).rename("era5_solar_mj")

    # Soil moisture: keep as m³/m³ (0-1 range)
    soil = renamed.select("era5_soil_moist").rename("era5_soil_moist")

    # Stack all derived bands
    result = (
        t2m_c
        .addBands(dew_c)
        .addBands(skin_c)
        .addBands(wind_speed)
        .addBands(dewpoint_depression)
        .addBands(precip_mm)
        .addBands(solar_mj)
        .addBands(soil)
    )

    return result


def extract_month(year, month, grid_fc):
    """Extract ERA5 weather for one month across all grid cells."""
    # ERA5 monthly aggregates: the image for month M is dated the 1st of M
    start = ee.Date.fromYMD(year, month, 1)
    end = start.advance(1, "month")

    collection = (
        ee.ImageCollection("ECMWF/ERA5_LAND/MONTHLY_AGGR")
        .filterBounds(grid_fc.geometry())
        .filterDate(start, end)
    )

    # Should be exactly 1 image per month, but take median for safety
    img = collection.map(process_era5_image).median()

    # Extract to grid cells
    # ERA5 scale is ~11132 m (0.1°), but we reduce at 1000m to match our grid
    extracted = img.reduceRegions(
        collection=grid_fc,
        reducer=ee.Reducer.mean(),
        scale=11132,  # native ERA5 resolution
    )

    # Tag with temporal metadata
    extracted = extracted.map(
        lambda f: f.set({"year": year, "month": month})
    )

    return extracted


def main():
    print("=" * 65)
    print("  ERA5-LAND MONTHLY WEATHER EXTRACTION")
    print("  Source: ECMWF/ERA5_LAND/MONTHLY_AGGR (~11 km resolution)")
    print(f"  Years: {YEARS}  Months: {[MONTH_NAMES[m] for m in MONTHS]}")
    print("=" * 65)

    # Load grid
    print(f"\n[1/3] Loading grid...")
    grid_gdf = gpd.read_file(GRID_PATH)
    n_cells = len(grid_gdf)
    print(f"  ✓ {n_cells} cells")

    grid_fc = ee.FeatureCollection(json.loads(grid_gdf.to_json()))

    # Extract each year-month
    all_rows = []
    total = len(YEARS) * len(MONTHS)
    step = 0

    # Output column names (after processing)
    out_cols = [
        "era5_t2m_c", "era5_dewpoint_c", "era5_skin_temp_c",
        "era5_wind_speed", "era5_dewpoint_depression",
        "era5_precip_mm", "era5_solar_mj", "era5_soil_moist",
    ]

    for year in YEARS:
        for month in MONTHS:
            step += 1
            label = f"{year}-{MONTH_NAMES[month]}"
            print(f"\n  [{step:2d}/{total}] {label} ...", end=" ", flush=True)

            try:
                extracted = extract_month(year, month, grid_fc)
                info = extracted.getInfo()

                for feat in info["features"]:
                    p = feat["properties"]
                    row = {
                        "cell_id": p.get("cell_id", ""),
                        "year": year,
                        "month": month,
                    }
                    for col in out_cols:
                        val = p.get(col)
                        row[col] = round(val, 3) if val is not None else np.nan
                    all_rows.append(row)

                # Quick stats from first cell
                sample = all_rows[-1]
                print(
                    f"T2m {sample['era5_t2m_c']:.1f}°C | "
                    f"Wind {sample['era5_wind_speed']:.1f}m/s | "
                    f"Rain {sample['era5_precip_mm']:.0f}mm  ✓"
                )

            except ee.EEException as e:
                print(f"⚠ GEE ERROR: {e}")
            except Exception as e:
                print(f"⚠ ERROR: {e}")

    # Build DataFrame
    df = pd.DataFrame(all_rows)

    # Save
    out_path = DATA_DIR / "nagpur_era5_monthly.parquet"
    df.to_parquet(out_path, index=False)

    print(f"\n[3/3] Saved to {out_path}")
    print("=" * 65)
    print("  ERA5 WEATHER SUMMARY")
    print("=" * 65)
    print(f"  Rows:            {len(df)}")
    print(f"  Unique cells:    {df['cell_id'].nunique()}")
    print(f"  T2m range:       {df['era5_t2m_c'].min():.1f} to"
          f" {df['era5_t2m_c'].max():.1f} °C")
    print(f"  Wind range:      {df['era5_wind_speed'].min():.1f} to"
          f" {df['era5_wind_speed'].max():.1f} m/s")
    print(f"  Precip range:    {df['era5_precip_mm'].min():.0f} to"
          f" {df['era5_precip_mm'].max():.0f} mm/month")
    print(f"  Soil moist range:{df['era5_soil_moist'].min():.3f} to"
          f" {df['era5_soil_moist'].max():.3f} m³/m³")
    print(f"  File size:       {out_path.stat().st_size / 1024:.1f} KB")
    print("=" * 65)


if __name__ == "__main__":
    main()
