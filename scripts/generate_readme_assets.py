#!/usr/bin/env python3
"""
scripts/generate_readme_assets.py

Generates flagship visual assets for the VARUNA GitHub repository:
1. docs/assets/readme/hero.gif — Animated hero banner with orbital trace & radar pulse
2. docs/assets/readme/hero-static.png — High-resolution static fallback
3. docs/assets/readme/workflow.png — Scientific processing pipeline architecture
4. docs/assets/readme/case-study-metrics.png — Executive scientific metric card grid
5. docs/assets/readme/satellite-comparison.png — Workspace 1 authentic view
6. docs/assets/readme/surface-change.png — Workspace 2 authentic view
7. docs/assets/readme/infrastructure-exposure.png — Workspace 3 authentic view
8. docs/assets/readme/reference-validation.png — Workspace 4 authentic view
9. docs/assets/readme/situation-copilot.png — Workspace 5 authentic view
"""

import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT_DIR / "docs" / "assets" / "readme"
SCREENSHOTS_DIR = ROOT_DIR / "reports" / "screenshots"

ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# Curated Brand Palette
COLOR_NAVY_DARK = (11, 20, 36)      # #0B1424
COLOR_NAVY_MID = (22, 36, 56)       # #162438
COLOR_NAVY_LIGHT = (30, 48, 74)     # #1E304A
COLOR_TEAL = (73, 184, 186)         # #49B8BA
COLOR_TEAL_DIM = (40, 100, 102)     # Muted teal
COLOR_ICE = (216, 237, 244)         # #D8EDF4
COLOR_ORANGE = (229, 154, 80)       # #E59A50
COLOR_WHITE = (255, 255, 255)
COLOR_GRAY = (140, 160, 185)


def get_font(size: int, bold: bool = False):
    """Load standard macOS system fonts with graceful fallbacks."""
    font_candidates = []
    if bold:
        font_candidates = [
            "/System/Library/Fonts/SFNSDisplay.ttf",
            "/System/Library/Fonts/SFProText-Bold.otf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/Library/Fonts/Arial Bold.ttf",
        ]
    else:
        font_candidates = [
            "/System/Library/Fonts/SFNSText.ttf",
            "/System/Library/Fonts/SFProText-Regular.otf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/Library/Fonts/Arial.ttf",
        ]
    for p in font_candidates:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


