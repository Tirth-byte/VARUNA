"""Compute and record traceable validation benchmarks and exposure analyses for Nepal Experiment."""

import json
from datetime import datetime, timezone
from pathlib import Path
import geopandas as gpd
import pandas as pd
import pyproj
from shapely.geometry import box
import rasterio
from rasterio.mask import mask
import numpy as np

geod = pyproj.Geod(ellps="WGS84")

job_dir = Path("data/experiments/nepal_aug2026/2ed78818-f3c5-40de-aeea-9647dc7a68ee")
results_dir = job_dir / "results"
ref_dir = Path("data/reference/emsr927")
infra_dir = Path("data/infrastructure")

# Load classification raster
raster_path = results_dir / "flood_change_classification.tif"
cand_path = results_dir / "candidate_hazard_polygons.geojson"

print("1. Computing independent validation against Copernicus EMSR927...")
val_results = {
    "reference_activation": "Copernicus EMS EMSR927 (GLOF & Flash Flood in Nepal)",
    "reference_citation": "European Commission Copernicus Emergency Management Service Rapid Mapping (Activation EMSR927, GDACS FL1104124)",
    "evaluation_timestamp": datetime.now(timezone.utc).isoformat(),
    "sar_observation_pair": {
        "pre_event": "2026-08-24T00:18:44 UTC (S1D_IW_GRDH_1SDV_20260824T001844...)",
        "post_event": "2026-09-05T00:18:44 UTC (S1D_IW_GRDH_1SDV_20260905T001844...)",
        "orbit": "Relative Orbit 19 (DESCENDING, VV)",
        "temporal_lag_from_peak_days": 10.0,
    },
    "spatial_coverage_evaluation": {},
    "aoi_evaluations": {},
    "methodological_caveats": [
        "Sensor disparity: Copernicus EMS EMSR927 utilized 0.3m optical WorldView-3 / Pleiades imagery capturing high-water debris/scour lines, whereas Sentinel-1 is 10m C-band SAR capturing standing surface water specular reflection.",
        "Hydrologic recession lag: Post-event SAR was acquired 10 days post-peak (Sept 5 vs Aug 26). In steep Himalayan gorges, torrential riverine flood pulses drain rapidly, leaving dry scour or muddy banks by Day 10.",
        "Radar geometry: Mountain flanks in the Trishuli gorge introduce layover and shadow. Backscatter drops represent smooth surfaces (water/mud), while backscatter increases represent coarsened debris/sediment deposition."
    ]
}

with rasterio.open(raster_path) as src:
    aoi_sar = box(*src.bounds)
    
    for aoi_id in ["AOI01", "AOI02", "AOI03", "AOI05"]:
        aoi_shp = list((ref_dir / aoi_id).glob("*areaOfInterestA*.shp"))[0]
        gdf_aoi = gpd.read_file(aoi_shp)
        aoi_poly = gdf_aoi.geometry.iloc[0]
        inter = aoi_poly.intersection(aoi_sar)
        overlap_pct = float((inter.area / aoi_poly.area) * 100)
        locality = str(gdf_aoi.get("locality", ["N/A"]).iloc[0])
        
        val_results["spatial_coverage_evaluation"][aoi_id] = {
            "locality": locality,
            "aoi_area_deg2": float(aoi_poly.area),
            "sar_grid_overlap_percent": round(overlap_pct, 2),
            "appropriate_for_benchmark": overlap_pct > 99.0
        }
        
        if overlap_pct > 99.0:
            event_shp = list((ref_dir / aoi_id).glob("*observedEventA*.shp"))[0]
            gdf_event = gpd.read_file(event_shp)
            
            # Mask to AOI
            aoi_img, _ = mask(src, [aoi_poly], crop=True)
            cls_aoi = aoi_img[1]
            tot_aoi_px = int(np.sum(cls_aoi > 0))
            water_aoi = int(np.sum(cls_aoi == 2))
            debris_aoi = int(np.sum(cls_aoi == 3))
            perm_aoi = int(np.sum(cls_aoi == 4))
            nochange_aoi = int(np.sum(cls_aoi == 1))
            
            # Mask to Observed Event Footprint
            ev_img, _ = mask(src, list(gdf_event.geometry), crop=True)
            cls_ev = ev_img[1]
            tot_ev_px = int(np.sum(cls_ev > 0))
            water_ev = int(np.sum(cls_ev == 2))
            debris_ev = int(np.sum(cls_ev == 3))
            perm_ev = int(np.sum(cls_ev == 4))
            nochange_ev = int(np.sum(cls_ev == 1))
            
            val_results["aoi_evaluations"][aoi_id] = {
                "locality": locality,
                "total_aoi_evaluated_pixels": tot_aoi_px,
                "total_aoi_evaluated_area_km2": round((tot_aoi_px * 87.920139) / 1e6, 4),
                "aoi_sar_candidate_water_pixels": water_aoi,
                "aoi_sar_candidate_water_km2": round((water_aoi * 87.920139) / 1e6, 4),
                "aoi_sar_candidate_debris_pixels": debris_aoi,
                "aoi_sar_candidate_debris_km2": round((debris_aoi * 87.920139) / 1e6, 4),
                "emsr927_observed_event_pixels": tot_ev_px,
                "emsr927_observed_event_area_km2": round((tot_ev_px * 87.920139) / 1e6, 4),
                "sar_water_inside_event_pixels": water_ev,
                "sar_water_inside_event_km2": round((water_ev * 87.920139) / 1e6, 4),
                "sar_water_inside_event_percent": round((water_ev / max(tot_ev_px, 1)) * 100, 2),
                "sar_debris_inside_event_pixels": debris_ev,
                "sar_debris_inside_event_km2": round((debris_ev * 87.920139) / 1e6, 4),
                "sar_debris_inside_event_percent": round((debris_ev / max(tot_ev_px, 1)) * 100, 2),
                "sar_total_anomaly_inside_event_percent": round(((water_ev + debris_ev) / max(tot_ev_px, 1)) * 100, 2),
                "sar_no_change_inside_event_percent": round((nochange_ev / max(tot_ev_px, 1)) * 100, 2),
            }

