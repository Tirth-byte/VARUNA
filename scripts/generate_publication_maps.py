import rasterio
from rasterio.plot import show
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import numpy as np
from pathlib import Path

out_dir = Path("data/demo_evidence")
out_dir.mkdir(parents=True, exist_ok=True)

res_dir = Path("data/experiments/nepal_aug2026/2ed78818-f3c5-40de-aeea-9647dc7a68ee")
post_tif = res_dir / "aligned" / "aligned_post.tif"
cls_tif = res_dir / "results" / "flood_change_classification.tif"

print("Loading data for publication cartography...")
with rasterio.open(post_tif) as src_post:
    post_arr = src_post.read(1)
    post_bounds = src_post.bounds
    post_extent = [post_bounds.left, post_bounds.right, post_bounds.bottom, post_bounds.top]

with rasterio.open(cls_tif) as src_cls:
    cls_arr = src_cls.read(2) # 1=none, 2=flood, 3=debris, 4=perm water

# Grayscale contrast stretch for SAR intensity (-22 dB to +2 dB)
vmin, vmax = -22.0, 2.0
sar_norm = np.clip((post_arr - vmin) / (vmax - vmin), 0.0, 1.0)
# Nodata mask
sar_norm[post_arr <= -9000] = np.nan

# Vector layers
gdf_emsr = gpd.read_file("dashboard/layers/emsr927_event_extents.geojson")
gdf_bldgs = gpd.read_file("dashboard/layers/exposed_buildings_dashboard.geojson")
gdf_roads = gpd.read_file("dashboard/layers/exposed_roads_dashboard.geojson")
gdf_hw = gpd.read_file("dashboard/layers/major_highways_trishuli.geojson")

print("1. Rendering Map 1: Trishuli Regional Overview Publication Map...")
fig, ax = plt.subplots(figsize=(12, 14), dpi=300, facecolor="#F7F8F6")
ax.set_facecolor("#182521")

# Show SAR intensity background
ax.imshow(sar_norm, cmap="gray", extent=post_extent, origin="upper", zorder=1)

# Build RGBA hazard mask for regional view
h, w = cls_arr.shape
hazard_rgba = np.zeros((h, w, 4), dtype=np.float32)
# Candidate floodwater (Code 2): #1D63B8 (29, 99, 184), alpha=0.75
hazard_rgba[cls_arr == 2] = [29/255, 99/255, 184/255, 0.75]
# Candidate debris (Code 3): #C2611B (194, 97, 27), alpha=0.75
hazard_rgba[cls_arr == 3] = [194/255, 97/255, 27/255, 0.75]

ax.imshow(hazard_rgba, extent=post_extent, origin="upper", zorder=2)

# Overlay Copernicus EMSR927 footprint
gdf_emsr.plot(ax=ax, facecolor="none", edgecolor="#A855F7", linewidth=1.8, linestyle="--", zorder=4)

# Overlay Pasang Lhamu Highway
gdf_hw.plot(ax=ax, color="#0D9488", linewidth=2.4, zorder=5)

# Formatting axes
ax.set_xlim(85.05, 85.40)
ax.set_ylim(27.85, 28.25)
ax.set_xlabel("Longitude (°E)", fontsize=10, fontweight="600", color="#182521")
ax.set_ylabel("Latitude (°N)", fontsize=10, fontweight="600", color="#182521")
ax.tick_params(colors="#182521", labelsize=9)
for spine in ax.spines.values():
    spine.set_color("#CBD5E1")
    spine.set_linewidth(1.2)
ax.grid(color="#E2E8F0", linestyle=":", linewidth=0.6, alpha=0.6)

# Scale Bar (approx 10 km at latitude 28° is ~0.102 degrees)
scale_lon = 85.08
scale_lat = 27.87
km10_deg = 10.0 / (111.32 * np.cos(np.radians(28.05)))
ax.plot([scale_lon, scale_lon + km10_deg], [scale_lat, scale_lat], color="#FFFFFF", linewidth=3.5, solid_capstyle="butt", zorder=10)
ax.plot([scale_lon, scale_lon + km10_deg], [scale_lat, scale_lat], color="#182521", linewidth=2.0, solid_capstyle="butt", zorder=11)
ax.text(scale_lon + km10_deg / 2, scale_lat + 0.006, "10 km", color="#FFFFFF", fontsize=9, fontweight="700", ha="center",
        bbox=dict(boxstyle="round,pad=0.2", facecolor="#182521", edgecolor="none", alpha=0.85), zorder=12)