# -----------------------------------------------------------------------------
# 1. Hero Banner & Animated GIF
# -----------------------------------------------------------------------------
def render_hero_frame(frame_idx: int, total_frames: int, width: int = 1200, height: int = 420) -> Image.Image:
    t = frame_idx / total_frames  # 0.0 to 1.0

    im = Image.new("RGB", (width, height), COLOR_NAVY_DARK)
    draw = ImageDraw.Draw(im, "RGBA")

    # Background subtle radial glow from center-right
    cx, cy = int(width * 0.72), int(height * 0.48)
    for r in range(280, 0, -10):
        alpha = int(22 * (1 - r / 280))
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(22, 45, 70, alpha))

    # Draw coordinate graticule grid (faint)
    grid_color = (73, 184, 186, 24)
    for x in range(60, width, 80):
        draw.line([(x, 0), (x, height)], fill=grid_color, width=1)
    for y in range(40, height, 60):
        draw.line([(0, y), (width, y)], fill=grid_color, width=1)

    # Stylized Himalayan mountain ridge lines (topographic silhouette)
    ridge_points = [
        (550, 360), (620, 290), (690, 315), (760, 240), (840, 280),
        (920, 210), (1000, 260), (1080, 200), (1160, 250), (1200, 220),
        (1200, 420), (550, 420)
    ]
    draw.polygon(ridge_points, fill=(18, 32, 52, 180))

    ridge_points_front = [
        (600, 380), (680, 320), (750, 340), (820, 290), (900, 330),
        (980, 270), (1060, 310), (1140, 260), (1200, 300),
        (1200, 420), (600, 420)
    ]
    draw.polygon(ridge_points_front, fill=(14, 25, 42, 230))

    # Orbital trace trajectory curve (descending orbit 19)
    orbit_start = (640, 30)
    orbit_end = (1080, 390)
    orbit_dx = orbit_end[0] - orbit_start[0]
    orbit_dy = orbit_end[1] - orbit_start[1]

    # Draw dashed orbital flight path
    num_dashes = 36
    for i in range(num_dashes):
        frac1 = i / num_dashes
        frac2 = (i + 0.55) / num_dashes
        p1 = (orbit_start[0] + orbit_dx * frac1, orbit_start[1] + orbit_dy * frac1)
        p2 = (orbit_start[0] + orbit_dx * frac2, orbit_start[1] + orbit_dy * frac2)
        draw.line([p1, p2], fill=(73, 184, 186, 90), width=2)

    # Orbiting satellite position
    sat_x = orbit_start[0] + orbit_dx * t
    sat_y = orbit_start[1] + orbit_dy * t

    # Radar conical swath scanline expanding from satellite to ground
    swath_angle = math.pi * 0.42
    swath_len = 160
    ground_lx = sat_x - swath_len * 0.6
    ground_rx = sat_x + swath_len * 0.3
    ground_y = sat_y + swath_len

    # Pulsing beam
    beam_alpha = int(45 + 30 * math.sin(t * 2 * math.pi))
    draw.polygon(
        [(sat_x, sat_y), (ground_lx, min(height, ground_y)), (ground_rx, min(height, ground_y))],
        fill=(73, 184, 186, beam_alpha)
    )

    # Expanding radar wavefront rings
    pulse_phase = (t * 2) % 1.0
    for wave_offset in [0.0, 0.5]:
        phase = (t + wave_offset) % 1.0
        ring_r = int(phase * 110)
        ring_alpha = int(140 * (1 - phase))
        if ring_r > 5:
            draw.ellipse(
                [sat_x - ring_r, sat_y - ring_r * 0.6, sat_x + ring_r, sat_y + ring_r * 0.6],
                outline=(229, 154, 80, ring_alpha),
                width=1
            )

    # Satellite node
    draw.ellipse([sat_x - 7, sat_y - 7, sat_x + 7, sat_y + 7], fill=(255, 255, 255, 240))
    draw.ellipse([sat_x - 12, sat_y - 12, sat_x + 12, sat_y + 12], outline=(73, 184, 186, 200), width=2)

    # Telemetry coordinate tag next to satellite
    font_tele = get_font(11, bold=True)
    lat_val = 28.25 - t * 0.40
    lon_val = 85.05 + t * 0.35
    tele_text = f"S1D ORBIT 19 • {lat_val:.2f}°N {lon_val:.2f}°E"
    draw.text((sat_x + 18, sat_y - 10), tele_text, fill=(216, 237, 244, 210), font=font_tele)

    # ----------------------------------------------------
    # Left Branding & Typography
    # ----------------------------------------------------
    # Top Tagline badge
    badge_bg = [60, 52, 380, 78]
    draw.rectangle(badge_bg, fill=(22, 36, 56, 220), outline=(73, 184, 186, 120), width=1)
    font_badge = get_font(11, bold=True)
    draw.text((72, 59), "MULTIMODAL AI HACKATHON 2026 • TRACK B", fill=COLOR_TEAL, font=font_badge)

    # Main Title: V A R U N A
    font_title = get_font(52, bold=True)
    draw.text((60, 102), "VARUNA", fill=COLOR_WHITE, font=font_title)

    # Small radar indicator square next to title
    draw.rectangle([348, 114, 356, 122], fill=COLOR_ORANGE)

    # Subtitle: Mapping Impact From Space.
    font_sub = get_font(24, bold=True)
    draw.text((60, 178), "Mapping Impact From Space.", fill=COLOR_ICE, font=font_sub)

    # Secondary line: Mission scope
    font_desc = get_font(15, bold=False)
    desc_line = "Satellite Observations  •  Surface Change  •  Infrastructure Intelligence"
    draw.text((60, 220), desc_line, fill=COLOR_TEAL, font=desc_desc if (desc_desc := get_font(14, bold=False)) else font_desc)

    # Scientific Proof Micro-Stats bar
    stat_y = 282
    draw.line([(60, stat_y - 14), (520, stat_y - 14)], fill=(73, 184, 186, 60), width=1)

    font_stat_val = get_font(18, bold=True)
    font_stat_lbl = get_font(10, bold=False)

    stats = [
        ("126.60 km²", "CANDIDATE FLOOD"),
        ("108.21 km²", "SURFACE DEBRIS"),
        ("1,062", "EXPOSED ASSETS"),
        ("37.16%", "EMSR927 COINCIDENCE"),
    ]

    col_w = 115
    for idx, (val, lbl) in enumerate(stats):
        bx = 60 + idx * col_w
        draw.text((bx, stat_y), val, fill=COLOR_WHITE, font=font_stat_val)
        draw.text((bx, stat_y + 24), lbl, fill=(140, 160, 185), font=font_stat_lbl)

    # Bottom border line
    draw.line([(0, height - 2), (width, height - 2)], fill=(73, 184, 186, 140), width=2)

    return im