val_path = results_dir / "independent_validation_emsr927.json"
with open(val_path, "w") as f:
    json.dump(val_results, f, indent=2)
print(f"Saved validation benchmark to {val_path}")

print("2. Computing infrastructure exposure analysis...")
gdf_cand = gpd.read_file(cand_path)
gdf_water = gdf_cand[gdf_cand["is_candidate_flood"] == True]
gdf_debris = gdf_cand[gdf_cand["is_candidate_debris"] == True]

# Surveyed Buildings
bldg_shps = list(ref_dir.rglob("*builtUpP*.shp"))
gdf_bldgs = pd.concat([gpd.read_file(p) for p in bldg_shps], ignore_index=True)
gdf_bldgs = gpd.GeoDataFrame(gdf_bldgs, crs="EPSG:4326")
gdf_bldgs = gdf_bldgs[gdf_bldgs.geometry.notnull() & ~gdf_bldgs.geometry.is_empty]

water_bldgs = set(gpd.sjoin(gdf_bldgs, gdf_water[["geometry"]], how="inner", predicate="intersects").index)
debris_bldgs = set(gpd.sjoin(gdf_bldgs, gdf_debris[["geometry"]], how="inner", predicate="intersects").index)
exposed_bldgs = water_bldgs.union(debris_bldgs)

# Surveyed Roads
road_shps = list(ref_dir.rglob("*transportationL*.shp"))
gdf_roads = pd.concat([gpd.read_file(p) for p in road_shps], ignore_index=True)
gdf_roads = gpd.GeoDataFrame(gdf_roads, crs="EPSG:4326")
gdf_roads = gdf_roads[gdf_roads.geometry.notnull() & ~gdf_roads.geometry.is_empty]

def safe_geom_len(g):
    try:
        return float(geod.geometry_length(g))
    except:
        return 0.0

total_road_length_m = sum(safe_geom_len(g) for g in gdf_roads.geometry)

roads_water = gpd.overlay(gdf_roads, gdf_water[["geometry"]], how="intersection")
roads_debris = gpd.overlay(gdf_roads, gdf_debris[["geometry"]], how="intersection")
water_road_m = sum(safe_geom_len(g) for g in roads_water.geometry)
debris_road_m = sum(safe_geom_len(g) for g in roads_debris.geometry)

water_roads_idx = set(gpd.sjoin(gdf_roads, gdf_water[["geometry"]], how="inner", predicate="intersects").index)
debris_roads_idx = set(gpd.sjoin(gdf_roads, gdf_debris[["geometry"]], how="inner", predicate="intersects").index)
exposed_roads_idx = water_roads_idx.union(debris_roads_idx)

# Major Highways
shp_hw = infra_dir / "major_roads/npl_majrdsl_gist.shp"
gdf_hw = gpd.read_file(shp_hw)
aoi_box = box(85.10, 27.90, 85.35, 28.20)
gdf_hw_aoi = gdf_hw[gdf_hw.geometry.intersects(aoi_box)].copy()
total_hw_m = sum(safe_geom_len(g) for g in gdf_hw_aoi.geometry)
hw_water = gpd.overlay(gdf_hw_aoi, gdf_water[["geometry"]], how="intersection")
hw_debris = gpd.overlay(gdf_hw_aoi, gdf_debris[["geometry"]], how="intersection")
hw_water_m = sum(safe_geom_len(g) for g in hw_water.geometry)
hw_debris_m = sum(safe_geom_len(g) for g in hw_debris.geometry)

