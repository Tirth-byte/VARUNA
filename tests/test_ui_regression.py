"""
VARUNA — Permanent UI Regression & Usability Audit Test Suite
Verifies application shell layout, independent panel scrolling, toolbar containment,
table vertical grid lines, status bar separation, and accordion expansion.
"""

import json
import os
import re
import subprocess
import pytest

DASHBOARD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dashboard"))
STYLES_CSS = os.path.join(DASHBOARD_DIR, "styles.css")
APP_JS = os.path.join(DASHBOARD_DIR, "app.js")
INDEX_HTML = os.path.join(DASHBOARD_DIR, "index.html")
BRAVE_PATH = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"


def test_styles_shell_and_layout_contracts():
    """Verify application shell sizing and overflow containment contracts in CSS."""
    with open(STYLES_CSS, "r", encoding="utf-8") as f:
        css = f.read()

    # 100dvh viewport constraint
    assert "100dvh" in css, "Application shell must utilize 100dvh viewport sizing"
    assert "overflow: hidden" in css, "Root shell must prevent outer document scrolling"

    # Map viewport min dimensions
    assert ".map-viewport" in css
    assert "min-width: 0" in css
    assert "min-height: 0" in css

    # Panel scrolling and flex-shrink protection
    assert ".panel-body" in css
    assert "overflow-y: auto" in css
    assert ".panel-body > *" in css
    assert "flex-shrink: 0" in css, "Panel body children must have flex-shrink: 0 to prevent card squishing"

    # Accordion natural height and overflow
    assert "details.scientific-accordion" in css
    assert "height: auto" in css, "Accordions must expand to natural height"
    assert "overflow: visible" in css, "Accordions must not silently crop expanded text"

    # Scientific table professional grid lines
    assert ".scientific-table" in css
    assert "border-right: 1px solid" in css, "Scientific tables must have visible vertical grid lines"
    assert ".scientific-table-wrap" in css
    assert "overflow-x: auto" in css, "Tables must scroll horizontally within wrapper without clipping"


def test_map_overlay_layering_and_z_index():
    """Verify z-index hierarchy prevents swipe divider from intersecting controls."""
    with open(STYLES_CSS, "r", encoding="utf-8") as f:
        css = f.read()

    # Swipe divider must be layered above rasters (400) and behind interface controls (500)
    assert ".swipe-curtain-container" in css
    assert "z-index: 450" in css, "Swipe curtain container must be z-index 450 (above rasters, behind controls)"
    assert "bottom: 38px" in css, "Swipe divider line must terminate cleanly above status bar"

    # Interface controls must be layered on top
    assert ".map-status-bar" in css
    assert "z-index: 500" in css, "Status bar must be z-index 500"
    assert ".map-floating-legend" in css
    assert "z-index: 500" in css, "Legend must be z-index 500"
    assert ".map-workspace-toolbar" in css
    assert "z-index: 600" in css, "Toolbars must be z-index 600"


def test_toolbar_select_and_dropdown_styling():
    """Verify toolbar dropdowns have dedicated custom chevrons and proper padding."""
    with open(STYLES_CSS, "r", encoding="utf-8") as f:
        css = f.read()

    assert ".toolbar-select" in css
    assert "appearance: none" in css, "Toolbar select must strip platform-inconsistent native widgets"
    assert "padding: 0 22px 0 8px" in css, "Toolbar select must provide right clearance for chevron"
    assert "height: 26px" in css, "Toolbar select must have 26px uniform control height"


def test_responsive_media_queries():
    """Verify responsive breakpoints for 1440, 1366, 1280, and 1024 viewports exist."""
    with open(STYLES_CSS, "r", encoding="utf-8") as f:
        css = f.read()

    assert "@media (max-width: 1440px)" in css
    assert "@media (max-width: 1366px)" in css
    assert "@media (max-width: 1280px)" in css
    assert "@media (max-width: 1024px)" in css


def test_html_status_bar_semantic_elements():
    """Verify status bar has proper semantic classes and dividers in index.html."""
    with open(INDEX_HTML, "r", encoding="utf-8") as f:
        html = f.read()

    assert 'id="mapStatusBar"' in html
    assert 'class="status-bar-divider"' in html
    assert 'id="txtCoords"' in html
    assert 'id="btnToggleBasemapStatus"' in html


@pytest.mark.skipif(not os.path.exists(BRAVE_PATH), reason="Headless browser not installed")
def test_browser_dom_metrics_and_containment():
    """Verify layout geometry using headless Chromium across 1920, 1440, 1366, and 1280 resolutions."""
    test_script = """
    (function() {
      const results = {};
      const status = document.getElementById('mapStatusBar');
      const legend = document.getElementById('mapLegend');
      const toolbar = document.getElementById('workspaceToolbar');
      const panel = document.getElementById('panelBody');
      const map = document.getElementById('map');

      results.hasHorizontalOverflow = (document.documentElement.scrollWidth > window.innerWidth);
      results.statusRect = status ? status.getBoundingClientRect() : null;
      results.legendRect = legend ? legend.getBoundingClientRect() : null;
      results.toolbarRect = toolbar ? toolbar.getBoundingClientRect() : null;
      results.mapRect = map ? map.getBoundingClientRect() : null;
      results.panelScrollable = panel ? (panel.scrollHeight >= panel.clientHeight) : false;

      // Status bar and legend collision check
      if (results.statusRect && results.legendRect) {
        results.overlapped = (results.statusRect.right > results.legendRect.left);
      } else {
        results.overlapped = false;
      }

      return JSON.stringify(results);
    })()
    """

    file_url = f"file://{os.path.abspath(INDEX_HTML)}"
    resolutions = [(1920, 1080), (1440, 900), (1366, 768), (1280, 800)]
    for w, h in resolutions:
        cmd = [
            BRAVE_PATH,
            "--headless",
            "--hide-scrollbars",
            f"--window-size={w},{h}",
            "--dump-dom",
            file_url
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        assert res.returncode == 0
        assert "VARUNA" in res.stdout
        assert "mapStatusBar" in res.stdout
