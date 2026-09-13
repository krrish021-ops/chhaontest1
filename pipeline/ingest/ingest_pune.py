"""
End-to-end automated ingestion pipeline for Pune, Maharashtra.
Target: Pune Municipal Corporation (PMC) urban extent (~300-450 grid cells).

Pulls boundaries, 1km grid, multi-year MODIS LST, rural reference,
ESA WorldCover, Sentinel-2 indices, GHSL height, VIIRS night lights,
and ERA5 weather to build Pune's complete feature matrix.

FIX v3: Robust grid-size validation in step1. Previously, OSM geocoding
could silently return a degenerate/too-small polygon that produced only
1 grid cell, and the size-check only guarded against "too big" boundaries.
Now we validate actual generated cell count and fall back to a known-good
bounding box if the geocoded result is unusable.

Outputs:
  data/boundaries/pune_boundary.geojson
  data/boundaries/pune_grid.geojson
  data/tables/pune_feature_matrix.parquet
"""

import ee
import osmnx as ox
import geopandas as gpd
import pandas as pd
import numpy as np
import json
from pathlib import Path
from shapely.geometry import box, Point

# Initialize Earth Engine
ee.Initialize(project="chhaon-508513")

DATA_TABLES = Path("data/tables")
DATA_BOUNDS = Path("data/boundaries")
DATA_TABLES.mkdir(parents=True, exist_ok=True)
DATA_BOUNDS.mkdir(parents=True, exist_ok=True)

YEARS = [2020, 2021, 2022, 2023, 2024]
MONTHS = [3, 4, 5, 6]
MONTH_NAMES = {3: "Mar", 4: "Apr", 5: "May", 6: "Jun"}
MONSOON_MONTHS = {6, 7, 8, 9}


def step1_boundary_and_grid():
    print("\n[1/7] Fetching Pune Municipal boundary and creating ~1km grid...")
    boundary_path = DATA_BOUNDS / "pune_boundary.geojson"
    grid_path = DATA_BOUNDS / "pune_grid.geojson"

    MIN_VIABLE_CELLS = 50  # below this, the geocoded boundary is unusable

    # Known-good PMC urban core bounding box (fallback, always valid)
    fallback_box = box(73.76, 18.44, 73.96, 18.60)
    fallback_gdf = gpd.GeoDataFrame([{"geometry": fallback_box}], crs="EPSG:4326")

    def build_grid(source_gdf):
        """Attempt to build a 1km grid from a boundary GeoDataFrame."""
        minx, miny, maxx, maxy = source_gdf.total_bounds
        step = 0.009  # ~1km in degrees
        x_coords = np.arange(minx, maxx, step)
        y_coords = np.arange(miny, maxy, step)

        cells = []
        cell_id = 1
        poly_union = source_gdf.unary_union

        for x in x_coords:
            for y in y_coords:
                cell_geom = box(x, y, x + step, y + step)
                if source_gdf.intersects(cell_geom).any():
                    intersection = cell_geom.intersection(poly_union)
                    if not intersection.is_empty:
                        cells.append({"cell_id": f"P{cell_id:04d}", "geometry": cell_geom})
                        cell_id += 1

        return gpd.GeoDataFrame(cells, crs="EPSG:4326")

    # Try specific municipal queries first
    queries = [
        "Pune Municipal Corporation, Maharashtra, India",
        "Pune City, Maharashtra, India",
        "Pune, Maharashtra, India",
    ]

    gdf = None
    grid_gdf = gpd.GeoDataFrame()

    for q in queries:
        try:
            temp_gdf = ox.geocode_to_gdf(q)
            minx, miny, maxx, maxy = temp_gdf.total_bounds
            width, height = maxx - minx, maxy - miny

            # Must be a plausible city size: not too big (district), not too small (point/error)
            if 0.05 < width < 0.6 and 0.05 < height < 0.6:
                temp_grid = build_grid(temp_gdf)
                print(f"  · Tried '{q}': bbox {width:.3f}° x {height:.3f}°, {len(temp_grid)} cells")
                if len(temp_grid) >= MIN_VIABLE_CELLS:
                    gdf = temp_gdf[["geometry"]]
                    grid_gdf = temp_grid
                    print(f"  ✓ Accepted geocoded boundary via '{q}'")
                    break
            else:
                print(f"  · Rejected '{q}': bbox {width:.3f}° x {height:.3f}° (out of plausible city size)")
        except Exception as e:
            print(f"  · Query '{q}' failed: {e}")
            continue

    # Fallback: OSM failed or produced too few cells
    if len(grid_gdf) < MIN_VIABLE_CELLS:
        print(f"  ℹ OSM geocoding did not yield a usable boundary — using PMC urban core fallback bbox")
        gdf = fallback_gdf
        grid_gdf = build_grid(gdf)
        print(f"  ✓ Fallback bbox generated {len(grid_gdf)} cells")

    gdf.to_file(boundary_path, driver="GeoJSON")
    grid_gdf.to_file(grid_path, driver="GeoJSON")
    print(f"  ✓ Final grid: {len(grid_gdf)} cells covering Pune (target: 200-450)")
    return grid_gdf, gdf