def build_hero_assets():
    print("[1/5] Generating Hero Banner & Animation...")
    # Static banner
    static_im = render_hero_frame(12, 24)
    static_path = ASSETS_DIR / "hero-static.png"
    static_im.save(static_path, "PNG", optimize=True)
    print(f"  ✓ Saved static hero: {static_path} ({static_path.stat().st_size / 1024:.1f} KB)")

    # Animated GIF (24 frames, ~80ms = 12.5 fps)
    frames = []
    num_frames = 24
    for f in range(num_frames):
        # Slightly downsample to 1000x350 for light GIF footprint (~1.2MB)
        full_f = render_hero_frame(f, num_frames, width=1000, height=350)
        # Convert to P mode with adaptive palette for crisp GIF rendering
        p_frame = full_f.convert("P", palette=Image.ADAPTIVE, colors=256)
        frames.append(p_frame)

    gif_path = ASSETS_DIR / "hero.gif"
    frames[0].save(
        gif_path,
        save_all=True,
        append_images=frames[1:],
        duration=80,
        loop=0,
        optimize=True,
    )
    print(f"  ✓ Saved animated hero GIF: {gif_path} ({gif_path.stat().st_size / (1024*1024):.2f} MB)")


# -----------------------------------------------------------------------------
# 2. Workflow Pipeline Diagram
# -----------------------------------------------------------------------------
def build_workflow_diagram():
    print("[2/5] Generating Scientific Architecture Workflow Diagram...")
    w, h = 1200, 360
    im = Image.new("RGB", (w, h), COLOR_NAVY_DARK)
    draw = ImageDraw.Draw(im, "RGBA")

    # Header
    font_head = get_font(18, bold=True)
    font_sub = get_font(12, bold=False)
    draw.text((40, 24), "VARUNA END-TO-END SCIENTIFIC PROCESSING ARCHITECTURE", fill=COLOR_WHITE, font=font_head)
    draw.text((40, 50), "Deterministic, physics-grounded satellite intelligence pipeline with strictly held-out reference validation.", fill=COLOR_TEAL, font=font_sub)

    # 5 Sequential Stages
    stages = [
        ("01. INGESTION", "Copernicus CDSE", ["Sentinel-1 GRD IW VV", "GLO-30 Global DEM", "POEORB Orbit Vectors", "OSM Pre-Event Roads"], COLOR_TEAL),
        ("02. PREPROCESS", "ESA SNAP 10.0 GPT", ["Thermal Noise Removal", "XML LUT Calibration", "Range-Doppler Ortho", "10m Grid Alignment"], COLOR_TEAL),
        ("03. CHANGE DETECTION", "Common Analysis Grid", ["Delta dB Thresholding", "Candidate Flood <= -3.5dB", "Candidate Debris >= +3.5dB", "MMU Morphology Filter"], COLOR_ORANGE),
        ("04. EXPOSURE & ROUTING", "NetworkX Graph", ["Road Corridor Cuts", "Building Intersections", "Hospital Isolation", "Pasang Lhamu Highway"], COLOR_ICE),
        ("05. AUDIT & COPILOT", "Traceable FactBase", ["Copernicus EMSR927 Held-Out", "Bilingual EN/NE Copilot", "1-Page SitRep (PDF)", "Academic Paper (PDF)"], COLOR_WHITE),
    ]

    card_y = 90
    card_w = 210
    card_h = 230
    gap = 22
    start_x = 40

    font_stage_num = get_font(11, bold=True)
    font_stage_title = get_font(14, bold=True)
    font_item = get_font(11, bold=False)

    for i, (num_tag, title, items, accent) in enumerate(stages):
        bx = start_x + i * (card_w + gap)

        # Card container
        draw.rectangle([bx, card_y, bx + card_w, card_y + card_h], fill=COLOR_NAVY_MID, outline=(73, 184, 186, 80), width=1)
        # Top color accent bar
        draw.rectangle([bx, card_y, bx + card_w, card_y + 4], fill=accent)

        draw.text((bx + 14, card_y + 16), num_tag, fill=COLOR_ORANGE, font=font_stage_num)
        draw.text((bx + 14, card_y + 36), title, fill=COLOR_WHITE, font=font_stage_title)

        draw.line([(bx + 14, card_y + 64), (bx + card_w - 14, card_y + 64)], fill=(73, 184, 186, 50), width=1)

        # Items
        for j, item in enumerate(items):
            iy = card_y + 78 + j * 34
            draw.ellipse([bx + 14, iy + 4, bx + 19, iy + 9], fill=accent)
            draw.text((bx + 26, iy), item, fill=(216, 237, 244), font=font_item)

        # Arrow connector between cards
        if i < len(stages) - 1:
            ax = bx + card_w + 6
            ay = card_y + card_h // 2
            draw.line([(ax, ay), (ax + 10, ay)], fill=COLOR_TEAL, width=2)
            draw.polygon([(ax + 8, ay - 4), (ax + 14, ay), (ax + 8, ay + 4)], fill=COLOR_TEAL)

    wf_path = ASSETS_DIR / "workflow.png"
    im.save(wf_path, "PNG", optimize=True)
    print(f"  ✓ Saved workflow architecture diagram: {wf_path} ({wf_path.stat().st_size / 1024:.1f} KB)")


