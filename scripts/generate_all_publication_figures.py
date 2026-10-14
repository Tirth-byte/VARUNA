#!/usr/bin/env python3
"""
VARUNA — Publication-Grade Scientific Cartography & Figure Generator
Generates the four high-resolution figures for the academic research paper:
  - Figure 1: Study Area and Geographic Context (Trishuli River Basin, Nepal)
  - Figure 2: Sentinel-1 Pre-Event (Aug 24) and Post-Event (Sept 5) SAR Comparison
  - Figure 3: SAR Surface Change Classification (Candidate Flood, Debris, Baseline Water)
  - Figure 4: Copernicus EMSR927 Reference Validation (Bidur Confluence AOI03)

Strictly calibrated for exact PDF display geometry (zero distortion, >=300 DPI, academic typography).
"""

import os
from pathlib import Path
import numpy as np
import rasterio
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D

# Set up matplotlib style for academic publication
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif", "Liberation Serif"],
    "mathtext.fontset": "stix",
    "axes.edgecolor": "#334155",
    "axes.linewidth": 0.8,
    "xtick.major.width": 0.8,
    "ytick.major.width": 0.8,
    "xtick.direction": "out",
    "ytick.direction": "out",
})

ROOT_DIR = Path(__file__).resolve().parent.parent
FIGURES_DIR = ROOT_DIR / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
DEMO_DIR = ROOT_DIR / "data" / "demo_evidence"
DEMO_DIR.mkdir(parents=True, exist_ok=True)

EXP_DIR = ROOT_DIR / "data" / "experiments" / "nepal_aug2026" / "2ed78818-f3c5-40de-aeea-9647dc7a68ee"
PRE_TIF = EXP_DIR / "aligned" / "aligned_pre.tif"
POST_TIF = EXP_DIR / "aligned" / "aligned_post.tif"
CLS_TIF = EXP_DIR / "results" / "flood_change_classification.tif"

EMSR_GEOJSON = ROOT_DIR / "dashboard" / "layers" / "emsr927_event_extents.geojson"
HW_GEOJSON = ROOT_DIR / "dashboard" / "layers" / "major_highways_trishuli.geojson"
ROADS_GEOJSON = ROOT_DIR / "dashboard" / "layers" / "exposed_roads_dashboard.geojson"
BLDGS_GEOJSON = ROOT_DIR / "dashboard" / "layers" / "exposed_buildings_dashboard.geojson"
WATER_GEOJSON = ROOT_DIR / "dashboard" / "layers" / "candidate_water_dashboard.geojson"


def add_north_arrow(ax, x=0.91, y=0.91, fontsize=8):
    """Draw a clean publication-style north arrow."""
    ax.annotate(
        "N",
        xy=(x, y),
        xytext=(x, y - 0.055),
        xycoords="axes fraction",
        ha="center",
        va="center",
        fontsize=fontsize,
        fontweight="bold",
        color="#0F172A",
        arrowprops=dict(
            facecolor="#0F172A",
            edgecolor="#0F172A",
            width=1.2,
            headwidth=5.0,
            headlength=5.0,
            shrink=0.05,
        ),
        zorder=35,
        bbox=dict(boxstyle="circle,pad=0.22", facecolor="#FFFFFF", edgecolor="#CBD5E1", alpha=0.95, lw=0.6),
    )


def add_scale_bar(ax, lon, lat, length_km=10.0, label="10 km", text_offset=0.005, fontsize=7.5):
    """Draw a high-contrast publication scale bar."""
    km_deg = length_km / (111.32 * np.cos(np.radians(lat)))
    # Outer white halo
    ax.plot([lon, lon + km_deg], [lat, lat], color="#FFFFFF", linewidth=4.0, solid_capstyle="butt", zorder=25)
    # Inner dark line
    ax.plot([lon, lon + km_deg], [lat, lat], color="#0F172A", linewidth=2.0, solid_capstyle="butt", zorder=26)
    # Ticks
    ax.plot([lon, lon], [lat - 0.002, lat + 0.002], color="#0F172A", linewidth=1.5, zorder=26)
    ax.plot([lon + km_deg, lon + km_deg], [lat - 0.002, lat + 0.002], color="#0F172A", linewidth=1.5, zorder=26)
    ax.text(
        lon + km_deg / 2,
        lat + text_offset,
        label,
        color="#0F172A",
        fontsize=fontsize,
        fontweight="bold",
        ha="center",
        va="bottom",
        bbox=dict(boxstyle="round,pad=0.15", facecolor="#FFFFFF", edgecolor="#CBD5E1", alpha=0.95, lw=0.5),
        zorder=27,
    )