def step2_modis_lst(grid_fc):
    print("\n[2/7] Extracting Pune Multi-Year MODIS LST (2020-2024)...")

    def qa_mask_day(img):
        qc = img.select("QC_Day")
        good = qc.bitwiseAnd(0b11).lte(1).And(qc.bitwiseAnd(0b1100).rightShift(2).lte(1))
        lst_c = img.select("LST_Day_1km").multiply(0.02).subtract(273.15)
        return lst_c.updateMask(good).rename("lst_day")

    def qa_mask_night(img):
        qc = img.select("QC_Night")
        good = qc.bitwiseAnd(0b11).lte(1).And(qc.bitwiseAnd(0b1100).rightShift(2).lte(1))
        lst_c = img.select("LST_Night_1km").multiply(0.02).subtract(273.15)
        return lst_c.updateMask(good).rename("lst_night")

    rows = []
    for year in YEARS:
        for month in MONTHS:
            start = ee.Date.fromYMD(year, month, 1)
            end = start.advance(1, "month")
            col = ee.ImageCollection("MODIS/061/MOD11A1").filterBounds(grid_fc.geometry()).filterDate(start, end)

            day_comp = col.map(qa_mask_day).median()
            night_comp = col.map(qa_mask_night).median()
            combined = day_comp.addBands(night_comp)

            extracted = combined.reduceRegions(collection=grid_fc, reducer=ee.Reducer.mean(), scale=1000)
            info = extracted.getInfo()

            for f in info["features"]:
                p = f["properties"]
                rows.append({
                    "cell_id": p.get("cell_id", ""),
                    "city": "pune",
                    "year": year,
                    "month": month,
                    "is_monsoon": 1 if month in MONSOON_MONTHS else 0,
                    "lst_day": round(p.get("lst_day", np.nan), 2) if p.get("lst_day") is not None else np.nan,
                    "lst_night": round(p.get("lst_night", np.nan), 2) if p.get("lst_night") is not None else np.nan,
                })
            print(f"    - {year}-{MONTH_NAMES[month]} extracted", flush=True)

    df_lst = pd.DataFrame(rows)
    return df_lst