exposure_results = {
    "exposure_definition_disclaimer": "All exposure metrics represent POTENTIAL exposure derived from satellite hazard intersection. They do NOT confirm structural damage or impassability without ground inspection.",
    "dataset_sources": [
        "European Commission Copernicus EMS Activation EMSR927 surveyed structures",
        "Nepal Survey Department / GIST Major Road Network",
        "Sentinel-1 SAR C-band bitemporal change classification"
    ],
    "building_exposure": {
        "total_surveyed_buildings": len(gdf_bldgs),
        "potential_flood_exposure_count": len(water_bldgs),
        "potential_flood_exposure_percent": round(len(water_bldgs) / len(gdf_bldgs) * 100, 2),
        "potential_debris_exposure_count": len(debris_bldgs),
        "potential_debris_exposure_percent": round(len(debris_bldgs) / len(gdf_bldgs) * 100, 2),
        "total_potential_exposure_count": len(exposed_bldgs),
        "total_potential_exposure_percent": round(len(exposed_bldgs) / len(gdf_bldgs) * 100, 2),
        "damage_grading_cross_tabulation": {
            "Destroyed": {
                "total": int(sum(gdf_bldgs["damage_gra"] == "Destroyed")),
                "intersecting_flood": int(sum((gdf_bldgs["damage_gra"] == "Destroyed") & gdf_bldgs.index.isin(water_bldgs))),
                "intersecting_debris": int(sum((gdf_bldgs["damage_gra"] == "Destroyed") & gdf_bldgs.index.isin(debris_bldgs))),
                "intersecting_any_anomaly": int(sum((gdf_bldgs["damage_gra"] == "Destroyed") & gdf_bldgs.index.isin(exposed_bldgs))),
                "no_anomaly": int(sum((gdf_bldgs["damage_gra"] == "Destroyed") & ~gdf_bldgs.index.isin(exposed_bldgs))),
            },
            "Damaged": {
                "total": int(sum(gdf_bldgs["damage_gra"] == "Damaged")),
                "intersecting_flood": int(sum((gdf_bldgs["damage_gra"] == "Damaged") & gdf_bldgs.index.isin(water_bldgs))),
                "intersecting_debris": int(sum((gdf_bldgs["damage_gra"] == "Damaged") & gdf_bldgs.index.isin(debris_bldgs))),
                "intersecting_any_anomaly": int(sum((gdf_bldgs["damage_gra"] == "Damaged") & gdf_bldgs.index.isin(exposed_bldgs))),
                "no_anomaly": int(sum((gdf_bldgs["damage_gra"] == "Damaged") & ~gdf_bldgs.index.isin(exposed_bldgs))),
            },
            "Possibly damaged": {
                "total": int(sum(gdf_bldgs["damage_gra"] == "Possibly damaged")),
                "intersecting_flood": int(sum((gdf_bldgs["damage_gra"] == "Possibly damaged") & gdf_bldgs.index.isin(water_bldgs))),
                "intersecting_debris": int(sum((gdf_bldgs["damage_gra"] == "Possibly damaged") & gdf_bldgs.index.isin(debris_bldgs))),
                "intersecting_any_anomaly": int(sum((gdf_bldgs["damage_gra"] == "Possibly damaged") & gdf_bldgs.index.isin(exposed_bldgs))),
                "no_anomaly": int(sum((gdf_bldgs["damage_gra"] == "Possibly damaged") & ~gdf_bldgs.index.isin(exposed_bldgs))),
            }
        }
    },
    "road_exposure": {
        "surveyed_network": {
            "total_segments": len(gdf_roads),
            "total_length_km": round(total_road_length_m / 1e3, 2),
            "potential_flood_exposure_length_km": round(water_road_m / 1e3, 2),
            "potential_flood_exposure_percent": round((water_road_m / total_road_length_m) * 100, 2),
            "potential_debris_exposure_length_km": round(debris_road_m / 1e3, 2),
            "potential_debris_exposure_percent": round((debris_road_m / total_road_length_m) * 100, 2),
            "total_exposed_length_km": round((water_road_m + debris_road_m) / 1e3, 2),
            "total_exposed_percent": round(((water_road_m + debris_road_m) / total_road_length_m) * 100, 2),
            "segments_exposed_count": len(exposed_roads_idx),
            "segments_exposed_percent": round(len(exposed_roads_idx) / len(gdf_roads) * 100, 2),
        },
        "major_highway_corridor_pasang_lhamu": {
            "total_corridor_length_in_aoi_km": round(total_hw_m / 1e3, 2),
            "potential_flood_exposure_km": round(hw_water_m / 1e3, 2),
            "potential_debris_exposure_km": round(hw_debris_m / 1e3, 2),
            "total_exposed_corridor_km": round((hw_water_m + hw_debris_m) / 1e3, 2),
            "total_exposed_corridor_percent": round(((hw_water_m + hw_debris_m) / max(total_hw_m, 1)) * 100, 2)
        }
    }
}

exp_path = results_dir / "infrastructure_exposure_analysis.json"
with open(exp_path, "w") as f:
    json.dump(exposure_results, f, indent=2)
print(f"Saved infrastructure exposure analysis to {exp_path}")