# North Indicator
ax.text(85.37, 28.22, "▲\nN", color="#182521", fontsize=11, fontweight="800", ha="center",
        bbox=dict(boxstyle="circle,pad=0.3", facecolor="#FFFFFF", edgecolor="#CBD5E1", alpha=0.9), zorder=10)

# Title Header & Attribution Box
title_text = (
    "VARUNA — Trishuli River Valley Flood & Surface Change Assessment\n"
    "Sentinel-1 C-SAR Change (2026-08-24 to 2026-09-05) & Copernicus EMS EMSR927"
)
ax.text(0.02, 0.96, title_text, transform=ax.transAxes, fontsize=12, fontweight="800", color="#0F172A",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#FFFFFF", edgecolor="#CBD5E1", alpha=0.95), zorder=20)

meta_text = (
    "Observation Telemetry:\n"
    "• Sensor: Sentinel-1 C-band SAR (Level-1 GRD IW, VV)\n"
    "• Pre-Event: 2026-08-24 00:18:44 UTC (2d pre-event)\n"
    "• Post-Event: 2026-09-05 00:18:44 UTC (10d post-event)\n"
    "• Repeat Pass: Orbit 19 Descending (12.0d baseline)\n"
    "• Terrain Correction: ESA SNAP 10 + Copernicus 30m DEM\n"
    "• Grid Bounds: 85.05°E–85.40°E, 27.85°N–28.25°N (1,526 km²)\n"
    "• Spatial Alignment: 100.0% Valid Overlap (0 NoData px)"
)
ax.text(0.02, 0.77, meta_text, transform=ax.transAxes, fontsize=8, color="#334155",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#FFFFFF", edgecolor="#E2E8F0", alpha=0.92), zorder=20)

caveat_text = (
    "Scientific Caveats & Provenance:\n"
    "1. Candidate Inundation: Radar specular drop (Δσ° ≤ -3.5 dB). In steep\n"
    "   mountain gorges, flash floods recede in 24–48h; Day 10 SAR detects\n"
    "   persistent standing water, widened channels & saturated gravel bars.\n"
    "2. Candidate Debris: Radar coarsening (Δσ° ≥ +3.5 dB) from debris/scour.\n"
    "3. Auxiliary shadow bands omitted during dB export (0 px shadow suspect);\n"
    "   slopes >25° require optical confirmation."
)
ax.text(0.02, 0.05, caveat_text, transform=ax.transAxes, fontsize=7.5, color="#475569",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#FFFBF5", edgecolor="#F3E4D1", alpha=0.95), zorder=20)

# Legend
legend_elements = [
    mpatches.Patch(facecolor="#1D63B8", edgecolor="none", label="Candidate Flood Inundation (126.60 km², 8.30%)"),
    mpatches.Patch(facecolor="#C2611B", edgecolor="none", label="Candidate Surface Debris / Roughening (108.21 km², 7.09%)"),
    Line2D([0], [0], color="#0D9488", lw=2.5, label="Pasang Lhamu Highway Corridor (57.95 km within AOI)"),
    Line2D([0], [0], color="#A855F7", lw=2, ls="--", label="Copernicus EMS EMSR927 Surveyed Disaster Footprint"),
]
ax.legend(handles=legend_elements, loc="lower right", fontsize=8.5, framealpha=0.95, facecolor="#FFFFFF", edgecolor="#CBD5E1")

plt.tight_layout()
map1_path = out_dir / "map_1_trishuli_regional_overview_publication.png"
plt.savefig(map1_path, dpi=300)
plt.close()
print(f"Saved {map1_path} ({round(map1_path.stat().st_size / 1e6, 2)} MB)")


print("2. Rendering Map 2: Detailed Bidur Impact and Validation Map...")
fig, ax = plt.subplots(figsize=(12, 14), dpi=300, facecolor="#F7F8F6")
ax.set_facecolor("#182521")

# Crop to Bidur Confluence (AOI03)
bidur_xlim = (85.10, 85.20)
bidur_ylim = (27.85, 28.01)

# Display SAR intensity
ax.imshow(sar_norm, cmap="gray", extent=post_extent, origin="upper", zorder=1)
ax.imshow(hazard_rgba, extent=post_extent, origin="upper", zorder=2)

# Overlay Roads
gdf_roads_bidur = gdf_roads[gdf_roads.geometry.intersects(gpd.GeoSeries.from_wkt([f"POLYGON(({bidur_xlim[0]} {bidur_ylim[0]}, {bidur_xlim[1]} {bidur_ylim[0]}, {bidur_xlim[1]} {bidur_ylim[1]}, {bidur_xlim[0]} {bidur_ylim[1]}, {bidur_xlim[0]} {bidur_ylim[0]}))"]).iloc[0])]
gdf_roads_bidur.plot(ax=ax, color="#64748B", linewidth=1.2, alpha=0.7, zorder=3)

# Highlight exposed roads
roads_flood = gdf_roads_bidur[gdf_roads_bidur["potential_exposure"].str.contains("FLOOD", na=False)]
roads_debris = gdf_roads_bidur[gdf_roads_bidur["potential_exposure"].str.contains("DEBRIS", na=False)]
if not roads_flood.empty:
    roads_flood.plot(ax=ax, color="#38BDF8", linewidth=2.0, zorder=4)
if not roads_debris.empty:
    roads_debris.plot(ax=ax, color="#F59E0B", linewidth=2.0, zorder=4)

# Overlay Copernicus EMSR927 footprint
gdf_emsr.plot(ax=ax, facecolor="#A855F7", alpha=0.18, edgecolor="#A855F7", linewidth=2.2, linestyle="--", zorder=5)

# Overlay Pasang Lhamu Highway
gdf_hw.plot(ax=ax, color="#0D9488", linewidth=3.0, zorder=6)

# Overlay Buildings by damage grade
gdf_bldgs_bidur = gdf_bldgs[gdf_bldgs.geometry.intersects(gpd.GeoSeries.from_wkt([f"POLYGON(({bidur_xlim[0]} {bidur_ylim[0]}, {bidur_xlim[1]} {bidur_ylim[0]}, {bidur_xlim[1]} {bidur_ylim[1]}, {bidur_xlim[0]} {bidur_ylim[1]}, {bidur_xlim[0]} {bidur_ylim[0]}))"]).iloc[0])]

bldgs_dest = gdf_bldgs_bidur[gdf_bldgs_bidur["damage_gra"] == "Destroyed"]
bldgs_dam = gdf_bldgs_bidur[gdf_bldgs_bidur["damage_gra"] == "Damaged"]
bldgs_pos = gdf_bldgs_bidur[gdf_bldgs_bidur["damage_gra"] == "Possibly damaged"]
bldgs_other = gdf_bldgs_bidur[~gdf_bldgs_bidur["damage_gra"].isin(["Destroyed", "Damaged", "Possibly damaged"])]

if not bldgs_other.empty:
    bldgs_other.plot(ax=ax, color="#94A3B8", markersize=8, alpha=0.6, zorder=7)
if not bldgs_pos.empty:
    bldgs_pos.plot(ax=ax, color="#EAB308", markersize=14, zorder=8)
if not bldgs_dam.empty:
    bldgs_dam.plot(ax=ax, color="#F97316", markersize=16, zorder=9)
if not bldgs_dest.empty:
    bldgs_dest.plot(ax=ax, color="#EF4444", markersize=20, edgecolor="#FFFFFF", linewidth=0.5, zorder=10)

ax.set_xlim(*bidur_xlim)
ax.set_ylim(*bidur_ylim)
ax.set_xlabel("Longitude (°E)", fontsize=10, fontweight="600", color="#182521")
ax.set_ylabel("Latitude (°N)", fontsize=10, fontweight="600", color="#182521")
ax.tick_params(colors="#182521", labelsize=9)
for spine in ax.spines.values():
    spine.set_color("#CBD5E1")
    spine.set_linewidth(1.2)
ax.grid(color="#E2E8F0", linestyle=":", linewidth=0.6, alpha=0.6)

# Scale Bar (2 km at lat 27.93° is ~0.0207 degrees)
scale_lon = 85.11
scale_lat = 27.86
km2_deg = 2.0 / (111.32 * np.cos(np.radians(27.93)))
ax.plot([scale_lon, scale_lon + km2_deg], [scale_lat, scale_lat], color="#FFFFFF", linewidth=3.5, solid_capstyle="butt", zorder=15)
ax.plot([scale_lon, scale_lon + km2_deg], [scale_lat, scale_lat], color="#182521", linewidth=2.0, solid_capstyle="butt", zorder=16)
ax.text(scale_lon + km2_deg / 2, scale_lat + 0.0025, "2 km", color="#FFFFFF", fontsize=9, fontweight="700", ha="center",
        bbox=dict(boxstyle="round,pad=0.2", facecolor="#182521", edgecolor="none", alpha=0.85), zorder=17)

# North Indicator
ax.text(85.19, 28.00, "▲\nN", color="#182521", fontsize=11, fontweight="800", ha="center",
        bbox=dict(boxstyle="circle,pad=0.3", facecolor="#FFFFFF", edgecolor="#CBD5E1", alpha=0.9), zorder=15)

# Title Block
title_bidur = (
    "Detail Assessment: Bidur / Battar Confluence (AOI03)\n"
    "SAR Hazard Anomalies vs Copernicus EMSR927 Surveyed Damage"
)
ax.text(0.02, 0.96, title_bidur, transform=ax.transAxes, fontsize=12, fontweight="800", color="#0F172A",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#FFFFFF", edgecolor="#CBD5E1", alpha=0.95), zorder=20)

val_stats_text = (
    "Copernicus EMSR927 Validation Benchmark:\n"
    "• Evaluated Sector Area: 20.93 km² (238,100 px)\n"
    "• Optical Event Footprint: 5.89 km² (66,959 px)\n"
    "• SAR Flood Water in Event: 1.58 km² (18,002 px, 26.89%)\n"
    "• SAR Debris in Event: 0.61 km² (6,883 px, 10.28%)\n"
    "• Total SAR Anomaly Capture: 37.16% (24,885 of 66,959 px)\n"
    "• Metric Definition: Observed-event spatial coincidence\n"
    "  (10-day recession lag); not algorithmic precision/recall."
)
ax.text(0.02, 0.77, val_stats_text, transform=ax.transAxes, fontsize=8, color="#334155",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#FFFFFF", edgecolor="#E2E8F0", alpha=0.95), zorder=20)

exposure_box = (
    "Infrastructure Exposure in Sector:\n"
    "• Surveyed Buildings: 3,816 total structures\n"
    "• Destroyed Structures (EMSR927): 2,813 total\n"
    "  └ Intersecting SAR Anomalies: 936 (33.27%)\n"
    "• Pasang Lhamu Highway Corridor: 9.62 km hazard crossing\n"
    "• Proximity Audit: Only 0.30 km within 50m of destroyed\n"
    "  local roads (highway follows upper bench, not riverbed tracks)."
)
ax.text(0.02, 0.05, exposure_box, transform=ax.transAxes, fontsize=7.8, color="#334155",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#FFFFFF", edgecolor="#CBD5E1", alpha=0.95), zorder=20)

# Legend
bidur_legends = [
    Line2D([0], [0], color="#A855F7", lw=2, ls="--", label="Copernicus EMSR927 Event Footprint (5.89 km²)"),
    mpatches.Patch(facecolor="#1D63B8", edgecolor="none", label="SAR Candidate Flood Inundation (Δσ° ≤ -3.5 dB)"),
    mpatches.Patch(facecolor="#C2611B", edgecolor="none", label="SAR Candidate Surface Debris (Δσ° ≥ +3.5 dB)"),
    Line2D([0], [0], color="#0D9488", lw=3.0, label="Pasang Lhamu National Highway"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor="#EF4444", markersize=8, label="Surveyed Building: Destroyed"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor="#F97316", markersize=7, label="Surveyed Building: Damaged"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor="#EAB308", markersize=6, label="Surveyed Building: Possibly Damaged"),
]
ax.legend(handles=bidur_legends, loc="lower right", fontsize=8, framealpha=0.95, facecolor="#FFFFFF", edgecolor="#CBD5E1")

plt.tight_layout()
map2_path = out_dir / "map_2_bidur_impact_validation_publication.png"
plt.savefig(map2_path, dpi=300)
plt.close()
print(f"Saved {map2_path} ({round(map2_path.stat().st_size / 1e6, 2)} MB)")