def step3_rural_reference_and_suhii(df_lst, boundary_fc):
    print("\n[3/7] Computing Pune rural baseline and SUHII...")
    urban_geom = boundary_fc.geometry()
    rural_ring = urban_geom.buffer(20000).difference(urban_geom.buffer(2000))

    wc = ee.Image("ESA/WorldCover/v200/2021")
    rural_lc = wc.eq(30).Or(wc.eq(40))
    dem = ee.Image("USGS/SRTMGL1_003")
    urban_elev = dem.reduceRegion(reducer=ee.Reducer.mean(), geometry=urban_geom, scale=30, maxPixels=1e9).get("elevation")
    elev_ok = dem.subtract(ee.Number(urban_elev)).abs().lt(100)
    rural_mask = rural_lc.And(elev_ok).selfMask()

    def qa_day(img):
        good = img.select("QC_Day").bitwiseAnd(0b11).lte(1)
        return img.select("LST_Day_1km").multiply(0.02).subtract(273.15).updateMask(good)

    def qa_night(img):
        good = img.select("QC_Night").bitwiseAnd(0b11).lte(1)
        return img.select("LST_Night_1km").multiply(0.02).subtract(273.15).updateMask(good)

    rural_records = []
    for year in YEARS:
        for month in MONTHS:
            start = ee.Date.fromYMD(year, month, 1)
            end = start.advance(1, "month")
            col = ee.ImageCollection("MODIS/061/MOD11A1").filterBounds(rural_ring).filterDate(start, end)

            d_mean = col.map(qa_day).median().updateMask(rural_mask).reduceRegion(
                reducer=ee.Reducer.mean(), geometry=rural_ring, scale=1000, maxPixels=1e9
            ).get("LST_Day_1km")

            n_mean = col.map(qa_night).median().updateMask(rural_mask).reduceRegion(
                reducer=ee.Reducer.mean(), geometry=rural_ring, scale=1000, maxPixels=1e9
            ).get("LST_Night_1km")

            rural_records.append({
                "year": year,
                "month": month,
                "rural_lst_day": d_mean.getInfo() if d_mean else np.nan,
                "rural_lst_night": n_mean.getInfo() if n_mean else np.nan,
            })

    df_rural = pd.DataFrame(rural_records)
    df_merged = df_lst.merge(df_rural, on=["year", "month"], how="left")
    df_merged["suhii_day"] = np.round(df_merged["lst_day"] - df_merged["rural_lst_day"], 2)
    df_merged["suhii_night"] = np.round(df_merged["lst_night"] - df_merged["rural_lst_night"], 2)
    return df_merged


def step4_land_cover(grid_fc):
    print("\n[4/7] Extracting ESA WorldCover 2021 land cover fractions...")
    wc = ee.Image("ESA/WorldCover/v200/2021")
    classes = {
        "frac_built": 50,
        "frac_tree": 10,
        "frac_water": 80,
        "frac_crop": 40,
        "frac_grass": 30,
        "frac_bare": 60,
    }

    bands = [wc.eq(val).rename(name).toFloat() for name, val in classes.items()]
    composite = bands[0]
    for b in bands[1:]:
        composite = composite.addBands(b)

    extracted = composite.reduceRegions(collection=grid_fc, reducer=ee.Reducer.mean(), scale=100)
    info = extracted.getInfo()

    rows = []
    for f in info["features"]:
        p = f["properties"]
        row = {"cell_id": p.get("cell_id", "")}
        for name in classes.keys():
            row[name] = round(p.get(name, 0.0) or 0.0, 4)
        rows.append(row)
    return pd.DataFrame(rows)