# -----------------------------------------------------------------------------
# 3. Case Study Metric Cards Banner
# -----------------------------------------------------------------------------
def build_case_study_metrics():
    print("[3/5] Generating Scientific Case Study Metrics Banner...")
    w, h = 1200, 240
    im = Image.new("RGB", (w, h), COLOR_NAVY_DARK)
    draw = ImageDraw.Draw(im, "RGBA")

    # Header
    font_head = get_font(16, bold=True)
    font_sub = get_font(11, bold=False)
    draw.text((40, 20), "TRISHULI BASIN FLOOD CASE STUDY — VERIFIED SCIENTIFIC METRICS", fill=COLOR_WHITE, font=font_head)
    draw.text((40, 42), "Copernicus Sentinel-1 (Relative Orbit 19) • August 24 Pre vs September 5 Post • 10-Day Recession Disclosed", fill=COLOR_TEAL, font=font_sub)

    cards = [
        ("126.60 km²", "Candidate Inundation (Raw)", "62.86 km² contiguous MMU ≥1000m²\nΔσ° ≤ -3.5 dB (10m grid)", COLOR_TEAL),
        ("108.21 km²", "Candidate Surface Debris (Raw)", "46.93 km² contiguous MMU ≥1000m²\nΔσ° ≥ +3.5 dB coarsening", COLOR_ORANGE),
        ("1,062 Assets", "Potentially Exposed Buildings", "27.83% of 3,816 surveyed\n33.27% of EMSR927 destroyed", COLOR_ICE),
        ("35.12 km", "Exposed Road Segments", "13.47% of 260.7 km network\n9.62 km Pasang Lhamu Highway", COLOR_WHITE),
        ("37.16%", "EMSR927 Truth Coincidence", "AOI03 Bidur optical overlap\nDirect recession indicator", COLOR_TEAL),
    ]

    card_y = 70
    card_w = 210
    card_h = 145
    gap = 18
    start_x = 40

    font_val = get_font(24, bold=True)
    font_title = get_font(12, bold=True)
    font_desc = get_font(10, bold=False)

    for i, (val, title, desc, accent) in enumerate(cards):
        bx = start_x + i * (card_w + gap)

        # Card container
        draw.rectangle([bx, card_y, bx + card_w, card_y + card_h], fill=COLOR_NAVY_MID, outline=(73, 184, 186, 70), width=1)
        draw.rectangle([bx, card_y, bx + card_w, card_y + 3], fill=accent)

        draw.text((bx + 14, card_y + 14), val, fill=COLOR_WHITE, font=font_val)
        draw.text((bx + 14, card_y + 48), title, fill=accent, font=font_title)

        draw.line([(bx + 14, card_y + 72), (bx + card_w - 14, card_y + 72)], fill=(73, 184, 186, 40), width=1)

        lines = desc.split("\n")
        for line_idx, line in enumerate(lines):
            draw.text((bx + 14, card_y + 82 + line_idx * 16), line, fill=(180, 200, 220), font=font_desc)

    metrics_path = ASSETS_DIR / "case-study-metrics.png"
    im.save(metrics_path, "PNG", optimize=True)
    print(f"  ✓ Saved metrics banner: {metrics_path} ({metrics_path.stat().st_size / 1024:.1f} KB)")