def generate_figure1():
    """
    Figure 1: Study Area and Geographic Context (Trishuli River Basin, Nepal).
    Slot: 225 x 225 pt (1:1 ratio).
    """
    print("\n[Figure 1] Rendering Study Area and Geographic Context Map...")
    with rasterio.open(POST_TIF) as src:
        post_arr = src.read(1)
        bounds = src.bounds
        extent = [bounds.left, bounds.right, bounds.bottom, bounds.top]

    vmin, vmax = -22.0, 2.0
    sar_norm = np.clip((post_arr - vmin) / (vmax - vmin), 0.0, 1.0)
    sar_norm[post_arr <= -9000] = np.nan

    gdf_emsr = gpd.read_file(EMSR_GEOJSON)
    gdf_hw = gpd.read_file(HW_GEOJSON)
    gdf_water = gpd.read_file(WATER_GEOJSON)

    # 4.5 x 4.5 inches at 500 DPI = 2250 x 2250 px (Exact 1:1 aspect ratio)
    fig, ax = plt.subplots(figsize=(4.5, 4.5), dpi=500, facecolor="#FFFFFF")
    ax.set_facecolor("#F8FAFC")

    # Display shaded SAR terrain backdrop
    ax.imshow(sar_norm, cmap="gray", extent=extent, origin="upper", alpha=0.45, zorder=1)

    # Trishuli River channel geometry
    gdf_water.plot(ax=ax, color="#0284C7", linewidth=0.7, alpha=0.75, zorder=3)

    # Analysis Grid Boundary (1,526.05 km²)
    cag_rect = mpatches.Rectangle(
        (85.05, 27.85),
        85.40 - 85.05,
        28.25 - 27.85,
        fill=False,
        edgecolor="#0F766E",
        linewidth=1.8,
        linestyle="--",
        zorder=10,
        label="Common Analysis Grid (1,526.05 km²)",
    )
    ax.add_patch(cag_rect)

    # Copernicus EMSR927 Survey AOIs
    gdf_emsr.plot(
        ax=ax,
        facecolor="#C084FC",
        alpha=0.30,
        edgecolor="#7E22CE",
        linewidth=1.0,
        linestyle="-",
        zorder=11,
    )

    # Pasang Lhamu National Highway Lifeline
    gdf_hw.plot(
        ax=ax,
        color="#B45309",
        linewidth=1.8,
        zorder=12,
    )

    # Key Settlements & Critical Hubs
    settlements = [
        ("Timure Border (AOI02)", 85.378, 28.232, "top left"),
        ("Syapru Besi (AOI01)", 85.340, 28.160, "right"),
        ("Dhunche (District HQ)", 85.295, 28.115, "right"),
        ("Mailung / Betrawati", 85.185, 28.025, "left"),
        ("Bidur / Battar (AOI03)", 85.155, 27.918, "left"),
    ]

    for name, lon, lat, pos in settlements:
        ax.plot(lon, lat, marker="o", color="#DC2626", markersize=4.5, markeredgecolor="#FFFFFF", markeredgewidth=0.6, zorder=20)
        ha = "left" if "right" in pos else ("right" if "left" in pos else "center")
        offset_x = 0.007 if ha == "left" else (-0.007 if ha == "right" else 0.0)
        offset_y = 0.006 if "top" in pos else 0.0
        ax.text(
            lon + offset_x,
            lat + offset_y,
            name,
            fontsize=6.5,
            fontweight="bold",
            color="#0F172A",
            ha=ha,
            va="center",
            bbox=dict(boxstyle="round,pad=0.18", facecolor="#FFFFFF", edgecolor="#CBD5E1", alpha=0.92, lw=0.4),
            zorder=21,
        )

    # Framing
    ax.set_xlim(85.04, 85.41)
    ax.set_ylim(27.84, 28.26)
    ax.set_xlabel("Longitude (°E)", fontsize=7.5, fontweight="bold", color="#1E293B", labelpad=2)
    ax.set_ylabel("Latitude (°N)", fontsize=7.5, fontweight="bold", color="#1E293B", labelpad=2)
    ax.tick_params(labelsize=6.5, colors="#334155", pad=2)
    ax.grid(color="#CBD5E1", linestyle=":", linewidth=0.5, alpha=0.6)

    # Scale bar and North arrow
    add_scale_bar(ax, 85.06, 27.855, length_km=10.0, label="10 km", text_offset=0.005, fontsize=6.5)
    add_north_arrow(ax, x=0.91, y=0.91, fontsize=7.5)

    # Legend
    legend_handles = [
        Line2D([0], [0], color="#0F766E", lw=1.6, ls="--", label="Analysis Grid (1,526 km²)"),
        Line2D([0], [0], color="#B45309", lw=1.8, label="Pasang Lhamu Highway (H04)"),
        Line2D([0], [0], color="#0284C7", lw=1.5, label="Trishuli River Corridor"),
        mpatches.Patch(facecolor="#C084FC", edgecolor="#7E22CE", alpha=0.5, label="EMSR927 Survey AOIs"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#DC2626", markersize=4.5, label="Key Settlement / Hub"),
    ]
    ax.legend(handles=legend_handles, loc="lower right", fontsize=6.0, framealpha=0.95, facecolor="#FFFFFF", edgecolor="#CBD5E1", borderpad=0.3, labelspacing=0.25)

    # Title Banner
    ax.text(
        0.02,
        0.965,
        "Trishuli River Basin: Study Area & Emergency Extents\nRasuwa & Nuwakot Districts, Central Nepal (Aug 2026)",
        transform=ax.transAxes,
        fontsize=6.8,
        fontweight="bold",
        color="#0F172A",
        va="top",
        bbox=dict(boxstyle="round,pad=0.25", facecolor="#FFFFFF", edgecolor="#CBD5E1", alpha=0.95, lw=0.5),
        zorder=30,
    )

    plt.subplots_adjust(left=0.12, right=0.97, bottom=0.10, top=0.97)
    out_path = FIGURES_DIR / "figure1_study_area_context.png"
    plt.savefig(out_path, dpi=500)
    plt.savefig(DEMO_DIR / "fig_study_area_context.png", dpi=500)
    plt.close()
    print(f"  -> Generated {out_path} ({round(out_path.stat().st_size / 1e3, 1)} KB)")


def generate_figure2():
    """
    Figure 2: Sentinel-1 Pre-Event and Post-Event Radar Intensity Comparison.
    Slot: 349.4929 x 170 pt (exact ratio: 2.0558406).
    """
    print("\n[Figure 2] Rendering Sentinel-1 Pre and Post Comparison (Matched Grid)...")
    with rasterio.open(PRE_TIF) as src_pre:
        pre_arr = src_pre.read(1)
        bounds = src_pre.bounds
        extent = [bounds.left, bounds.right, bounds.bottom, bounds.top]

    with rasterio.open(POST_TIF) as src_post:
        post_arr = src_post.read(1)

    vmin, vmax = -22.0, 2.0
    pre_norm = np.clip((pre_arr - vmin) / (vmax - vmin), 0.0, 1.0)
    pre_norm[pre_arr <= -9000] = np.nan

    post_norm = np.clip((post_arr - vmin) / (vmax - vmin), 0.0, 1.0)
    post_norm[post_arr <= -9000] = np.nan

    # 8.0 x 3.89133 inches at 400 DPI = 3200 x 1557 px (Exact ratio: 2.05584)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.0, 3.89133), dpi=400, facecolor="#FFFFFF")

    # Panel 1: Pre-Event
    ax1.imshow(pre_norm, cmap="gray", extent=extent, origin="upper")
    ax1.set_xlim(85.05, 85.40)
    ax1.set_ylim(27.85, 28.25)
    ax1.set_xlabel("Longitude (°E)", fontsize=7.2, fontweight="bold", color="#1E293B", labelpad=2)
    ax1.set_ylabel("Latitude (°N)", fontsize=7.2, fontweight="bold", color="#1E293B", labelpad=2)
    ax1.tick_params(labelsize=6.5, colors="#334155", pad=2)
    ax1.grid(color="#E2E8F0", linestyle=":", linewidth=0.5, alpha=0.5)
    ax1.text(
        0.03,
        0.95,
        "(a) Pre-Event Sentinel-1 C-SAR\n2026-08-24 00:18:44 UTC (Orbit 19)",
        transform=ax1.transAxes,
        fontsize=6.8,
        fontweight="bold",
        color="#0F172A",
        va="top",
        bbox=dict(boxstyle="round,pad=0.25", facecolor="#FFFFFF", edgecolor="#CBD5E1", alpha=0.92, lw=0.4),
        zorder=10,
    )
    add_scale_bar(ax1, 85.07, 27.87, length_km=10.0, label="10 km", text_offset=0.005, fontsize=6.2)
    add_north_arrow(ax1, x=0.88, y=0.90, fontsize=7.0)

    # Panel 2: Post-Event
    ax2.imshow(post_norm, cmap="gray", extent=extent, origin="upper")
    ax2.set_xlim(85.05, 85.40)
    ax2.set_ylim(27.85, 28.25)
    ax2.set_xlabel("Longitude (°E)", fontsize=7.2, fontweight="bold", color="#1E293B", labelpad=2)
    ax2.tick_params(labelsize=6.5, colors="#334155", pad=2)
    ax2.grid(color="#E2E8F0", linestyle=":", linewidth=0.5, alpha=0.5)
    ax2.text(
        0.03,
        0.95,
        "(b) Post-Event Sentinel-1 C-SAR\n2026-09-05 00:18:44 UTC (Orbit 19)",
        transform=ax2.transAxes,
        fontsize=6.8,
        fontweight="bold",
        color="#0F172A",
        va="top",
        bbox=dict(boxstyle="round,pad=0.25", facecolor="#FFFFFF", edgecolor="#CBD5E1", alpha=0.92, lw=0.4),
        zorder=10,
    )
    add_scale_bar(ax2, 85.07, 27.87, length_km=10.0, label="10 km", text_offset=0.005, fontsize=6.2)
    add_north_arrow(ax2, x=0.88, y=0.90, fontsize=7.0)

    # Shared colorbar at the bottom
    cbar_ax = fig.add_axes([0.22, 0.08, 0.56, 0.03])
    sm = plt.cm.ScalarMappable(cmap="gray", norm=plt.Normalize(vmin=vmin, vmax=vmax))
    sm.set_array([])
    cbar = fig.colorbar(sm, cax=cbar_ax, orientation="horizontal")
    cbar.set_label("Calibrated Radar Backscatter $\\sigma^0$ (dB, Level-1 GRD IW VV)", fontsize=7.0, color="#1E293B", labelpad=1)
    cbar.ax.tick_params(labelsize=6.5, colors="#334155", pad=1)
    cbar.ax.text(0.0, -1.9, "-22 dB (Specular / Water)", transform=cbar.ax.transAxes, fontsize=6.0, ha="left", color="#475569")
    cbar.ax.text(1.0, -1.9, "+2 dB (Rough / Debris)", transform=cbar.ax.transAxes, fontsize=6.0, ha="right", color="#475569")

    fig.subplots_adjust(left=0.08, right=0.96, bottom=0.22, top=0.96, wspace=0.15)
    out_path = FIGURES_DIR / "figure2_s1_pre_post_comparison.png"
    plt.savefig(out_path, dpi=400)
    plt.savefig(DEMO_DIR / "fig_s1_pre_post_comparison.png", dpi=400)
    plt.close()
    print(f"  -> Generated {out_path} ({round(out_path.stat().st_size / 1e3, 1)} KB)")


def generate_figure3():
    """
    Figure 3: SAR Surface Change Classification (Candidate Flood, Debris, Baseline Water).
    Slot: 234.6595 x 220 pt (exact ratio: 1.066634).
    """
    print("\n[Figure 3] Rendering SAR Surface Change Classification Map...")
    with rasterio.open(POST_TIF) as src_post:
        post_arr = src_post.read(1)
        bounds = src_post.bounds
        extent = [bounds.left, bounds.right, bounds.bottom, bounds.top]

    with rasterio.open(CLS_TIF) as src_cls:
        cls_arr = src_cls.read(2)  # Band 2: 1=none, 2=flood, 3=debris, 4=perm water

    vmin, vmax = -22.0, 2.0
    sar_norm = np.clip((post_arr - vmin) / (vmax - vmin), 0.0, 1.0)
    sar_norm[post_arr <= -9000] = np.nan

    h, w = cls_arr.shape
    hazard_rgba = np.zeros((h, w, 4), dtype=np.float32)
    # Candidate floodwater (Code 2): #1D63B8 (Blue), alpha=0.88
    hazard_rgba[cls_arr == 2] = [29/255, 99/255, 184/255, 0.88]
    # Candidate debris/scour (Code 3): #D97706 (Amber/Orange), alpha=0.88
    hazard_rgba[cls_arr == 3] = [217/255, 119/255, 6/255, 0.88]
    # Permanent water baseline (Code 4): #0B2545 (Deep Navy), alpha=0.88
    hazard_rgba[cls_arr == 4] = [11/255, 37/255, 69/255, 0.88]

    gdf_emsr = gpd.read_file(EMSR_GEOJSON)
    gdf_hw = gpd.read_file(HW_GEOJSON)

    # 4.8 x 4.5 inches at 500 DPI = 2400 x 2250 px (Exact ratio: 1.06667)
    fig, ax = plt.subplots(figsize=(4.8, 4.5), dpi=500, facecolor="#FFFFFF")
    ax.set_facecolor("#182521")

    # Grayscale SAR backdrop + hazards
    ax.imshow(sar_norm, cmap="gray", extent=extent, origin="upper", zorder=1)
    ax.imshow(hazard_rgba, extent=extent, origin="upper", zorder=2)

    # Pasang Lhamu Highway
    gdf_hw.plot(ax=ax, color="#14B8A6", linewidth=1.5, zorder=4)
    # EMSR927 footprint
    gdf_emsr.plot(ax=ax, facecolor="none", edgecolor="#C084FC", linewidth=1.2, linestyle="--", zorder=5)

    ax.set_xlim(85.05, 85.40)
    ax.set_ylim(27.85, 28.25)
    ax.set_xlabel("Longitude (°E)", fontsize=7.5, fontweight="bold", color="#1E293B", labelpad=2)
    ax.set_ylabel("Latitude (°N)", fontsize=7.5, fontweight="bold", color="#1E293B", labelpad=2)
    ax.tick_params(labelsize=6.5, colors="#334155", pad=2)
    ax.grid(color="#E2E8F0", linestyle=":", linewidth=0.5, alpha=0.5)

    # Scale Bar and North Arrow
    add_scale_bar(ax, 85.07, 27.868, length_km=10.0, label="10 km", text_offset=0.005, fontsize=6.2)
    add_north_arrow(ax, x=0.91, y=0.91, fontsize=7.5)

    # Legend
    legend_elements = [
        mpatches.Patch(facecolor="#1D63B8", edgecolor="none", label="Candidate Flood (126.60 km², Δσ° ≤ -3.5 dB)"),
        mpatches.Patch(facecolor="#D97706", edgecolor="none", label="Candidate Debris (108.21 km², Δσ° ≥ +3.5 dB)"),
        mpatches.Patch(facecolor="#0B2545", edgecolor="none", label="Permanent Water (66.40 km², pre/post ≤ -16 dB)"),
        Line2D([0], [0], color="#14B8A6", lw=1.5, label="Pasang Lhamu Highway (57.95 km corridor)"),
        Line2D([0], [0], color="#C084FC", lw=1.2, ls="--", label="Copernicus EMSR927 Survey Footprint"),
    ]
    ax.legend(handles=legend_elements, loc="lower right", fontsize=5.8, framealpha=0.95, facecolor="#FFFFFF", edgecolor="#CBD5E1", borderpad=0.3, labelspacing=0.25)

    # Title Banner
    title_text = (
        "SAR Surface Change: Trishuli River Corridor\n"
        "Sentinel-1 GRD IW (Orbit 19, 2026-08-24 vs 2026-09-05, CAG 1,526.05 km²)"
    )
    ax.text(
        0.02,
        0.965,
        title_text,
        transform=ax.transAxes,
        fontsize=6.5,
        fontweight="bold",
        color="#0F172A",
        va="top",
        bbox=dict(boxstyle="round,pad=0.25", facecolor="#FFFFFF", edgecolor="#CBD5E1", alpha=0.95, lw=0.5),
        zorder=20,
    )

    plt.subplots_adjust(left=0.11, right=0.97, bottom=0.10, top=0.97)
    out_path = FIGURES_DIR / "figure3_sar_surface_change_classification.png"
    plt.savefig(out_path, dpi=500)
    plt.savefig(DEMO_DIR / "map_1_trishuli_regional_overview_publication_preview.png", dpi=500)
    plt.close()
    print(f"  -> Generated {out_path} ({round(out_path.stat().st_size / 1e3, 1)} KB)")


def generate_figure4():
    """
    Figure 4: Copernicus EMSR927 Reference Validation (Bidur Confluence AOI03).
    Slot: 234.6595 x 220 pt (exact ratio: 1.066634).
    """
    print("\n[Figure 4] Rendering Copernicus EMSR927 Reference Validation Map (AOI03)...")
    with rasterio.open(POST_TIF) as src_post:
        post_arr = src_post.read(1)
        bounds = src_post.bounds
        extent = [bounds.left, bounds.right, bounds.bottom, bounds.top]

    with rasterio.open(CLS_TIF) as src_cls:
        cls_arr = src_cls.read(2)

    vmin, vmax = -22.0, 2.0
    sar_norm = np.clip((post_arr - vmin) / (vmax - vmin), 0.0, 1.0)
    sar_norm[post_arr <= -9000] = np.nan

    h, w = cls_arr.shape
    hazard_rgba = np.zeros((h, w, 4), dtype=np.float32)
    hazard_rgba[cls_arr == 2] = [29/255, 99/255, 184/255, 0.88]
    hazard_rgba[cls_arr == 3] = [217/255, 119/255, 6/255, 0.88]

    gdf_emsr = gpd.read_file(EMSR_GEOJSON)
    gdf_bldgs = gpd.read_file(BLDGS_GEOJSON)
    gdf_roads = gpd.read_file(ROADS_GEOJSON)
    gdf_hw = gpd.read_file(HW_GEOJSON)

    # AOI03 Crop: Bidur / Battar Confluence
    bidur_xlim = (85.10, 85.20)
    bidur_ylim = (27.85, 28.01)
    bbox_poly = gpd.GeoSeries.from_wkt([f"POLYGON(({bidur_xlim[0]} {bidur_ylim[0]}, {bidur_xlim[1]} {bidur_ylim[0]}, {bidur_xlim[1]} {bidur_ylim[1]}, {bidur_xlim[0]} {bidur_ylim[1]}, {bidur_xlim[0]} {bidur_ylim[0]}))"]).iloc[0]

    gdf_roads_b = gdf_roads[gdf_roads.geometry.intersects(bbox_poly)]
    gdf_bldgs_b = gdf_bldgs[gdf_bldgs.geometry.intersects(bbox_poly)]

    # 4.8 x 4.5 inches at 500 DPI = 2400 x 2250 px (Exact ratio: 1.06667)
    fig, ax = plt.subplots(figsize=(4.8, 4.5), dpi=500, facecolor="#FFFFFF")
    ax.set_facecolor("#182521")

    # Base SAR + Hazards
    ax.imshow(sar_norm, cmap="gray", extent=extent, origin="upper", zorder=1)
    ax.imshow(hazard_rgba, extent=extent, origin="upper", zorder=2)

    # Road Network
    gdf_roads_b.plot(ax=ax, color="#64748B", linewidth=0.8, alpha=0.6, zorder=3)
    roads_exp = gdf_roads_b[gdf_roads_b["potential_exposure"].str.contains("FLOOD|DEBRIS", na=False)]
    if not roads_exp.empty:
        roads_exp.plot(ax=ax, color="#F59E0B", linewidth=1.4, zorder=4)

    # Pasang Lhamu Highway
    gdf_hw.plot(ax=ax, color="#14B8A6", linewidth=1.8, zorder=5)

    # EMSR927 Footprint
    gdf_emsr.plot(ax=ax, facecolor="#A855F7", alpha=0.18, edgecolor="#A855F7", linewidth=1.5, linestyle="--", zorder=6)

    # Buildings by damage grade
    bldgs_dest = gdf_bldgs_b[gdf_bldgs_b["damage_gra"] == "Destroyed"]
    bldgs_dam = gdf_bldgs_b[gdf_bldgs_b["damage_gra"] == "Damaged"]
    bldgs_pos = gdf_bldgs_b[gdf_bldgs_b["damage_gra"] == "Possibly damaged"]
    bldgs_other = gdf_bldgs_b[~gdf_bldgs_b["damage_gra"].isin(["Destroyed", "Damaged", "Possibly damaged"])]

    if not bldgs_other.empty:
        bldgs_other.plot(ax=ax, color="#94A3B8", markersize=4, alpha=0.5, zorder=7)
    if not bldgs_pos.empty:
        bldgs_pos.plot(ax=ax, color="#EAB308", markersize=7, zorder=8)
    if not bldgs_dam.empty:
        bldgs_dam.plot(ax=ax, color="#F97316", markersize=8, zorder=9)
    if not bldgs_dest.empty:
        bldgs_dest.plot(ax=ax, color="#EF4444", markersize=10, edgecolor="#FFFFFF", linewidth=0.3, zorder=10)

    ax.set_xlim(*bidur_xlim)
    ax.set_ylim(*bidur_ylim)
    ax.set_xlabel("Longitude (°E)", fontsize=7.5, fontweight="bold", color="#1E293B", labelpad=2)
    ax.set_ylabel("Latitude (°N)", fontsize=7.5, fontweight="bold", color="#1E293B", labelpad=2)
    ax.tick_params(labelsize=6.5, colors="#334155", pad=2)
    ax.grid(color="#E2E8F0", linestyle=":", linewidth=0.5, alpha=0.5)

    # Scale Bar (2 km) and North Arrow
    add_scale_bar(ax, 85.11, 27.858, length_km=2.0, label="2 km", text_offset=0.0025, fontsize=6.2)
    add_north_arrow(ax, x=0.91, y=0.91, fontsize=7.5)

    # Legend
    legend_elements = [
        Line2D([0], [0], color="#A855F7", lw=1.5, ls="--", label="Copernicus EMSR927 Footprint (5.89 km²)"),
        mpatches.Patch(facecolor="#1D63B8", edgecolor="none", label="SAR Candidate Flood (Δσ° ≤ -3.5 dB)"),
        mpatches.Patch(facecolor="#D97706", edgecolor="none", label="SAR Candidate Debris (Δσ° ≥ +3.5 dB)"),
        Line2D([0], [0], color="#14B8A6", lw=1.8, label="Pasang Lhamu Highway (9.62 km in hazard)"),
        Line2D([0], [0], color="#F59E0B", lw=1.4, label="Potentially Exposed Road Segments"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#EF4444", markersize=5, label="Building: Destroyed (EMSR927)"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#F97316", markersize=4.5, label="Building: Damaged"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#EAB308", markersize=4, label="Building: Possibly Damaged"),
    ]
    ax.legend(handles=legend_elements, loc="lower right", fontsize=5.5, framealpha=0.95, facecolor="#FFFFFF", edgecolor="#CBD5E1", borderpad=0.25, labelspacing=0.2)

    # Title & Validation Metrics Box
    val_banner = (
        "Reference Validation: Bidur Confluence (Copernicus EMSR927 AOI03)\n"
        "Total Anomaly Coincidence: 37.16% (24,885 of 66,959 optical footprint pixels)\n"
        "• Flood Overlap: 1.58 km² (26.89%)  |  Debris Overlap: 0.61 km² (10.28%)\n"
        "• Observed spatial coincidence under 10-day lag (not classifier precision/recall)"
    )
    ax.text(
        0.02,
        0.965,
        val_banner,
        transform=ax.transAxes,
        fontsize=5.8,
        fontweight="bold",
        color="#0F172A",
        va="top",
        bbox=dict(boxstyle="round,pad=0.25", facecolor="#FFFFFF", edgecolor="#CBD5E1", alpha=0.95, lw=0.5),
        zorder=20,
    )

    plt.subplots_adjust(left=0.11, right=0.97, bottom=0.10, top=0.97)
    out_path = FIGURES_DIR / "figure4_emsr927_validation_bidur.png"
    plt.savefig(out_path, dpi=500)
    plt.savefig(DEMO_DIR / "map_2_bidur_impact_validation_publication_preview.png", dpi=500)
    plt.close()
    print(f"  -> Generated {out_path} ({round(out_path.stat().st_size / 1e3, 1)} KB)")


def generate_sitrep_figure():
    """
    Figure for Operational Situation Report 01.
    Slot: 202.0358 x 235.2756 pt (exact ratio: 0.8587196).
    """
    print("\n[SitRep Figure] Rendering Sentinel-1 Bitemporal Change-Screening Map...")
    with rasterio.open(POST_TIF) as src_post:
        post_arr = src_post.read(1)
        bounds = src_post.bounds
        extent = [bounds.left, bounds.right, bounds.bottom, bounds.top]

    with rasterio.open(CLS_TIF) as src_cls:
        cls_arr = src_cls.read(2)

    vmin, vmax = -22.0, 2.0
    sar_norm = np.clip((post_arr - vmin) / (vmax - vmin), 0.0, 1.0)
    sar_norm[post_arr <= -9000] = np.nan

    h, w = cls_arr.shape
    hazard_rgba = np.zeros((h, w, 4), dtype=np.float32)
    hazard_rgba[cls_arr == 2] = [29/255, 99/255, 184/255, 0.88]
    hazard_rgba[cls_arr == 3] = [217/255, 119/255, 6/255, 0.88]
    hazard_rgba[cls_arr == 4] = [11/255, 37/255, 69/255, 0.88]

    gdf_emsr = gpd.read_file(EMSR_GEOJSON)
    gdf_hw = gpd.read_file(HW_GEOJSON)

    # 4.2936 x 5.0 inches at 500 DPI = 2147 x 2500 px (Exact ratio: 0.85872)
    fig, ax = plt.subplots(figsize=(4.2936, 5.0), dpi=500, facecolor="#FFFFFF")
    ax.set_facecolor("#182521")

    # Grayscale SAR backdrop + hazards
    ax.imshow(sar_norm, cmap="gray", extent=extent, origin="upper", zorder=1)
    ax.imshow(hazard_rgba, extent=extent, origin="upper", zorder=2)

    # Pasang Lhamu Highway
    gdf_hw.plot(ax=ax, color="#14B8A6", linewidth=1.5, zorder=4)
    # EMSR927 footprint
    gdf_emsr.plot(ax=ax, facecolor="none", edgecolor="#C084FC", linewidth=1.1, linestyle="--", zorder=5)

    # Key Settlements
    settlements = [
        ("Timure Border (AOI02)", 85.378, 28.232, "bottom left"),
        ("Syapru Besi (AOI01)", 85.340, 28.160, "right"),
        ("Dhunche (HQ)", 85.295, 28.115, "right"),
        ("Mailung", 85.185, 28.025, "left"),
        ("Bidur (AOI03)", 85.155, 27.918, "left"),
    ]
    for name, lon, lat, pos in settlements:
        ax.plot(lon, lat, marker="o", color="#DC2626", markersize=3.5, markeredgecolor="#FFFFFF", markeredgewidth=0.5, zorder=20)
        ha = "left" if "right" in pos else ("right" if "left" in pos else "center")
        va = "top" if "bottom" in pos else "center"
        offset_x = 0.007 if ha == "left" else (-0.007 if ha == "right" else 0.0)
        offset_y = -0.008 if "bottom" in pos else (0.005 if "top" in pos else 0.0)
        ax.text(
            lon + offset_x,
            lat + offset_y,
            name,
            fontsize=5.6,
            fontweight="bold",
            color="#0F172A",
            ha=ha,
            va=va,
            bbox=dict(boxstyle="round,pad=0.15", facecolor="#FFFFFF", edgecolor="#CBD5E1", alpha=0.92, lw=0.4),
            zorder=21,
        )

    ax.set_xlim(85.05, 85.40)
    ax.set_ylim(27.85, 28.25)
    ax.set_xlabel("Longitude (°E)", fontsize=7.0, fontweight="bold", color="#1E293B", labelpad=2)
    ax.set_ylabel("Latitude (°N)", fontsize=7.0, fontweight="bold", color="#1E293B", labelpad=2)
    ax.tick_params(labelsize=6.0, colors="#334155", pad=2)
    ax.grid(color="#E2E8F0", linestyle=":", linewidth=0.5, alpha=0.5)

    # Scale Bar and North Arrow
    add_scale_bar(ax, 85.07, 27.868, length_km=10.0, label="10 km", text_offset=0.005, fontsize=6.0)
    add_north_arrow(ax, x=0.90, y=0.91, fontsize=7.2)

    # Title Banner
    title_text = (
        "Trishuli Valley SAR Surface Change Assessment\n"
        "Sentinel-1 Level-1 GRD (24 Aug – 05 Sep 2026) & EMSR927"
    )
    ax.text(
        0.02,
        0.965,
        title_text,
        transform=ax.transAxes,
        fontsize=5.8,
        fontweight="bold",
        color="#0F172A",
        va="top",
        bbox=dict(boxstyle="round,pad=0.22", facecolor="#FFFFFF", edgecolor="#CBD5E1", alpha=0.95, lw=0.5),
        zorder=25,
    )

    # Legend
    legend_elements = [
        mpatches.Patch(facecolor="#1D63B8", edgecolor="none", label="Candidate Flood (126.60 km², Δσ° ≤ -3.5 dB)"),
        mpatches.Patch(facecolor="#D97706", edgecolor="none", label="Candidate Debris (108.21 km², Δσ° ≥ +3.5 dB)"),
        mpatches.Patch(facecolor="#0B2545", edgecolor="none", label="Permanent Water (66.40 km², pre/post ≤ -16 dB)"),
        Line2D([0], [0], color="#14B8A6", lw=1.4, label="Pasang Lhamu Highway (57.95 km corridor)"),
        Line2D([0], [0], color="#C084FC", lw=1.1, ls="--", label="Copernicus EMSR927 Survey Footprint"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#DC2626", markersize=3.5, label="Key Settlement / Hub"),
    ]
    ax.legend(
        handles=legend_elements,
        loc="lower right",
        fontsize=5.2,
        framealpha=0.95,
        facecolor="#FFFFFF",
        edgecolor="#CBD5E1",
        borderpad=0.25,
        labelspacing=0.2,
    )

    plt.subplots_adjust(left=0.12, right=0.97, bottom=0.09, top=0.97)
    out_path = FIGURES_DIR / "figure_sitrep_trishuli_change_map.png"
    plt.savefig(out_path, dpi=500)
    plt.close()
    print(f"  -> Generated {out_path} ({round(out_path.stat().st_size / 1e3, 1)} KB)")


if __name__ == "__main__":
    generate_figure1()
    generate_figure2()
    generate_figure3()
    generate_figure4()
    generate_sitrep_figure()
    print("\nAll scientific figures generated successfully at >=300 DPI.")