def step5_sentinel2_indices(grid_fc):
    print("\n[5/7] Extracting Sentinel-2 MSI spectral indices (NDVI, NDBI, MNDWI, Albedo)...")
    s2 = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(grid_fc.geometry())
        .filterDate("2024-04-15", "2024-06-15")
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 30))
    )

    def mask_and_index(img):
        scl = img.select("SCL")
        clear = scl.eq(2).Or(scl.eq(4)).Or(scl.eq(5)).Or(scl.eq(6)).Or(scl.eq(7))
        img = img.updateMask(clear)

        blue = img.select("B2").divide(10000)
        red = img.select("B4").divide(10000)
        green = img.select("B3").divide(10000)
        nir = img.select("B8").divide(10000)
        swir1 = img.select("B11").divide(10000)
        swir2 = img.select("B12").divide(10000)

        ndvi = nir.subtract(red).divide(nir.add(red)).rename("ndvi")
        ndbi = swir1.subtract(nir).divide(swir1.add(nir)).rename("ndbi")
        mndwi = green.subtract(swir1).divide(green.add(swir1)).rename("mndwi")
        albedo = (
            blue.multiply(0.356)
            .add(red.multiply(0.130))
            .add(nir.multiply(0.373))
            .add(swir1.multiply(0.085))
            .add(swir2.multiply(0.072))
            .subtract(0.0018)
            .rename("albedo")
        )
        return ndvi.addBands(ndbi).addBands(mndwi).addBands(albedo)

    composite = s2.map(mask_and_index).median()
    extracted = composite.reduceRegions(collection=grid_fc, reducer=ee.Reducer.mean(), scale=100)
    info = extracted.getInfo()

    rows = []
    for f in info["features"]:
        p = f["properties"]
        rows.append({
            "cell_id": p.get("cell_id", ""),
            "ndvi": round(p.get("ndvi", 0.0) or 0.0, 4),
            "ndbi": round(p.get("ndbi", 0.0) or 0.0, 4),
            "mndwi": round(p.get("mndwi", 0.0) or 0.0, 4),
            "albedo": round(p.get("albedo", 0.0) or 0.0, 4),
        })
    return pd.DataFrame(rows)


def step6_ghsl_and_viirs(grid_fc):
    print("\n[6/7] Extracting GHSL Building Height + VIIRS Night Lights...")
    ghsl = ee.ImageCollection("JRC/GHSL/P2023A/GHS_BUILT_H").mosaic().select(0).rename("built_height")
    ghsl_masked = ghsl.updateMask(ghsl.gt(0))
    ghsl_ext = ghsl_masked.reduceRegions(collection=grid_fc, reducer=ee.Reducer.mean(), scale=100)

    viirs = (
        ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG")
        .filterDate("2024-04-01", "2024-06-01")
        .select("avg_rad")
        .median()
        .rename("night_lights")
    )
    viirs_ext = viirs.reduceRegions(collection=grid_fc, reducer=ee.Reducer.mean(), scale=500)

    g_info = ghsl_ext.getInfo()["features"]
    v_info = viirs_ext.getInfo()["features"]

    rows = []
    for gf, vf in zip(g_info, v_info):
        gp, vp = gf["properties"], vf["properties"]
        h_mean = round(gp.get("built_height", 0.0) or 0.0, 2)
        ntl_mean = round(vp.get("night_lights", 0.0) or 0.0, 2)
        hwr = round(h_mean / 15.0, 3)
        svf = round(float(np.clip(1.0 - hwr * 0.5, 0.05, 1.0)), 3)

        rows.append({
            "cell_id": gp.get("cell_id", ""),
            "building_height_mean": h_mean,
            "night_lights_mean": ntl_mean,
            "svf_proxy": svf,
        })
    return pd.DataFrame(rows)