# -----------------------------------------------------------------------------
# 4. Authentic Workspace Screenshots (Optimized 1280x720)
# -----------------------------------------------------------------------------
def process_workspace_screenshots():
    print("[4/5] Formatting and Optimizing Authentic Workspace Screenshots...")

    screenshot_mappings = [
        ("04_comparison_highlight_changes_corridor.png", "satellite-comparison.png", "Workspace 1: Sentinel-1 SAR Intensity Comparison & Swath Swipe"),
        ("07_workspace_change_detection.png", "surface-change.png", "Workspace 2: Bitemporal Radar Surface Change Classification (10m)"),
        ("08_workspace_infrastructure_exposure.png", "infrastructure-exposure.png", "Workspace 3: Critical Infrastructure & Road Exposure Routing"),
        ("09_workspace_reference_validation.png", "reference-validation.png", "Workspace 4: Copernicus EMS EMSR927 Held-Out Validation Benchmark"),
        ("10_workspace_situation_copilot.png", "situation-copilot.png", "Workspace 5: Bilingual Grounded Situation Copilot (English & Nepali)"),
    ]

    for src_name, dst_name, label in screenshot_mappings:
        src_path = SCREENSHOTS_DIR / src_name
        dst_path = ASSETS_DIR / dst_name

        if not src_path.exists():
            print(f"  ! Warning: {src_path} not found, checking fallback in data/demo_evidence")
            continue

        im = Image.open(src_path).convert("RGB")
        # Resize to crisp 1280x720 with high-quality Lanczos resampling
        im_resized = im.resize((1280, 720), Image.Resampling.LANCZOS)
        im_resized.save(dst_path, "PNG", optimize=True)
        print(f"  ✓ Formatted {dst_name}: {im_resized.size[0]}x{im_resized.size[1]} ({dst_path.stat().st_size / 1024:.1f} KB)")


# -----------------------------------------------------------------------------
# 5. Interactive Swipe Demo GIF (Before / After Comparison)
# -----------------------------------------------------------------------------
def build_comparison_swipe_gif():
    print("[5/5] Generating Comparison Swipe Demonstration GIF...")
    # Frames from 01, 02, 03, 04 comparison
    comp_files = [
        SCREENSHOTS_DIR / "01_comparison_initial_50.png",
        SCREENSHOTS_DIR / "02_comparison_drag_left_20.png",
        SCREENSHOTS_DIR / "01_comparison_initial_50.png",
        SCREENSHOTS_DIR / "03_comparison_drag_right_80.png",
        SCREENSHOTS_DIR / "04_comparison_highlight_changes_corridor.png",
    ]

    valid_frames = []
    for cf in comp_files:
        if cf.exists():
            im = Image.open(cf).convert("RGB").resize((960, 540), Image.Resampling.LANCZOS)
            p_im = im.convert("P", palette=Image.ADAPTIVE, colors=256)
            valid_frames.append(p_im)

    if len(valid_frames) >= 3:
        swipe_gif_path = ASSETS_DIR / "satellite-comparison-swipe.gif"
        # Duplicate frames to provide comfortable viewing pause
        full_loop = [
            valid_frames[0], valid_frames[0],
            valid_frames[1], valid_frames[1],
            valid_frames[2],
            valid_frames[3], valid_frames[3],
            valid_frames[4], valid_frames[4], valid_frames[4],
        ]
        full_loop[0].save(
            swipe_gif_path,
            save_all=True,
            append_images=full_loop[1:],
            duration=600,
            loop=0,
            optimize=True,
        )
        print(f"  ✓ Saved comparison swipe GIF: {swipe_gif_path} ({swipe_gif_path.stat().st_size / (1024*1024):.2f} MB)")


if __name__ == "__main__":
    build_hero_assets()
    build_workflow_diagram()
    build_case_study_metrics()
    process_workspace_screenshots()
    build_comparison_swipe_gif()
    print("\nAll README visual assets successfully built under docs/assets/readme/")