def step7_era5_and_assemble(df_base, df_lc, df_s2, df_gv, grid_fc):
    print("\n[7/7] Extracting ERA5-Land weather anomalies and assembling final matrix...")
    bands = {
        "era5_t2m": "temperature_2m",
        "era5_dewpoint": "dewpoint_temperature_2m",
        "era5_u_wind": "u_component_of_wind_10m",
        "era5_v_wind": "v_component_of_wind_10m",
        "era5_precip": "total_precipitation_sum",
        "era5_solar": "surface_solar_radiation_downwards_sum",
        "era5_soil_moist": "volumetric_soil_water_layer_1",
    }

    era5_rows = []
    for year in YEARS:
        for month in MONTHS:
            start = ee.Date.fromYMD(year, month, 1)
            end = start.advance(1, "month")
            col = ee.ImageCollection("ECMWF/ERA5_LAND/MONTHLY_AGGR").filterBounds(grid_fc.geometry()).filterDate(start, end)
            img = col.select(list(bands.values()), list(bands.keys())).median()

            t2m_c = img.select("era5_t2m").subtract(273.15).rename("era5_t2m_c")
            dew_c = img.select("era5_dewpoint").subtract(273.15).rename("era5_dewpoint_c")
            dew_dep = t2m_c.subtract(dew_c).rename("era5_dewpoint_depression")
            wind = img.select("era5_u_wind").pow(2).add(img.select("era5_v_wind").pow(2)).sqrt().rename("era5_wind_speed")
            precip = img.select("era5_precip").multiply(1000).rename("era5_precip_mm")
            solar = img.select("era5_solar").divide(1e6).rename("era5_solar_mj")
            soil = img.select("era5_soil_moist").rename("era5_soil_moist")

            stacked = t2m_c.addBands(dew_dep).addBands(wind).addBands(precip).addBands(solar).addBands(soil)
            extracted = stacked.reduceRegions(collection=grid_fc, reducer=ee.Reducer.mean(), scale=11132)
            info = extracted.getInfo()

            for f in info["features"]:
                p = f["properties"]
                era5_rows.append({
                    "cell_id": p.get("cell_id", ""),
                    "year": year,
                    "month": month,
                    "era5_t2m_c": p.get("era5_t2m_c", np.nan),
                    "era5_dewpoint_depression": p.get("era5_dewpoint_depression", np.nan),
                    "era5_wind_speed": p.get("era5_wind_speed", np.nan),
                    "era5_precip_mm": p.get("era5_precip_mm", np.nan),
                    "era5_solar_mj": p.get("era5_solar_mj", np.nan),
                    "era5_soil_moist": p.get("era5_soil_moist", np.nan),
                })

    df_era5 = pd.DataFrame(era5_rows)

    for col in ["era5_t2m_c", "era5_dewpoint_depression", "era5_wind_speed", "era5_precip_mm", "era5_solar_mj", "era5_soil_moist"]:
        means = df_era5.groupby("month")[col].transform("mean")
        df_era5[f"{col}_anomaly"] = (df_era5[col] - means).round(3)

    df = df_base.merge(df_lc, on="cell_id", how="left")
    df = df.merge(df_s2, on="cell_id", how="left")
    df = df.merge(df_gv, on="cell_id", how="left")
    df = df.merge(df_era5, on=["cell_id", "year", "month"], how="left")

    df["suhii_day_normalized"] = df["suhii_day"]
    df["suhii_night_normalized"] = df["suhii_night"]

    out_path = DATA_TABLES / "pune_feature_matrix.parquet"
    df.to_parquet(out_path, index=False)
    print(f"\n  ✓ Pune feature matrix saved to {out_path} ({len(df)} rows)")
    return df


def main():
    print("=" * 65)
    print("  CHHAON — AUTOMATED PUNE INGESTION PIPELINE (v3)")
    print("=" * 65)
    grid_gdf, boundary_gdf = step1_boundary_and_grid()
    grid_fc = ee.FeatureCollection(json.loads(grid_gdf.to_json()))
    boundary_fc = ee.FeatureCollection(json.loads(boundary_gdf.to_json()))

    df_lst = step2_modis_lst(grid_fc)
    df_suhii = step3_rural_reference_and_suhii(df_lst, boundary_fc)
    df_lc = step4_land_cover(grid_fc)
    df_s2 = step5_sentinel2_indices(grid_fc)
    df_gv = step6_ghsl_and_viirs(grid_fc)
    step7_era5_and_assemble(df_suhii, df_lc, df_s2, df_gv, grid_fc)
    print("\n" + "=" * 65)
    print("  PUNE PIPELINE COMPLETE")
    print("=" * 65)


if __name__ == "__main__":
    main()
