// VARUNA — Earth Observation & Flood Intelligence Workspace Logic
// High-grade scientific cartography & interactive multi-workspace controller

(function () {
  'use strict';

  // 1. App State
  const state = {
    activeWorkspace: 'comparison', // 'comparison' | 'change' | 'exposure' | 'validation' | 'copilot'
    currentSector: 'corridor',     // 'corridor' | 'aoi03' | 'aoi01' | 'aoi02' | 'all'
    activeBasemap: 'topo',         // 'topo' | 'satellite' (Default: restrained Topographic relief)
    sarUnderlay: false,            // SAR backscatter underlay in workspaces 2, 3, 4
    mmuFilter: 'all',              // 'all' (raw 10m) | 'mmu1000' (contiguous >= 1,000 m2)
    changeLayerType: 'classified', // 'classified' | 'diff' | 'water' | 'debris'
    changeOpacity: 0.85,
    swipePosition: 0.5,            // 0.0 to 1.0 (fraction of map width)
    comparisonMode: 'swipe',       // 'swipe' | 'pre' | 'post'
    comparisonSector: 'full',      // 'full' | 'corridor' | 'aoi03' | 'aoi01'
    highlightChanges: false,       // Authentic SAR backscatter change overlay (muted blue flood / soft amber debris)
    highlightOpacity: 0.35,        // Default 35% opacity for subtle, professional overlay (range 0% to 75%)
    copilotLang: 'en',             // 'en' | 'ne'
    panelOpen: true,
    inspectedFeature: null
  };

  // Geographic Extents & Bounds
  const EXTENTS = {
    full: { bounds: [[27.8499, 85.0500], [28.2500, 85.4000]], name: 'Full Analysis Extent (1,526 km²)' },
    corridor: { bounds: [[27.8700, 85.0900], [28.2100, 85.3800]], center: [28.04, 85.23], zoom: 12, name: 'Trishuli River Corridor' },
    aoi03: { center: [27.918, 85.155], zoom: 13, name: 'Bidur / Battar Confluence (AOI03)' },
    aoi01: { center: [28.160, 85.340], zoom: 14, name: 'Syapru Besi Gorge (AOI01)' },
    aoi02: { center: [28.230, 85.375], zoom: 14, name: 'Timure Border Corridor (AOI02)' }
  };

  const RASTER_BOUNDS = [
    [27.8499136746345, 85.04996096098255],
    [28.2500164946345, 85.40002847098255]
  ];

  // 2. Map Initialization
  const map = L.map('map', {
    center: [28.050, 85.225],
    zoom: 12,
    minZoom: 9,
    maxZoom: 18,
    zoomSnap: 0.25,
    zoomDelta: 0.5,
    zoomControl: false,
    attributionControl: true
  });

  // Basemap Tile Layers (Coherent, 100% Opaque, No Tile Gaps)
  const basemaps = {
    topo: L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', {
      attribution: 'Esri, USGS, NOAA (Topographic Terrain)',
      maxZoom: 18,
      opacity: 1.0
    }),
    satellite: L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
      attribution: 'Esri, Maxar, Earthstar (Satellite Context; non-contemporaneous)',
      maxZoom: 19,
      opacity: 1.0
    })
  };
  basemaps[state.activeBasemap].addTo(map);

  function setBasemap(name) {
    if (!basemaps[name] || state.activeBasemap === name) return;
    map.removeLayer(basemaps[state.activeBasemap]);
    state.activeBasemap = name;
    basemaps[name].addTo(map);
    const btn = document.getElementById('btnToggleBasemapStatus');
    if (btn) btn.textContent = name === 'topo' ? 'Basemap: Topo Relief' : 'Basemap: Satellite Ortho';
    const sel = document.getElementById('selBasemap');
    if (sel) sel.value = name;
  }

  // Custom Map Panes (Strict Cartographic Hierarchy)
  // 1. Basemap (pane 200) -> 2. AOI neatline -> 3. SAR underlay -> 4. Pre/Post swipe -> 5. Hazard -> 6. Vectors
  map.createPane('paneAoiFrame');
  map.getPane('paneAoiFrame').style.zIndex = 205;

  map.createPane('paneSarUnderlay');
  map.getPane('paneSarUnderlay').style.zIndex = 210;
  map.getPane('paneSarUnderlay').classList.add('pane-sar-underlay');

  map.createPane('panePreRaster');
  map.getPane('panePreRaster').style.zIndex = 215;

  map.createPane('panePostRaster');
  map.getPane('panePostRaster').style.zIndex = 220;

  map.createPane('paneHazardRaster');
  map.getPane('paneHazardRaster').style.zIndex = 230;

  map.createPane('paneReference');
  map.getPane('paneReference').style.zIndex = 240;

  map.createPane('paneVectors');
  map.getPane('paneVectors').style.zIndex = 250;

  // Analysis Domain Framing Rectangle (Subtle, Restrained Neatline — Zero Fill)
  const aoiFrame = L.rectangle(RASTER_BOUNDS, {
    pane: 'paneAoiFrame',
    color: '#176B52',
    weight: 1.2,
    dashArray: '5, 5',
    fill: false,
    interactive: false
  }).addTo(map);

  // 3. Raster Layers (Sentinel-1 Intensity & Hazard Classification)
  const rasters = {
    pre: L.imageOverlay('rasters/s1_pre_intensity_half.webp', RASTER_BOUNDS, {
      pane: 'panePreRaster',
      opacity: 1.0,
      interactive: false
    }),
    post: L.imageOverlay('rasters/s1_post_intensity_half.webp', RASTER_BOUNDS, {
      pane: 'panePostRaster',
      opacity: 1.0,
      interactive: false
    }),
    sarUnderlay: L.imageOverlay('rasters/s1_post_intensity_half.webp', RASTER_BOUNDS, {
      pane: 'paneSarUnderlay',
      opacity: 0.55,
      interactive: false
    }),
    changeHighlight: L.imageOverlay('rasters/sar_change_highlight_half.png', RASTER_BOUNDS, {
      pane: 'paneHazardRaster',
      opacity: state.highlightOpacity,
      className: 'layer-sar-change-highlight',
      interactive: false
    }),
    classified: L.imageOverlay('rasters/hazard_classified_half.png', RASTER_BOUNDS, {
      pane: 'paneHazardRaster',
      opacity: state.changeOpacity,
      interactive: false
    }),
    filtered: L.imageOverlay('rasters/hazard_filtered_half.png', RASTER_BOUNDS, {
      pane: 'paneHazardRaster',
      opacity: state.changeOpacity,
      interactive: false
    }),
    diff: L.imageOverlay('rasters/s1_diff_continuous_half.png', RASTER_BOUNDS, {
      pane: 'paneHazardRaster',
      opacity: state.changeOpacity,
      interactive: false
    }),
    water: L.imageOverlay('rasters/hazard_water_half.png', RASTER_BOUNDS, {
      pane: 'paneHazardRaster',
      opacity: state.changeOpacity,
      interactive: false
    }),
    debris: L.imageOverlay('rasters/hazard_debris_half.png', RASTER_BOUNDS, {
      pane: 'paneHazardRaster',
      opacity: state.changeOpacity,
      interactive: false
    })
  };

  // 4. Vector Layers & Scale-Dependent Infrastructure
  let buildingsGeoJson = null;
  const clusterMarkersLayer = L.layerGroup();
  const individualBldgsLayer = L.layerGroup({ pane: 'paneVectors' });

  // Known Building Clusters (at zoom <= 12)
  const REGIONAL_CLUSTERS = [
    { name: 'Bidur / Battar Cluster', latlng: [27.915, 85.155], count: 3124, destroyed: 2310 },
    { name: 'Betrawati / Mailung', latlng: [28.025, 85.190], count: 412, destroyed: 320 },
    { name: 'Syapru Besi Gorge', latlng: [28.160, 85.340], count: 280, destroyed: 183 }
  ];

  function renderClusterMarkers() {
    clusterMarkersLayer.clearLayers();
    REGIONAL_CLUSTERS.forEach(c => {
      const icon = L.divIcon({
        className: 'cluster-circle',
        html: `<span>${c.count}</span>`,
        iconSize: [36, 36]
      });
      const marker = L.marker(c.latlng, { icon: icon });
      marker.bindPopup(`
        <div style="font-size:11px; font-weight:700; color:var(--text-primary); margin-bottom:4px;">${c.name}</div>
        <div style="font-size:10.5px; color:var(--text-secondary);">
          Total Surveyed Structures: <strong>${c.count}</strong><br>
          Confirmed Destroyed: <strong style="color:var(--status-destroyed);">${c.destroyed}</strong><br>
          <em>Zoom in to level 13+ to inspect individual structures.</em>
        </div>
      `);
      marker.on('click', () => {
        map.setView(c.latlng, 13);
      });
      clusterMarkersLayer.addLayer(marker);
    });
  }
  renderClusterMarkers();

  const vectorLayers = {
    emsr: L.geoJSON(null, {
      pane: 'paneReference',
      style: {
        color: '#6D28D9',
        weight: 2,
        dashArray: '4, 4',
        fillColor: '#6D28D9',
        fillOpacity: 0.15
      },
      onEachFeature: setupFeatureInspection
    }),
    roads: L.geoJSON(null, {
      pane: 'paneVectors',
      style: (feature) => {
        const exp = feature.properties.potential_exposure || 'NO_ANOMALY';
        const grade = feature.properties.damage_gra || '';
        let color = '#788580';
        let weight = 1.2;
        let opacity = 0.75;
        if (grade === 'Destroyed') {
          color = '#B91C1C';
          weight = 1.8;
          opacity = 0.9;
        } else if (exp.includes('FLOOD')) {
          color = '#1D63B8';
          weight = 1.8;
          opacity = 0.9;
        } else if (exp.includes('DEBRIS')) {
          color = '#C2611B';
          weight = 1.8;
          opacity = 0.9;
        }
        return { color: color, weight: weight, opacity: opacity };
      },
      onEachFeature: setupFeatureInspection
    }),
    highway: L.geoJSON(null, {
      pane: 'paneVectors',
      style: {
        color: '#0D9488',
        weight: 2.8,
        opacity: 0.95
      },
      onEachFeature: setupFeatureInspection
    })
  };

  // Update infrastructure scale-dependency on map zoom
  function updateInfrastructureScale() {
    if (state.activeWorkspace !== 'exposure') return;

    const currentZoom = map.getZoom();
    if (currentZoom >= 13) {
      if (map.hasLayer(clusterMarkersLayer)) map.removeLayer(clusterMarkersLayer);
      if (!map.hasLayer(individualBldgsLayer)) individualBldgsLayer.addTo(map);
    } else {
      if (map.hasLayer(individualBldgsLayer)) map.removeLayer(individualBldgsLayer);
      if (!map.hasLayer(clusterMarkersLayer)) clusterMarkersLayer.addTo(map);
    }
  }

  map.on('zoomend', updateInfrastructureScale);

  // Load Vector GeoJSON Data
  async function loadVectorData() {
    try {
      const [emsrRes, bldgsRes, roadsRes, hwRes] = await Promise.all([
        fetch('layers/emsr927_event_extents.geojson').then(r => r.json()),
        fetch('layers/exposed_buildings_dashboard.geojson').then(r => r.json()),
        fetch('layers/exposed_roads_dashboard.geojson').then(r => r.json()),
        fetch('layers/major_highways_trishuli.geojson').then(r => r.json())
      ]);
      vectorLayers.emsr.addData(emsrRes);
      vectorLayers.roads.addData(roadsRes);
      vectorLayers.highway.addData(hwRes);

      // Build individual building markers
      buildingsGeoJson = bldgsRes;
      individualBldgsLayer.clearLayers();
      L.geoJSON(bldgsRes, {
        pointToLayer: (feature, latlng) => {
          const grade = feature.properties.damage_gra || 'Unknown';
          let fillColor = '#64748B';
          let radius = 3.0;
          if (grade === 'Destroyed') {
            fillColor = '#B91C1C';
            radius = 3.5;
          } else if (grade === 'Damaged') {
            fillColor = '#C2410C';
          } else if (grade === 'Possibly damaged') {
            fillColor = '#B45309';
          }
          return L.circleMarker(latlng, {
            radius: radius,
            fillColor: fillColor,
            color: '#FFFFFF',
            weight: 0.4,
            opacity: 0.9,
            fillOpacity: 0.85
          });
        },
        onEachFeature: setupFeatureInspection
      }).eachLayer(layer => individualBldgsLayer.addLayer(layer));

      console.log('Vector layers and scale-dependent buildings loaded.');
    } catch (err) {
      console.error('Failed to load vector layers:', err);
    }
  }

  // 5. Feature Click & Inspection Handler
  function setupFeatureInspection(feature, layer) {
    layer.on('click', (e) => {
      L.DomEvent.stopPropagation(e);
      state.inspectedFeature = {
        properties: feature.properties,
        latlng: e.latlng
      };
      renderInspectorCard();
    });
  }

  // 6. Interactive Swipe Divider Controller
  const swipeContainer = document.getElementById('swipeCurtainContainer');
  const swipeLine = document.getElementById('swipeDividerLine');
  const swipeHandle = document.getElementById('swipeDividerHandle');
  let isDraggingSwipe = false;

  function updateSwipeDivider(clientX) {
    if (state.activeWorkspace !== 'comparison') return;
    const mapBox = map.getContainer().getBoundingClientRect();
    if (clientX === undefined) {
      clientX = mapBox.left + (mapBox.width * state.swipePosition);
    }
    let x = clientX - mapBox.left;
    x = Math.max(10, Math.min(mapBox.width - 10, x));
    state.swipePosition = x / mapBox.width;

    if (swipeLine) swipeLine.style.left = `${x}px`;

    const postEl = rasters.post.getElement();
    const classEl = (state.highlightChanges && map.hasLayer(rasters.changeHighlight)) ? rasters.changeHighlight.getElement() : null;
    if (!postEl) return;

    if (state.comparisonMode === 'pre') {
      postEl.style.clipPath = 'inset(0 0 0 100%)';
      postEl.style.webkitClipPath = 'inset(0 0 0 100%)';
      if (classEl) {
        classEl.style.clipPath = 'inset(0 0 0 100%)';
        classEl.style.webkitClipPath = 'inset(0 0 0 100%)';
      }
      return;
    }
    if (state.comparisonMode === 'post') {
      postEl.style.clipPath = 'none';
      postEl.style.webkitClipPath = 'none';
      if (classEl) {
        classEl.style.clipPath = 'none';
        classEl.style.webkitClipPath = 'none';
      }
      return;
    }

    // Swipe divider mode: accurately align raster clipping with screen divider position
    const postBox = postEl.getBoundingClientRect();
    const dividerClientX = mapBox.left + x;
    const localX = dividerClientX - postBox.left;

    let clipStr = 'none';
    if (localX <= 0) {
      clipStr = 'none';
    } else if (localX >= postBox.width) {
      clipStr = 'inset(0 0 0 100%)';
    } else {
      clipStr = `inset(0 0 0 ${localX}px)`;
    }

    postEl.style.clipPath = clipStr;
    postEl.style.webkitClipPath = clipStr;
    if (classEl) {
      classEl.style.clipPath = clipStr;
      classEl.style.webkitClipPath = clipStr;
    }
  }

  swipeHandle.addEventListener('mousedown', (e) => {
    isDraggingSwipe = true;
    e.preventDefault();
  });

  swipeLine.addEventListener('mousedown', (e) => {
    isDraggingSwipe = true;
    e.preventDefault();
  });

  window.addEventListener('mousemove', (e) => {
    if (!isDraggingSwipe) return;
    updateSwipeDivider(e.clientX);
  });

  window.addEventListener('mouseup', () => {
    isDraggingSwipe = false;
  });

  swipeHandle.addEventListener('touchstart', (e) => {
    isDraggingSwipe = true;
  }, { passive: true });

  window.addEventListener('touchmove', (e) => {
    if (!isDraggingSwipe || !e.touches[0]) return;
    updateSwipeDivider(e.touches[0].clientX);
  }, { passive: true });

  window.addEventListener('touchend', () => {
    isDraggingSwipe = false;
  });

  map.on('move zoom viewreset resize', () => {
    if (state.activeWorkspace === 'comparison' && state.comparisonMode === 'swipe') {
      updateSwipeDivider();
    }
  });

  window.addEventListener('resize', () => {
    if (state.activeWorkspace === 'comparison' && state.comparisonMode === 'swipe') {
      updateSwipeDivider();
    }
  });

  rasters.pre.on('load', () => {
    if (state.activeWorkspace === 'comparison') updateSwipeDivider();
  });
  rasters.post.on('load', () => {
    if (state.activeWorkspace === 'comparison') updateSwipeDivider();
  });

  // 7. Workspace Switcher & Toolbar Rendering
  const workspaceButtons = {
    comparison: document.getElementById('btnWsComparison'),
    change: document.getElementById('btnWsChange'),
    exposure: document.getElementById('btnWsExposure'),
    validation: document.getElementById('btnWsValidation'),
    copilot: document.getElementById('btnWsCopilot')
  };

  Object.entries(workspaceButtons).forEach(([wsKey, btn]) => {
    if (btn) btn.addEventListener('click', () => switchWorkspace(wsKey));
  });

  function switchWorkspace(wsKey, preserveExtent = false) {
    state.activeWorkspace = wsKey;
    Object.values(workspaceButtons).forEach(b => b.classList.remove('active'));
    workspaceButtons[wsKey].classList.add('active');

    // Default basemap per workspace (Satellite for Comparison; Restrained Topo for Change, Exposure, Validation)
    if (wsKey === 'comparison') {
      setBasemap('satellite');
    } else {
      setBasemap('topo');
    }

    // Clean up layer state
    Object.values(rasters).forEach(r => map.removeLayer(r));
    Object.values(vectorLayers).forEach(v => map.removeLayer(v));
    if (map.hasLayer(clusterMarkersLayer)) map.removeLayer(clusterMarkersLayer);
    if (map.hasLayer(individualBldgsLayer)) map.removeLayer(individualBldgsLayer);
    swipeContainer.classList.remove('active');
    const swipeLabelsEl = document.getElementById('swipeLabels');
    if (swipeLabelsEl) swipeLabelsEl.style.display = 'none';

    // Apply Workspace-Specific Layers & Extents
    if (wsKey === 'comparison') {
      rasters.pre.addTo(map);
      rasters.post.addTo(map);
      if (state.highlightChanges) {
        rasters.changeHighlight.setOpacity(state.highlightOpacity);
        rasters.changeHighlight.addTo(map);
      }
      if (state.comparisonMode === 'swipe') {
        swipeContainer.classList.add('active');
        if (swipeLabelsEl) swipeLabelsEl.style.display = 'flex';
      }
      if (!preserveExtent) {
        if (state.comparisonSector === 'full') {
          map.fitBounds(RASTER_BOUNDS, { padding: [10, 10] });
        } else if (state.comparisonSector === 'corridor') {
          map.fitBounds(EXTENTS.corridor.bounds, { padding: [15, 15] });
        } else if (EXTENTS[state.comparisonSector]) {
          map.setView(EXTENTS[state.comparisonSector].center, EXTENTS[state.comparisonSector].zoom);
        }
      }
      setTimeout(() => {
        updateSwipeDivider();
      }, 50);
    } else if (wsKey === 'change') {
      if (state.sarUnderlay) rasters.sarUnderlay.addTo(map);
      applyChangeRaster();
      if (!preserveExtent) {
        // Default to meaningful river corridor
        map.fitBounds(EXTENTS.corridor.bounds, { padding: [15, 15] });
      }
    } else if (wsKey === 'exposure') {
      if (state.sarUnderlay) rasters.sarUnderlay.addTo(map);
      applyChangeRaster();
      vectorLayers.highway.addTo(map);
      vectorLayers.roads.addTo(map);
      updateInfrastructureScale();
      if (!preserveExtent) {
        map.fitBounds(EXTENTS.corridor.bounds, { padding: [15, 15] });
      }
    } else if (wsKey === 'validation') {
      if (state.sarUnderlay) rasters.sarUnderlay.addTo(map);
      applyChangeRaster();
      vectorLayers.emsr.addTo(map);
      vectorLayers.highway.addTo(map);
      if (!preserveExtent) {
        zoomToSector('aoi03');
      }
    } else if (wsKey === 'copilot') {
      if (state.sarUnderlay) rasters.sarUnderlay.addTo(map);
      applyChangeRaster();
      vectorLayers.highway.addTo(map);
      vectorLayers.roads.addTo(map);
      vectorLayers.emsr.addTo(map);
      if (!preserveExtent) {
        map.fitBounds(EXTENTS.corridor.bounds, { padding: [15, 15] });
      }
    }

    renderWorkspaceToolbar();
    renderContextualPanel();
    renderLegend();
  }

  function applyChangeRaster() {
    Object.values(rasters).forEach(r => {
      if (r !== rasters.pre && r !== rasters.post && r !== rasters.sarUnderlay) map.removeLayer(r);
    });

    let activeRaster = (state.mmuFilter === 'mmu1000') ? rasters.filtered : rasters.classified;
    if (state.changeLayerType === 'diff') activeRaster = rasters.diff;
    else if (state.changeLayerType === 'water') activeRaster = rasters.water;
    else if (state.changeLayerType === 'debris') activeRaster = rasters.debris;

    activeRaster.setOpacity(state.changeOpacity);
    activeRaster.addTo(map);
  }

  // 8. Render Floating Workspace Toolbar
  const toolbarContainer = document.getElementById('workspaceToolbar');

  function renderWorkspaceToolbar() {
    const ws = state.activeWorkspace;
    let html = '';

    if (ws === 'comparison') {
      html = `
        <div class="toolbar-segment-group">
          <button class="toolbar-segment-btn ${state.comparisonMode === 'swipe' ? 'active' : ''}" data-mode="swipe">Swipe Divider</button>
          <button class="toolbar-segment-btn ${state.comparisonMode === 'pre' ? 'active' : ''}" data-mode="pre" title="Pre-Event Sentinel-1 SAR (Aug 24, 2026)">Pre (Aug 24)</button>
          <button class="toolbar-segment-btn ${state.comparisonMode === 'post' ? 'active' : ''}" data-mode="post" title="Post-Event Sentinel-1 SAR (Sept 5, 2026)">Post (Sept 5)</button>
        </div>
        <div class="toolbar-divider"></div>
        <span class="toolbar-control-label">Framing:</span>
        <select class="toolbar-select" id="selCompPreset">
          <option value="full" ${state.comparisonSector === 'full' ? 'selected' : ''}>Full AOI (SAR Domain)</option>
          <option value="corridor" ${state.comparisonSector === 'corridor' ? 'selected' : ''}>Trishuli Corridor</option>
          <option value="aoi03" ${state.comparisonSector === 'aoi03' ? 'selected' : ''}>Bidur (AOI03)</option>
          <option value="aoi01" ${state.comparisonSector === 'aoi01' ? 'selected' : ''}>Syapru Besi (AOI01)</option>
        </select>
        <div class="toolbar-divider"></div>
        <button class="toolbar-segment-btn highlight-toggle ${state.highlightChanges ? 'active' : ''}" id="btnToggleHighlightChanges" title="Toggle authentic SAR backscatter change overlay (35% default opacity)">Highlight Changes ${state.highlightChanges ? '● ON' : '○ OFF'}</button>
        ${state.highlightChanges ? `
          <span class="toolbar-control-label" style="margin-left:4px;">Opacity:</span>
          <input type="range" id="rngHighlightOpacity" min="0" max="75" value="${Math.round(state.highlightOpacity * 100)}" style="width:58px; height:4px; vertical-align:middle; cursor:pointer;" title="Adjust Change Overlay Opacity (0% - 75%)">
          <span id="valHighlightOpacity" style="font-size:10px; font-family:var(--font-mono); color:var(--text-tertiary); width:24px; text-align:right;">${Math.round(state.highlightOpacity * 100)}%</span>
        ` : ''}
      `;
    } else if (ws === 'change') {
      html = `
        <div class="toolbar-segment-group">
          <button class="toolbar-segment-btn ${state.changeLayerType === 'classified' ? 'active' : ''}" data-type="classified" title="Classified Hazard: Inundation & Debris">Hazard</button>
          <button class="toolbar-segment-btn ${state.changeLayerType === 'diff' ? 'active' : ''}" data-type="diff" title="Continuous Backscatter Difference Δσ° (dB)">Δσ° (dB)</button>
          <button class="toolbar-segment-btn ${state.changeLayerType === 'water' ? 'active' : ''}" data-type="water" title="Water Backscatter Drop Only (≤ -2.5 dB)">Water</button>
          <button class="toolbar-segment-btn ${state.changeLayerType === 'debris' ? 'active' : ''}" data-type="debris" title="Debris Backscatter Coarsening (≥ +2.0 dB)">Debris</button>
        </div>
        <div class="toolbar-divider"></div>
        <span class="toolbar-control-label">Morphology:</span>
        <div class="toolbar-segment-group">
          <button class="toolbar-segment-btn ${state.mmuFilter === 'all' ? 'active' : ''}" data-mmu="all" title="Raw 10m per-pixel decision (126.6 km² flood / 108.2 km² debris; includes steep-slope speckle)">Raw 10m</button>
          <button class="toolbar-segment-btn ${state.mmuFilter === 'mmu1000' ? 'active' : ''}" data-mmu="mmu1000" title="Contiguous clusters ≥ 1,000 m² (MMU filter removes isolated mountain speckle)">MMU ≥1k m²</button>
        </div>
        <div class="toolbar-divider"></div>
        <span class="toolbar-control-label">Extent:</span>
        <select class="toolbar-select" id="selChangeExtent">
          <option value="corridor">River Corridor</option>
          <option value="full">Full Domain</option>
        </select>
        <div class="toolbar-divider"></div>
        <button class="toolbar-segment-btn ${state.sarUnderlay ? 'active' : ''}" id="btnToggleSarUnderlay" title="Toggle blended Sentinel-1 SAR intensity underlay">
          SAR ${state.sarUnderlay ? '● ON' : '○ OFF'}
        </button>
        <div class="toolbar-divider"></div>
        <span class="toolbar-control-label" title="Layer Opacity">Opacity:</span>
        <input type="range" id="rngOpacity" min="20" max="100" value="${Math.round(state.changeOpacity * 100)}" style="width:48px; cursor:pointer;" title="Adjust Layer Opacity">
      `;
    } else if (ws === 'exposure') {
      const zoom = map.getZoom();
      html = `
        <span class="toolbar-control-label">Sector:</span>
        <select class="toolbar-select" id="selExposureSector">
          <option value="corridor" ${state.currentSector === 'corridor' ? 'selected' : ''}>Trishuli River Corridor</option>
          <option value="aoi03" ${state.currentSector === 'aoi03' ? 'selected' : ''}>Bidur Confluence (AOI03)</option>
          <option value="aoi01" ${state.currentSector === 'aoi01' ? 'selected' : ''}>Syapru Besi Gorge (AOI01)</option>
          <option value="aoi02" ${state.currentSector === 'aoi02' ? 'selected' : ''}>Timure Border (AOI02)</option>
          <option value="all" ${state.currentSector === 'all' ? 'selected' : ''}>Entire Basin (1,526 km²)</option>
        </select>
        <div class="toolbar-divider"></div>
        <button class="toolbar-segment-btn ${state.sarUnderlay ? 'active' : ''}" id="btnToggleSarUnderlay" title="Toggle blended Sentinel-1 SAR intensity underlay">
          SAR ${state.sarUnderlay ? '● ON' : '○ OFF'}
        </button>
        <div class="toolbar-divider"></div>
        <span class="zoom-level-notice">${zoom >= 13 ? '● Level 13+: 3,816 Surveyed Buildings' : '○ Level ' + zoom + ': Regional Building Clusters (Zoom in for points)'}</span>
      `;
    } else if (ws === 'validation') {
      html = `
        <span class="toolbar-control-label">Sector:</span>
        <div class="toolbar-segment-group">
          <button class="toolbar-segment-btn ${state.currentSector === 'aoi03' ? 'active' : ''}" data-sector="aoi03" title="Bidur Confluence Held-Out AOI03">Bidur (AOI03)</button>
          <button class="toolbar-segment-btn ${state.currentSector === 'aoi01' ? 'active' : ''}" data-sector="aoi01" title="Syapru Besi Gorge Held-Out AOI01">Syapru Besi (AOI01)</button>
          <button class="toolbar-segment-btn ${state.currentSector === 'corridor' ? 'active' : ''}" data-sector="corridor" title="River Corridor">Corridor</button>
          <button class="toolbar-segment-btn ${state.currentSector === 'all' ? 'active' : ''}" data-sector="all" title="Basin Overview">Overview</button>
        </div>
        <div class="toolbar-divider"></div>
        <button class="toolbar-segment-btn ${state.sarUnderlay ? 'active' : ''}" id="btnToggleSarUnderlay" title="Toggle blended Sentinel-1 SAR intensity underlay">
          SAR ${state.sarUnderlay ? '● ON' : '○ OFF'}
        </button>
      `;
    } else if (ws === 'copilot') {
      html = `
        <div class="toolbar-segment-group">
          <button class="toolbar-segment-btn ${state.copilotLang === 'en' ? 'active' : ''}" data-clang="en">English (EN)</button>
          <button class="toolbar-segment-btn ${state.copilotLang === 'ne' ? 'active' : ''}" data-clang="ne">नेपाली (NE)</button>
        </div>
        <div class="toolbar-divider"></div>
        <button class="toolbar-segment-btn" id="btnCopilotSitrepPreview" title="View Full Operational Situation Report">Operational SitRep</button>
      `;
    }

    toolbarContainer.innerHTML = html;
    bindToolbarEvents();
  }

  function bindToolbarEvents() {
    const ws = state.activeWorkspace;

    // Common SAR Underlay Toggle
    const btnSar = document.getElementById('btnToggleSarUnderlay');
    if (btnSar) {
      btnSar.addEventListener('click', () => {
        state.sarUnderlay = !state.sarUnderlay;
        if (state.sarUnderlay) {
          if (!map.hasLayer(rasters.sarUnderlay)) rasters.sarUnderlay.addTo(map);
        } else {
          if (map.hasLayer(rasters.sarUnderlay)) map.removeLayer(rasters.sarUnderlay);
        }
        renderWorkspaceToolbar();
      });
    }

    if (ws === 'comparison') {
      toolbarContainer.querySelectorAll('[data-mode]').forEach(btn => {
        btn.addEventListener('click', () => {
          const mode = btn.dataset.mode;
          state.comparisonMode = mode;
          const postEl = rasters.post.getElement();
          const swipeLabelsEl = document.getElementById('swipeLabels');
          if (mode === 'swipe') {
            swipeContainer.classList.add('active');
            if (swipeLabelsEl) swipeLabelsEl.style.display = 'flex';
            updateSwipeDivider();
          } else if (mode === 'pre') {
            swipeContainer.classList.remove('active');
            if (swipeLabelsEl) swipeLabelsEl.style.display = 'none';
            if (postEl) {
              postEl.style.clipPath = 'inset(0 0 0 100%)';
              postEl.style.webkitClipPath = 'inset(0 0 0 100%)';
            }
          } else if (mode === 'post') {
            swipeContainer.classList.remove('active');
            if (swipeLabelsEl) swipeLabelsEl.style.display = 'none';
            if (postEl) {
              postEl.style.clipPath = 'none';
              postEl.style.webkitClipPath = 'none';
            }
          }
          renderWorkspaceToolbar();
        });
      });
      const selPreset = document.getElementById('selCompPreset');
      if (selPreset) {
        selPreset.addEventListener('change', (e) => {
          const val = e.target.value;
          state.comparisonSector = val;
          if (val === 'full') map.fitBounds(RASTER_BOUNDS, { padding: [10, 10] });
          else if (val === 'corridor') map.fitBounds(EXTENTS.corridor.bounds, { padding: [15, 15] });
          else if (EXTENTS[val]) map.setView(EXTENTS[val].center, EXTENTS[val].zoom);
          setTimeout(() => updateSwipeDivider(), 50);
        });
      }

      const btnHighlight = document.getElementById('btnToggleHighlightChanges');
      if (btnHighlight) {
        btnHighlight.addEventListener('click', () => {
          state.highlightChanges = !state.highlightChanges;
          if (state.highlightChanges) {
            rasters.changeHighlight.setOpacity(state.highlightOpacity);
            rasters.changeHighlight.addTo(map);
            if (state.comparisonSector === 'full') {
              state.comparisonSector = 'corridor';
              map.fitBounds(EXTENTS.corridor.bounds, { padding: [15, 15] });
              const selCompPreset = document.getElementById('selCompPreset');
              if (selCompPreset) selCompPreset.value = 'corridor';
            }
          } else {
            if (map.hasLayer(rasters.changeHighlight)) {
              map.removeLayer(rasters.changeHighlight);
            }
          }
          updateSwipeDivider();
          renderWorkspaceToolbar();
          renderLegend();
        });
      }

      const rngHighlight = document.getElementById('rngHighlightOpacity');
      if (rngHighlight) {
        rngHighlight.addEventListener('input', (e) => {
          state.highlightOpacity = parseFloat(e.target.value) / 100.0;
          rasters.changeHighlight.setOpacity(state.highlightOpacity);
          const valEl = document.getElementById('valHighlightOpacity');
          if (valEl) valEl.textContent = `${Math.round(state.highlightOpacity * 100)}%`;
        });
      }
    } else if (ws === 'change') {
      toolbarContainer.querySelectorAll('[data-type]').forEach(btn => {
        btn.addEventListener('click', () => {
          state.changeLayerType = btn.dataset.type;
          applyChangeRaster();
          renderWorkspaceToolbar();
        });
      });
      toolbarContainer.querySelectorAll('[data-mmu]').forEach(btn => {
        btn.addEventListener('click', () => {
          state.mmuFilter = btn.dataset.mmu;
          applyChangeRaster();
          renderWorkspaceToolbar();
          renderContextualPanel();
        });
      });
      const selExt = document.getElementById('selChangeExtent');
      if (selExt) {
        selExt.addEventListener('change', (e) => {
          if (e.target.value === 'full') map.fitBounds(RASTER_BOUNDS, { padding: [15, 15] });
          else map.fitBounds(EXTENTS.corridor.bounds, { padding: [15, 15] });
        });
      }
      const rng = document.getElementById('rngOpacity');
      if (rng) {
        rng.addEventListener('input', (e) => {
          state.changeOpacity = parseFloat(e.target.value) / 100.0;
          applyChangeRaster();
        });
      }
    } else if (ws === 'exposure') {
      const sel = document.getElementById('selExposureSector');
      if (sel) {
        sel.addEventListener('change', (e) => {
          zoomToSector(e.target.value);
        });
      }
    } else if (ws === 'validation') {
      toolbarContainer.querySelectorAll('[data-sector]').forEach(btn => {
        btn.addEventListener('click', () => {
          zoomToSector(btn.dataset.sector);
          renderWorkspaceToolbar();
          renderContextualPanel();
        });
      });
    } else if (ws === 'copilot') {
      toolbarContainer.querySelectorAll('[data-clang]').forEach(btn => {
        btn.addEventListener('click', () => {
          state.copilotLang = btn.dataset.clang;
          renderWorkspaceToolbar();
          renderContextualPanel();
        });
      });
      const btnSitrep = document.getElementById('btnCopilotSitrepPreview');
      if (btnSitrep) {
        btnSitrep.addEventListener('click', () => {
          triggerCopilotBriefingModal();
        });
      }
    }
  }

  function zoomToSector(sectorKey) {
    state.currentSector = sectorKey;
    if (sectorKey === 'all') {
      map.fitBounds(RASTER_BOUNDS, { padding: [15, 15] });
    } else if (sectorKey === 'corridor') {
      map.fitBounds(EXTENTS.corridor.bounds, { padding: [15, 15] });
    } else if (EXTENTS[sectorKey]) {
      map.setView(EXTENTS[sectorKey].center, EXTENTS[sectorKey].zoom);
    }
    renderContextualPanel();
  }

  // 9. Render Right Contextual Analysis Panel
  const panelTitle = document.getElementById('panelTitle');
  const panelBadge = document.getElementById('panelBadge');
  const panelBody = document.getElementById('panelBody');

  function renderContextualPanel() {
    const ws = state.activeWorkspace;

    if (ws === 'comparison') {
      panelTitle.textContent = 'Satellite Comparison';
      panelBadge.textContent = 'C-SAR Orbit 19';
      panelBody.innerHTML = `
        <div class="analysis-section">
          <div class="section-label">Observation Telemetry</div>
          <div class="metric-grid-2x2">
            <div class="metric-card accent-primary">
              <span class="metric-card-label">Pre-Event Scene</span>
              <span class="metric-card-value">Aug 24, 2026</span>
              <span class="metric-card-sub">00:18:44 UTC (2d Pre)</span>
            </div>
            <div class="metric-card accent-primary">
              <span class="metric-card-label">Post-Event Scene</span>
              <span class="metric-card-value">Sept 05, 2026</span>
              <span class="metric-card-sub">00:18:44 UTC (10d Post)</span>
            </div>
          </div>
        </div>

        <div class="scientific-table-wrap">
          <table class="scientific-table">
            <thead><tr><th>Parameter</th><th>Value</th></tr></thead>
            <tbody>
              <tr><td>Relative Orbit</td><td class="bold">19 (Descending)</td></tr>
              <tr><td>Polarization</td><td>VV (Co-polarized)</td></tr>
              <tr><td>Repeat Cycle</td><td class="num">12.0 days</td></tr>
              <tr><td>Radiometric LUT</td><td>IPF 004.03 A_sigma</td></tr>
              <tr><td>Contrast Stretch</td><td class="num">-22.0 to +2.0 dB</td></tr>
              <tr><td>Native Resolution</td><td class="bold num">10 m Level-1 GRD</td></tr>
              <tr><td>Display Rendering</td><td class="num">18.6 m/px Web Mercator</td></tr>
              <tr><td>Valid Grid Overlap</td><td class="bold num" style="color:var(--accent-primary);">100.0% (0 NoData px)</td></tr>
            </tbody>
          </table>
        </div>

        <details class="scientific-accordion" open>
          <summary>Radar Backscatter Physics</summary>
          <div class="accordion-content">
            Calibrated SAR intensity reflects surface roughness and dielectric permittivity. Smooth standing water causes specular reflection away from the radar antenna, producing dark backscatter drops. Rugged terrain, coarsened debris, and boulder deposits cause diffuse volume scattering, appearing bright.
          </div>
        </details>

        <details class="scientific-accordion caveat" open>
          <summary>10-Day Acquisition Lag & Peak Flood Note</summary>
          <div class="accordion-content">
            <strong>Post-Event Scene: Sept 05, 2026 (10 days post-peak).</strong> Detections capture residual inundation, saturated alluvium, and scoured gravel bars rather than peak flood depth (Aug 26). Lowland floodwaters had receded significantly, while braided gravel bed coarsening remained clearly detectable.
          </div>
        </details>

        <details class="scientific-accordion">
          <summary>Surface Anomalies vs. Structural Failure</summary>
          <div class="accordion-content">
            SAR backscatter changes (Δσ°) identify physical surface anomalies, not ground-verified structural collapse. Radar layover, mountain shadow, and steep Himalayan slopes can introduce false candidates. Contiguous morphology filtering (MMU ≥ 1,000 m²) is applied in change analysis to isolate genuine valley hazard footprints.
          </div>
        </details>

        <details class="scientific-accordion caveat">
          <summary>SNAP Calibration Warning Provenance</summary>
          <div class="accordion-content">
            CloudFerro COG wrappers added an outer XML element <code>&lt;safe:processing name="COG Conversion"&gt;</code>, which triggered SNAP's version parser warning. Bytecode inspection verified that genuine Sentinel-1 IPF 004.03 lookup tables were executed without radiometric corruption.
          </div>
        </details>
      `;
    } else if (ws === 'change') {
      const isFiltered = state.mmuFilter === 'mmu1000';
      panelTitle.textContent = 'Surface Change Detection';
      panelBadge.textContent = isFiltered ? 'Morphology Filter (≥ 1,000 m²)' : 'Raw 10m Decision Grid';
      panelBody.innerHTML = `
        <div class="analysis-section">
          <div class="section-label">${isFiltered ? 'Contiguous Hazard Morphology (MMU ≥ 1,000 m²)' : 'Raw Basin Baseline Statistics (1,526 km² Grid)'}</div>
          <div class="metric-grid-2x2">
            <div class="metric-card accent-water">
              <span class="metric-card-label">${isFiltered ? 'Contiguous Floodwater' : 'Candidate Floodwater'}</span>
              <span class="metric-card-value">${isFiltered ? '62.86 km²' : '126.60 km²'}</span>
              <span class="metric-card-sub">${isFiltered ? '714,994 px (49.7% of raw)' : '1,439,895 px (8.30%)'}</span>
            </div>
            <div class="metric-card accent-debris">
              <span class="metric-card-label">${isFiltered ? 'Contiguous Debris / Scour' : 'Candidate Debris / Scour'}</span>
              <span class="metric-card-value">${isFiltered ? '46.93 km²' : '108.21 km²'}</span>
              <span class="metric-card-sub">${isFiltered ? '533,819 px (43.4% of raw)' : '1,230,733 px (7.09%)'}</span>
            </div>
            <div class="metric-card">
              <span class="metric-card-label">Permanent Water Baseline</span>
              <span class="metric-card-value">66.43 km²</span>
              <span class="metric-card-sub">755,548 px (4.35%)</span>
            </div>
            <div class="metric-card">
              <span class="metric-card-label">${isFiltered ? 'Filtered Slope Speckle' : 'Unchanged Land Surface'}</span>
              <span class="metric-card-value">${isFiltered ? '125.02 km²' : '1,224.82 km²'}</span>
              <span class="metric-card-sub">${isFiltered ? '1,421,815 isolated px' : '13,931,062 px (80.26%)'}</span>
            </div>
          </div>
        </div>

        <div class="scientific-table-wrap">
          <table class="scientific-table">
            <thead><tr><th>Class</th><th>Decision Rule</th><th style="text-align:right;">${isFiltered ? 'Contiguous MMU' : 'Raw Baseline'}</th></tr></thead>
            <tbody>
              <tr><td class="bold" style="color:var(--hazard-flood);">Candidate Inundation</td><td>Δσ° ≤ -3.5 dB (specular drop)</td><td class="num bold">${isFiltered ? '62.86 km²' : '126.60 km²'}</td></tr>
              <tr><td class="bold" style="color:var(--hazard-debris);">Candidate Debris / Scour</td><td>Δσ° ≥ +3.5 dB (coarsening)</td><td class="num bold">${isFiltered ? '46.93 km²' : '108.21 km²'}</td></tr>
              <tr><td>Permanent Water</td><td>pre & post ≤ -16 dB</td><td class="num">66.43 km²</td></tr>
              <tr><td>Unchanged Surface</td><td>-3.5 &lt; Δσ° &lt; +3.5</td><td class="num">1,224.82 km²</td></tr>
            </tbody>
          </table>
        </div>

        <details class="scientific-accordion" open>
          <summary>Mountain Slope Speckle Investigation</summary>
          <div class="accordion-content">
            Connected component analysis on the 10m classification raster reveals that <strong>46.5% of raw flood detections (171,417 discrete features)</strong> and <strong>44.3% of raw debris detections (148,718 discrete features)</strong> are isolated single pixels (100 m²). Micro-clusters ≤ 5 pixels (≤ 500 m²) comprise 39.3% of flood and 43.9% of debris pixels.<br><br>
            <strong>Physical Origin:</strong> In steep Himalayan terrain (>25°), severe local incidence angle variations generate single-look radar speckle variance in the absence of an auxiliary DEM layover/shadow mask.<br><br>
            <strong>Standard MMU Filter:</strong> Applying Copernicus EMS Minimum Mapping Unit criteria (≥ 1,000 m² / 10 connected pixels) cleanly suppresses ridge speckle while preserving the true contiguous alluvial inundation and debris flows along the Trishuli River corridor.
          </div>
        </details>

        <details class="scientific-accordion">
          <summary>Geodesic Area Verification</summary>
          <div class="accordion-content">
            Raw flood extent (126.60 km²) was independently verified against exact row-by-row WGS84 geodesic ellipsoidal integration using <code>pyproj.Geod</code> (126.61 km², variance +0.015%) and equal-area UTM Zone 45N metric reprojection (126.58 km², variance -0.010%).
          </div>
        </details>

        <details class="scientific-accordion caveat" open>
          <summary>Disclosed Scientific Caveats</summary>
          <div class="accordion-content">
            1. <strong>Candidate Anomaly Designation:</strong> Radar backscatter changes indicate potential physical anomalies, not field-surveyed flood destruction.<br>
            2. <strong>Recession Lag:</strong> Post-event observation is 10 days post-peak. In steep gorges, water drains rapidly; Day 10 SAR maps lingering pooled water and saturated mud bars.<br>
            3. <strong>Terrain Shadow:</strong> Auxiliary shadow bands were omitted during single-band dB GeoTIFF export (0 px shadow suspect). Slopes &gt;25° require optical confirmation.
          </div>
        </details>
      `;
    } else if (ws === 'exposure') {
      panelTitle.textContent = 'Infrastructure Exposure';
      panelBadge.textContent = 'Scale-Dependent Risk';
      panelBody.innerHTML = `
        <div class="analysis-section">
          <div class="section-label">Unique Infrastructure Intersections</div>
          <div class="metric-grid-2x2">
            <div class="metric-card accent-primary">
              <span class="metric-card-label">Exposed Buildings</span>
              <span class="metric-card-value">1,062</span>
              <span class="metric-card-sub">27.83% of 3,816 surveyed</span>
            </div>
            <div class="metric-card accent-primary">
              <span class="metric-card-label">Exposed Roads</span>
              <span class="metric-card-value">35.12 km</span>
              <span class="metric-card-sub">13.47% of 260.7 km network</span>
            </div>
            <div class="metric-card">
              <span class="metric-card-label">Destroyed Overlap</span>
              <span class="metric-card-value">936 / 2,813</span>
              <span class="metric-card-sub">33.27% of Destroyed bldgs</span>
            </div>
            <div class="metric-card">
              <span class="metric-card-label">Pasang Lhamu Hwy</span>
              <span class="metric-card-value">9.62 km</span>
              <span class="metric-card-sub">16.59% of 57.95 km corridor</span>
            </div>
          </div>
        </div>

        <div class="section-label" style="margin-top:4px;">Building Damage Cross-Tabulation</div>
        <div class="scientific-table-wrap">
          <table class="scientific-table">
            <thead><tr><th>EMSR Grade</th><th class="num">Flood</th><th class="num">Debris</th><th class="num">Total Exposed</th></tr></thead>
            <tbody>
              <tr><td class="bold" style="color:var(--status-destroyed);">Destroyed</td><td class="num">812</td><td class="num">124</td><td class="num bold">936 (33.3%)</td></tr>
              <tr><td class="bold" style="color:var(--status-damaged);">Damaged</td><td class="num">48</td><td class="num">21</td><td class="num bold">69 (19.5%)</td></tr>
              <tr><td class="bold" style="color:var(--status-possible);">Possibly Damaged</td><td class="num">24</td><td class="num">33</td><td class="num bold">57 (8.8%)</td></tr>
              <tr><td class="bold">Total Unique</td><td class="num">884</td><td class="num">178</td><td class="num bold">1,062 (27.8%)</td></tr>
            </tbody>
          </table>
        </div>

        <details class="scientific-accordion" open>
          <summary>Highway Spatial Correspondence Audit</summary>
          <div class="accordion-content">
            The 9.62 km of national highway hazard intersection represents a spatial hazard crossing screening metric. A proximity audit proved that only 0.30 km directly coincides geometrically (within 50m) with the 60.97 km of destroyed local roads mapped in EMSR927, because EMSR927 evaluated local riverbed access tracks while Pasang Lhamu follows an upper engineered bench.
          </div>
        </details>

        <details class="scientific-accordion caveat" open>
          <summary>Potential Exposure vs Confirmed Damage</summary>
          <div class="accordion-content">
            All infrastructure figures denote <strong>POTENTIAL EXPOSURE</strong> derived from satellite hazard intersection. They do NOT confirm structural collapse or road closure without on-site civil engineering inspection.
          </div>
        </details>
      `;
    } else if (ws === 'validation') {
      const isBidur = state.currentSector === 'aoi03' || state.currentSector === 'corridor' || state.currentSector === 'all';
      panelTitle.textContent = 'Reference Validation';
      panelBadge.textContent = 'Copernicus EMSR927';
      panelBody.innerHTML = `
        <div class="analysis-section">
          <div class="section-label">Sector: ${isBidur ? 'Bidur Confluence (AOI03)' : 'Syapru Besi Gorge (AOI01)'}</div>
          <div class="metric-grid-2x2">
            <div class="metric-card accent-emsr">
              <span class="metric-card-label">Observed Event Coincidence</span>
              <span class="metric-card-value">${isBidur ? '37.16%' : '23.70%'}</span>
              <span class="metric-card-sub">${isBidur ? '24,885 of 66,959 px (5.89 km²)' : '3,000 of 12,660 px (1.11 km²)'}</span>
            </div>
            <div class="metric-card accent-water">
              <span class="metric-card-label">SAR Inundation Capture</span>
              <span class="metric-card-value">${isBidur ? '26.89%' : '9.82%'}</span>
              <span class="metric-card-sub">${isBidur ? '1.58 km² (18,002 px)' : '0.11 km² (1,243 px)'}</span>
            </div>
            <div class="metric-card accent-debris">
              <span class="metric-card-label">SAR Debris / Scour Capture</span>
              <span class="metric-card-value">${isBidur ? '10.28%' : '13.88%'}</span>
              <span class="metric-card-sub">${isBidur ? '0.61 km² (6,883 px)' : '0.15 km² (1,757 px)'}</span>
            </div>
            <div class="metric-card">
              <span class="metric-card-label">SAR Spatial Coverage</span>
              <span class="metric-card-value">100.0%</span>
              <span class="metric-card-sub">Complete Domain Overlap</span>
            </div>
          </div>
        </div>

        <div class="section-label" style="margin-top:4px;">Footprint Overlap Breakdown (AOI03 Bidur)</div>
        <div class="scientific-table-wrap">
          <table class="scientific-table">
            <thead><tr><th>Phenomenon</th><th class="num">Inside Footprint</th><th class="num">% of EMSR927</th></tr></thead>
            <tbody>
              <tr><td class="bold" style="color:var(--hazard-flood);">SAR Inundation</td><td class="num">18,002 px (1.58 km²)</td><td class="num bold">26.89%</td></tr>
              <tr><td class="bold" style="color:var(--hazard-debris);">SAR Debris / Scour</td><td class="num">6,883 px (0.61 km²)</td><td class="num bold">10.28%</td></tr>
              <tr><td class="bold" style="color:var(--reference-emsr);">Total SAR Capture</td><td class="num bold">24,885 px (2.19 km²)</td><td class="num bold">37.16%</td></tr>
              <tr><td>SAR No-Change (Dried)</td><td class="num">40,654 px (3.57 km²)</td><td class="num">60.71%</td></tr>
              <tr><td class="bold">EMSR927 Optical Footprint</td><td class="num bold">66,959 px (5.89 km²)</td><td class="num bold">100.00%</td></tr>
            </tbody>
          </table>
        </div>

        <details class="scientific-accordion" open>
          <summary>Hydrologic Recession Dynamics (10-Day Lag)</summary>
          <div class="accordion-content">
            Copernicus EMSR927 mapped maximum mud and debris scour lines from 0.3m optical imagery within 24–48 hours post-event. In steep Himalayan torrents, flood surges drain rapidly. The September 5 SAR pass (10 days later) observes persistent standing water, saturated mud bars, and altered riverbanks, capturing 37.16% of the high-water footprint.
          </div>
        </details>

        <details class="scientific-accordion caveat" open>
          <summary>Observed Event Overlap vs Classifier Accuracy</summary>
          <div class="accordion-content">
            This benchmark measures <em>observed-event spatial coincidence</em>, NOT algorithmic precision/recall or detection accuracy. Ground truth is non-contemporaneous, reflecting distinct physical phenomena (0.3m optical mud lines vs 10m C-band radar specular water).
          </div>
        </details>
      `;
    } else if (ws === 'copilot') {
      renderCopilotPanel();
    }

    if (state.inspectedFeature) {
      renderInspectorCard();
    }
  }

  // 10. Situation-Report Copilot Panel & Interactive Engine
  function renderCopilotPanel() {
    const isNe = state.copilotLang === 'ne';
    panelTitle.textContent = isNe ? 'वरुणा स्थिति-प्रतिवेदन कोपाइलट' : 'Situation-Report Copilot';
    panelBadge.textContent = isNe ? 'भू-स्थानिक एआई' : 'Evidence-Grounded AI';

    panelBody.innerHTML = `
      <div class="copilot-container">
        <div class="copilot-header-bar">
          <div class="section-label" style="margin:0;">${isNe ? 'सञ्चालन प्रश्न सोध्नुहोस्' : 'Operational AI Q&A'}</div>
          <div class="copilot-lang-toggle">
            <button class="copilot-lang-btn ${!isNe ? 'active' : ''}" id="btnLangEn">EN</button>
            <button class="copilot-lang-btn ${isNe ? 'active' : ''}" id="btnLangNe">नेपाली</button>
          </div>
        </div>

        <div class="copilot-chips-wrap">
          <button class="copilot-chip" data-q="${isNe ? 'कुन कुन बस्तीहरू सम्पर्कविहीन छन्?' : 'Which settlements are isolated?'}">${isNe ? '🚨 सम्पर्कविहीन बस्तीहरू' : '🚨 Isolated Settlements'}</button>
          <button class="copilot-chip" data-q="${isNe ? 'सडक पूर्वाधारमा कति क्षति पुगेको छ?' : 'What is the road exposure in the corridor?'}">${isNe ? '🛣️ सडक पूर्वाधार' : '🛣️ Road Exposure'}</button>
          <button class="copilot-chip" data-q="${isNe ? 'बाढी डुबान तथा गेग्रानको क्षेत्रफल कति छ?' : 'What are the flood and debris areas?'}">${isNe ? '🌊 डुबान तथा गेग्रान' : '🌊 Hazard Areas'}</button>
          <button class="copilot-chip" data-q="${isNe ? 'उपग्रह अर्बिट विश्लेषण' : 'Why Orbit 19 instead of Orbit 85?'}">${isNe ? '🛰️ अर्बिट विश्लेषण' : '🛰️ Orbit Telemetry'}</button>
          <button class="copilot-chip" data-q="${isNe ? 'बाढीमा कति जनाको मृत्यु भयो?' : 'How many casualties and deaths occurred?'}">${isNe ? '⚠️ मानवीय क्षति (अस्वीकरण परीक्षण)' : '⚠️ Casualty Query (Refusal Test)'}</button>
        </div>

        <div class="copilot-input-wrap">
          <input type="text" class="copilot-input" id="copilotQueryInput" placeholder="${isNe ? 'उद्धार सम्बन्धी प्रश्न सोध्नुहोस्...' : 'Ask an operational rescue question...'}" />
          <button class="copilot-submit-btn" id="btnCopilotSubmit">${isNe ? 'सोध्नुहोस्' : 'Ask'}</button>
        </div>

        <div id="copilotResponseWrap">
          <div class="copilot-response-card">
            <div class="copilot-response-header">
              <span class="copilot-badge-grounded">✓ ${isNe ? 'प्रमाणित भू-स्थानिक तथ्याङ्क' : 'Strictly Grounded Facts'}</span>
              <span style="font-size:10px; color:var(--text-tertiary); font-family:var(--font-mono);">Sentinel-1 C-SAR</span>
            </div>
            <div class="copilot-answer-text">
              ${isNe 
                ? 'वरुणा कोपाइलटमा स्वागत छ। यो सहायक केवल प्रमाणित उपग्रह राडार र सडक सञ्जाल विश्लेषणबाट प्राप्त आधिकारिक तथ्याङ्कमा आधारित छ। माथिका बटनहरू थिच्नुहोस् वा आफ्ना प्रश्न टाइप गर्नुहोस्।'
                : 'Welcome to the VARUNA Situation-Report Copilot. Every quantitative claim is strictly grounded in computed radar and road-network outputs, with zero hallucination. Select a preset query above or enter a question.'}
            </div>
            <div class="copilot-facts-footer">
              <span class="copilot-fact-tag">CAG: 1,526.05 km²</span>
              <span class="copilot-fact-tag">Water: 126.60 km²</span>
              <span class="copilot-fact-tag">Debris: 108.21 km²</span>
              <span class="copilot-fact-tag">Roads: 35.12 km</span>
              <span class="copilot-fact-tag">Hwy: 9.62 km</span>
              <span class="copilot-fact-tag">Isolated: 6 Villages</span>
            </div>
          </div>
        </div>

        <div style="margin-top:4px;">
          <button class="btn-header" style="width:100%; justify-content:center; padding:7px 0; background:var(--surface-primary); border:1px solid var(--border-light);" id="btnPanelOpenBriefing">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            <span style="font-size:11px; font-weight:600;">${isNe ? 'पूर्ण आपतकालीन स्थिति प्रतिवेदन हेर्नुहोस् (SITREP)' : 'Open Full Situation Briefing (SITREP)'}</span>
          </button>
        </div>
      </div>
    `;

    // Bind Copilot Event Listeners
    document.getElementById('btnLangEn').addEventListener('click', () => {
      state.copilotLang = 'en';
      renderWorkspaceToolbar();
      renderCopilotPanel();
    });
    document.getElementById('btnLangNe').addEventListener('click', () => {
      state.copilotLang = 'ne';
      renderWorkspaceToolbar();
      renderCopilotPanel();
    });

    const inputEl = document.getElementById('copilotQueryInput');
    const submitBtn = document.getElementById('btnCopilotSubmit');

    function executeCopilotQuery(q) {
      if (!q || !q.trim()) return;
      handleCopilotQuery(q.trim());
    }

    submitBtn.addEventListener('click', () => executeCopilotQuery(inputEl.value));
    inputEl.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') executeCopilotQuery(inputEl.value);
    });

    panelBody.querySelectorAll('.copilot-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        const q = chip.dataset.q;
        inputEl.value = q;
        executeCopilotQuery(q);
      });
    });

    const btnBriefing = document.getElementById('btnPanelOpenBriefing');
    if (btnBriefing) {
      btnBriefing.addEventListener('click', () => triggerCopilotBriefingModal());
    }
  }

  function handleCopilotQuery(query) {
    const wrap = document.getElementById('copilotResponseWrap');
    if (!wrap) return;

    const isNe = state.copilotLang === 'ne' || /[\u0900-\u097F]/.test(query);
    const qLower = query.toLowerCase();

    wrap.innerHTML = `
      <div class="copilot-response-card" style="opacity:0.7;">
        <div style="font-size:11px; color:var(--text-secondary);">${isNe ? 'प्रमाणीकरण गरिँदैछ...' : 'Validating grounded geospatial metrics...'}</div>
      </div>
    `;

    // Attempt backend query if API server is reachable, with immediate reliable offline fallback
    fetch('http://localhost:8000/api/v1/copilot/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: query, language: isNe ? 'ne' : 'en' })
    })
    .then(res => res.json())
    .then(data => {
      renderCopilotResponse(data.answer, data.unsupported_topic_flag, data.grounding_facts_used, data.sources, isNe);
    })
    .catch(() => {
      // Offline reliable fallback using exact same grounded facts
      const offlineResp = generateOfflineCopilotAnswer(query, isNe);
      renderCopilotResponse(offlineResp.answer, offlineResp.unsupported, offlineResp.facts, offlineResp.sources, isNe);
    });
  }

  function generateOfflineCopilotAnswer(query, isNe) {
    const qLower = query.toLowerCase();

    // 1. Anti-hallucination check
    if (/death|casualty|fatalities|died|killed|injured|missing|cost|dollar|rupee|monetary|forecast|मृत्यु|घाइते|बेपत्ता|हताहत|आर्थिक/i.test(query)) {
      return {
        unsupported: true,
        answer: isNe
          ? 'वरुणा वैज्ञानिक अस्वीकरण: उपग्रह भू-अवलोकन (SAR Radar) प्रणालीबाट मानवीय क्षति, मृतक, घाइते वा बेपत्ता व्यक्तिहरूको संख्या वा आर्थिक लागत प्रत्यक्ष अवलोकन गर्न सकिँदैन। यो प्रणालीले केवल भू-सतहको जलमग्नता, गेग्रान बहाव, र सडक/भवन पूर्वाधारको भौगोलिक जोखिम मात्र मापन गर्दछ। कृपया आधिकारिक मानवीय तथ्याङ्कका लागि नेपाल सरकार NDRRMA को स्थिति प्रतिवेदन हेर्नुहोस्।'
          : 'VARUNA SCIENTIFIC DISCLOSURE: Ground casualties, fatalities, injuries, missing persons, and economic valuation cannot be directly observed from Synthetic Aperture Radar (SAR) Earth observation satellites. VARUNA exclusively measures surface physical phenomena: floodwater inundation extents, debris scour, and infrastructure intersections. For official casualty numbers, consult the National Disaster Risk Reduction and Management Authority (NDRRMA).',
        facts: [],
        sources: ['NDRRMA Official Situation Reports']
      };
    }

    // 2. Multi-topic detection for compound queries
    const hasRoads = /road|roads|highway|highways|bridge|bridges|pasang lhamu|transport|सडक|राजमार्ग|पुल|पासाङ ल्हामु/i.test(query) ||
      ((/kilometer|km|किमी/i.test(query)) && /road|highway|सडक|राजमार्ग|exposed|cutoff|cut off/i.test(query));
    const hasFlood = /water|flood|floodwater|inundation|flooded|inundated|बाढी|डुबान|पानी|जलमग्न/i.test(query);
    const hasDebris = /debris|scour|roughening|sediment|deposits|108\.21|17\.51|गेग्रान|पहिरो|खस्रोपन/i.test(query);
    const hasArea = /area|extent|size|cag|grid|km2|क्षेत्रफल|आयतन|फैलावट/i.test(query);
    const hasSettlements = /isolated|cut off|cutoff|settlement|settlements|village|villages|hospital|सम्पर्कविहीन|बस्ती|गाउँ|अस्पताल/i.test(query);
    const hasBuildings = /building|buildings|house|houses|structure|structures|भवन|घर|संरचना/i.test(query);
    const hasOrbit = /orbit|satellite|sensor|19|85|अर्बिट|उपग्रह/i.test(query);

    const sections = [];
    const facts = [];
    const sources = ['Sentinel-1 C-SAR (Orbit 19, VV)', 'OpenStreetMap Pre-Event Network'];

    // Topic A: Flood & Debris Extents
    if (hasFlood || hasDebris || (hasArea && !hasRoads && !hasBuildings && !hasSettlements)) {
      facts.push('flood_inundation_km2 (126.60)', 'surface_debris_km2 (108.21)', 'filtered_debris_clusters_km2 (17.51)');
      sections.push(isNe
        ? '• सम्भावित बाढी डुबान क्षेत्र: १२६.६० वर्ग किमी (१४,३९,८९५ पिक्सेल, कुल १,५२६.०५ वर्ग किमी विश्लेषण ग्रिडमा Δσ° ≤ -३.५ dB)\n• सम्भावित गेग्रान तथा खस्रोपन: १०८.२१ वर्ग किमी (१२,३०,७३३ पिक्सेल, कच्चा); प्रमुख निरन्तर क्लस्टरहरू १७.५१ वर्ग किमी (२,००० वर्ग मि. भन्दा ठूला); १० पिक्सेल MMU मा ४६.९३ वर्ग किमी\n• अवलोकन समय: घटनाको १० दिनपछि (सेप्टेम्बर ५) खिचिएको, जसले बाँकी रहेको पानी र भिजेको बगर देखाउँछ।'
        : '• Candidate Flood Inundation: 126.60 km² (1,439,895 pixels, Δσ° <= -3.5 dB across 1,526.05 km² Common Analysis Grid)\n• Candidate Surface Debris / Roughening: 108.21 km² raw unconstrained radar coarsening (Δσ° >= +3.5 dB across full CAG); filtered contiguous major debris clusters total 17.51 km² (MMU >= 2,000 m²); contiguous morphology (MMU >= 1,000 m²) totals 46.93 km²\n• Temporal Observation: Captured on Sept 5, 2026 (10 days post-peak), observing persistent valley floor water, saturated deposits, and scouring.'
      );
    }

    // Topic B: Road Infrastructure Exposure
    if (hasRoads) {
      facts.push('exposed_roads_km (35.12)', 'highway_exposed_km (9.62)', 'double_counting_km (0.00)');
      if (!hasSettlements) facts.push('isolated_settlements (6)');
      const settlementNote = !hasSettlements ? (isNe ? '\n• सम्भावित सम्पर्कविहीन बस्तीहरू (६): स्याफ्रुबेसी, मैलुङ, बेत्रावती, राम्चे, टिमुरे, थाम्बुचेत' : '\n• Resulting Candidate Isolated Settlements (6): Syaphrubesi, Mailung, Betrawati, Ramche, Timure, Thambuchet') : '';
      sections.push(isNe
        ? `• प्रभावित सडक सञ्जाल: कुल २६०.७१ किमीमध्ये ३५.१२ किमी सडक जोखिममा (१३.४७%, ६०५ खण्डहरू)\n• पासाङ ल्हामु राजमार्ग (H04): ५७.९५ किमी करिडोरमध्ये ९.६२ किमी प्रभावित (१६.५९%)\n• शून्य दोहोरो गणना: ०.०० किमी (पानी र गेग्रानको संयुक्त बहुभुज बनाइ शून्य दोहोरो गणना सुनिश्चित गरिएको)${settlementNote}\n• प्राविधिक नोट: उपग्रह जोखिमले सम्भावित अवरोध जनाउँछ; सडक बन्द हुनु पहुँच विश्लेषणका लागि गरिएको परिदृश्य हो, पूर्ण भौतिक विनाश होइन।`
        : `• Exposed Road Network: 35.12 km of 260.71 km total surveyed network (13.47%, 605 segments)\n• Pasang Lhamu Highway (H04): 9.62 km exposed along the 57.95 km gorge corridor (16.59%)\n• Double-Counting: Exactly 0.00 km (hazard polygons dissolved via unary_union before line intersection)${settlementNote}\n• Scientific Exposure Caveat: Satellite hazard intersection denotes POTENTIAL EXPOSURE; road closure is an assumed scenario for reachability testing, not independently confirmed physical collapse.`
      );
    }

    // Topic C: Settlement Reachability & Hospital Connectivity
    if (hasSettlements) {
      facts.push('isolated_settlements (6)', 'critical_hubs (Nuwakot Hospital)');
      sections.push(isNe
        ? '• सम्पर्कविहीन बस्तीहरू (६ वटा): स्याफ्रुबेसी, मैलुङ, बेत्रावती, राम्चे, टिमुरे, थाम्बुचेत\n• विच्छेद भएका अस्पताल तथा केन्द्र: नुवाकोट जिल्ला अस्पताल (विदुर / त्रिशुली) उत्तरतर्फको करिडोरबाट सम्पर्कविच्छेद भएको मोडेल परिदृश्य।\n• मुख्य अवरोध: पासाङ ल्हामु राजमार्गको ९.६२ किमी (१६.५९%) खण्ड प्रभावित भई कुल ३५.१२ किमी सडक सञ्जाल अवरुद्ध भएको काल्पनिक परिदृश्य।'
        : '• Candidate Isolated Settlements (6): Syaphrubesi, Mailung, Betrawati, Ramche, Timure, Thambuchet\n• Cut-Off Critical Hubs: Nuwakot District Hospital (Bidur / Trishuli) is cut off from vehicular access to the northern gorge.\n• Disruption Corridor: 9.62 km (16.59%) of the Pasang Lhamu National Highway (H04) corridor intersects floodwater or debris. Across the full study corridor, 35.12 km of road network is exposed.\n• Methodology Note: Road closure is a simulation assumption for accessibility modeling. Model-derived candidate isolation does NOT constitute confirmed physical destruction.'
      );
    }

    // Topic D: Buildings & Structures
    if (hasBuildings) {
      facts.push('exposed_buildings (1062)', 'destroyed_buildings_coincidence (936)');
      sections.push(isNe
        ? '• जोखिममा परेका भवनहरू: सर्वेक्षण गरिएका ३,८१६ संरचनाहरूमध्ये १,०६२ वटा (२७.८३%)\n• EMSR927 नष्ट संरचनाहरूसँग मेल: आधिकारिक २,८१३ नष्ट संरचनाहरूमध्ये ९३६ वटा (३३.२७% राडार खतरा क्षेत्रभित्र परेका)\n• विधिगत नोट: उपग्रह जोखिमले पानी वा गेग्रानको उपस्थिति जनाउँछ, भवन भत्किएको आधिकारिक पुष्टि स्थलगत सर्वेक्षणबाट मात्र हुन्छ।'
        : '• Potentially Exposed Buildings: 1,062 of 3,816 surveyed structures (27.83%)\n• Coincidence with EMSR927 Destroyed Buildings: 936 of 2,813 confirmed destroyed structures (33.27%)\n• Methodological note: Spatial intersection denotes exposure to floodwater or debris flow, not structural certification.'
      );
    }

    // Topic E: Orbit & Telemetry
    if (hasOrbit) {
      facts.push('post_event_lag_days (10)', 'bidur_emsr_overlap_pct (37.16)');
      sections.push(isNe
        ? '• प्रयोग गरिएको मुख्य अर्बिट: अर्बिट १९ (डिसेन्डिङ), सेप्टेम्बर ५, २०२६ (+१० दिनको विलम्ब)\n• तुलनात्मक जोडी: अर्बिट ८५ (एसेन्डिङ), अगस्ट २८, २०२६ (+२.५ दिन / ४८-६० घण्टाको अन्तराल)\n• EMSR927 प्रमाणीकरण: विदुर (AOI03) मा ३७.१६% र स्याफ्रुबेसी (AOI01) मा २३.७०% भौगोलिक मेल।'
        : '• Executed Primary Dataset: Relative Orbit 19 (Descending), Pre: Aug 24, Post: Sept 5, 2026 (+10 days post-peak lag)\n• Alternate Evaluated Pair: Relative Orbit 85 (Ascending), Pre: Aug 16, Post: Aug 28, 2026 (+2.5 days / 48-60 hrs lag). Orbit 85 provides closer temporal proximity to the flood wave, while Orbit 19 documents 10-day residual inundation.\n• Copernicus EMSR927 Held-Out Validation: 37.16% total anomaly coincidence at Bidur (AOI03) and 23.70% at Syapru Besi (AOI01).'
      );
    }

    if (sections.length > 0) {
      const header = sections.length > 1
        ? (isNe ? 'उपग्रह राडार तथा पूर्वाधार विश्लेषणका प्रमाणित तथ्याङ्कहरू:\n' : 'Grounded multi-hazard and infrastructure analysis:\n')
        : '';
      return {
        unsupported: false,
        answer: header + sections.join('\n\n'),
        facts: Array.from(new Set(facts)),
        sources: sources
      };
    }

    // Default Operational Briefing fallback
    return {
      unsupported: false,
      answer: isNe
        ? 'वरुणा उद्धार स्थिति सारांश (त्रिशुली नदी करिडोर, अगस्ट २०२६):\n• कुल बाढी डुबान: १२६.६० वर्ग किमी | गेग्रान थुप्रिएको क्षेत्र: १०८.२१ वर्ग किमी (कच्चा) / १७.५१ वर्ग किमी (प्रमुख क्लस्टर)\n• प्रभावित सडक सञ्जाल: ३५.१२ किमी (पासाङ ल्हामु राजमार्ग: ९.६२ किमी प्रभावित)\n• सम्भावित सम्पर्कविहीन बस्तीहरू (६): स्याफ्रुबेसी, मैलुङ, बेत्रावती, राम्चे, टिमुरे, थाम्बुचेत\n• प्रमुख अस्पताल सम्पर्क: नुवाकोट जिल्ला अस्पताल (विदुर) उत्तरतर्फको करिडोरबाट सम्पर्कविच्छेद भएको मोडेल परिदृश्य।'
        : 'VARUNA Operational Rescue Briefing (Trishuli Corridor, August 2026 Disaster):\n• Hazard Extents: 126.60 km² flood inundation | 108.21 km² raw debris scour (17.51 km² major contiguous clusters)\n• Road Impact: 35.12 km exposed (Pasang Lhamu Highway: 9.62 km cut off)\n• Candidate Isolated Settlements (6): Syaphrubesi, Mailung, Betrawati, Ramche, Timure, Thambuchet\n• Medical Center Reachability: Nuwakot District Hospital at Bidur is severed from the upper valley under hypothetical closure.',
      facts: ['flood_inundation_km2 (126.60)', 'surface_debris_km2 (108.21)', 'exposed_roads_km (35.12)', 'highway_exposed_km (9.62)'],
      sources: ['Sentinel-1 C-SAR Orbit 19', 'OpenStreetMap', 'NDRRMA Situation Report']
    };
  }

  function renderCopilotResponse(answer, unsupported, facts, sources, isNe) {
    const wrap = document.getElementById('copilotResponseWrap');
    if (!wrap) return;

    wrap.innerHTML = `
      <div class="copilot-response-card">
        <div class="copilot-response-header">
          ${unsupported 
            ? `<span class="copilot-badge-refusal">⚠️ ${isNe ? 'वैज्ञानिक अस्वीकरण' : 'Anti-Hallucination Refusal'}</span>`
            : `<span class="copilot-badge-grounded">✓ ${isNe ? 'प्रमाणित तथ्याङ्क' : 'Strictly Grounded Facts'}</span>`
          }
          <span style="font-size:10px; color:var(--text-tertiary); font-family:var(--font-mono);">${sources && sources[0] ? sources[0] : 'Sentinel-1 C-SAR'}</span>
        </div>
        <div class="copilot-answer-text">${answer}</div>
        ${facts && facts.length > 0 ? `
          <div class="copilot-facts-footer">
            ${facts.map(f => `<span class="copilot-fact-tag">${f}</span>`).join('')}
          </div>
        ` : ''}
      </div>
    `;
  }

  function triggerCopilotBriefingModal() {
    const isNe = state.copilotLang === 'ne';
    const briefingText = isNe ? `
# वरुणा आपतकालीन स्थिति प्रतिवेदन (SITREP) — त्रिशुली बाढी तथा गेग्रान बहाव
मिति: २०२६ अक्टोबर १४ | घटना मिति: २०२६ अगस्ट २६ | सेन्सर: Sentinel-1 C-SAR (अर्बिट १९)

१. भू-सतह जोखिम विश्लेषण (Hazard Extents)
• कुल साझा विश्लेषण ग्रिड (CAG): १,५२६.०५ वर्ग किमी (शून्य NoData)
• सम्भावित बाढी डुबान क्षेत्र: १२६.६० वर्ग किमी (१४,३९,८९५ पिक्सेल, Δσ° ≤ -३.५ dB)
• सम्भावित गेग्रान तथा सतह खस्रोपन: १०८.२१ वर्ग किमी (१२,३०,७३३ पिक्सेल, Δσ° ≥ +३.५ dB)
• अवलोकन विलम्ब: घटनाको १० दिनपछि (सेप्टेम्बर ५) खिचिएकाले यसले बाढीको उच्चतम बहाव नभई बाँकी रहेको पानी र गेग्रान देखाउँछ।

२. सडक सञ्जाल तथा पूर्वाधार जोखिम (Infrastructure Exposure)
• प्रभावित सडक सञ्जाल: ३५.१२ किमी (कुल २६०.७१ किमीको १३.४७%, ६०५ सडक खण्डहरू)
• पासाङ ल्हामु राजमार्ग (H04): ९.६२ किमी खण्ड बाढी/गेग्रानले प्रत्यक्ष प्रभावित (५७.९५ किमीको १६.५९%)
• दोहोरो गणना: ०.०० किमी (शून्य दोहोरो गणना, पूर्ण रूपमा एकाकार गरिएको बहुभुज)
• जोखिममा परेका भवनहरू: १,०६२ वटा (सर्वेक्षण गरिएका ३,८१६ संरचनाहरूको २७.८३%)

३. विच्छेदित बस्तीहरू तथा अस्पताल पहुँच
• सम्पर्कविहीन बस्तीहरू (६ वटा): स्याफ्रुबेसी, मैलुङ, बेत्रावती, राम्चे, टिमुरे, थाम्बुचेत
• प्रमुख अस्पताल केन्द्र: नुवाकोट जिल्ला अस्पताल (विदुर) सँग माथिल्लो करिडोरको सडक सम्पर्क टुटेको छ।

४. वैज्ञानिक सीमाहरू तथा स्रोत आभार
• उपग्रह जोखिमले 'सम्भावित भौगोलिक अवरोध' जनाउँछ, पूर्ण भौतिक विनाश होइन।
• "Contains modified Copernicus Sentinel data 2026."
• "Produced using Copernicus WorldDEM-30 © DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018."
• "© OpenStreetMap contributors."
` : `
# VARUNA OPERATIONAL SITUATION REPORT (SITREP) — TRISHULI RIVER FLOOD
Generated: 2026-10-14 UTC | Disaster Date: August 26, 2026 | Sensor: Sentinel-1 C-SAR (Orbit 19 Descending)

1. SAR Hazard Mapping Extents
• Common Analysis Grid (CAG): 1,526.05 km² (100% valid overlap, zero NoData)
• Candidate Flood Inundation: 126.60 km² (1,439,895 pixels, Δσ° <= -3.5 dB)
• Candidate Surface Debris / Roughening: 108.21 km² (1,230,733 pixels, Δσ° >= +3.5 dB)
• Observation Lag: 10 days post-peak (Sept 5 acquisition); documents persistent valley ponding and gravel bed scour.

2. Infrastructure Exposure
• Road Network Intersected: 35.12 km of 260.71 km surveyed network (13.47%, 605 segments)
• Pasang Lhamu Highway (H04): 9.62 km hazard intersection along 57.95 km corridor (16.59%)
• Hazard Double-Counting: Exactly 0.00 km (water and debris dissolved via unary_union before line intersection)
• Building Structures Intersected: 1,062 of 3,816 surveyed structures (27.83%)

3. Isolated Settlements & Critical Medical Hub Connectivity
• Candidate Isolated Settlements (6): Syaphrubesi, Mailung, Betrawati, Ramche, Timure, Thambuchet
• Critical Medical Hub: Nuwakot District Hospital at Bidur is severed from vehicular access for northern settlements.

4. Scientific Disclosures & Required Attributions
• Satellite hazard intersection denotes POTENTIAL EXPOSURE; ground civil engineering verification is required.
• "Contains modified Copernicus Sentinel data 2026."
• "Produced using Copernicus WorldDEM-30 © DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018 provided under COPERNICUS by the European Union and ESA; all rights reserved."
• "© OpenStreetMap contributors."
`;

    const wrap = document.getElementById('copilotResponseWrap');
    if (wrap) {
      wrap.innerHTML = `
        <div class="copilot-response-card">
          <div class="copilot-response-header">
            <span class="copilot-badge-grounded">✓ ${isNe ? 'आधिकारिक स्थिति प्रतिवेदन' : 'Official Situation Briefing'}</span>
            <a href="docs/SITUATION_REPORT_NEPAL_2026.pdf" target="_blank" style="font-size:10px; color:var(--accent-primary); font-weight:700;">Open PDF ↗</a>
          </div>
          <div class="copilot-report-preview">${briefingText}</div>
        </div>
      `;
    }
  }


  function renderInspectorCard() {
    const feat = state.inspectedFeature;
    if (!feat) return;
    const p = feat.properties;

    let existingCard = document.getElementById('inspectorCard');
    if (!existingCard) {
      existingCard = document.createElement('div');
      existingCard.id = 'inspectorCard';
      existingCard.className = 'inspector-card';
      panelBody.prepend(existingCard);
    }

    const title = p.damage_gra ? `Surveyed Structure (${p.damage_gra})` : (p.name || p.highway || 'Inspected GeoJSON Feature');
    existingCard.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <div class="inspector-card-title">${title}</div>
        <button id="btnCloseInspector" style="border:none; background:transparent; cursor:pointer; color:var(--text-tertiary); font-size:12px;">✕</button>
      </div>
      <div class="inspector-grid">
        <span class="label">Coordinates:</span>
        <span class="val">${feat.latlng.lat.toFixed(4)}°N, ${feat.latlng.lng.toFixed(4)}°E</span>
        ${p.damage_gra ? `<span class="label">Damage Grade:</span><span class="val" style="color:${p.damage_gra === 'Destroyed' ? 'var(--status-destroyed)' : 'var(--text-primary)'}">${p.damage_gra}</span>` : ''}
        ${p.potential_exposure ? `<span class="label">Potential Exposure:</span><span class="val">${p.potential_exposure}</span>` : ''}
        ${p.event_type ? `<span class="label">Event Type:</span><span class="val">${p.event_type} (${p.obj_desc || 'Scour'})</span>` : ''}
        ${p.aoi_source ? `<span class="label">Copernicus AOI:</span><span class="val">${p.aoi_source}</span>` : ''}
        ${p.length_m ? `<span class="label">Segment Length:</span><span class="val">${Math.round(p.length_m)} m</span>` : ''}
      </div>
    `;

    document.getElementById('btnCloseInspector').addEventListener('click', () => {
      state.inspectedFeature = null;
      existingCard.remove();
    });
  }

  // 10. Floating Legend Rendering
  const legendItems = document.getElementById('legendItems');
  const legendTitle = document.getElementById('legendTitle');

  function renderLegend() {
    const ws = state.activeWorkspace;
    let html = '';

    if (ws === 'comparison') {
      if (state.highlightChanges) {
        legendTitle.textContent = 'SAR Comparison & Anomaly Key';
        html = `
          <div class="legend-row">
            <div class="legend-swatch highlight-flood" style="width:12px; height:8px; border-radius:2px;"></div>
            <span>Candidate Floodwater (Δσ° ≤ -3.5 dB)</span>
          </div>
          <div class="legend-row">
            <div class="legend-swatch highlight-debris" style="width:12px; height:8px; border-radius:2px;"></div>
            <span>Possible Debris / Surface Change (Δσ° ≥ +3.5 dB)</span>
          </div>
          <div class="legend-row" style="margin-top:4px; padding-top:4px; border-top:1px solid var(--border-subtle); display:flex; align-items:center;">
            <div style="width:26px; height:6px; border-radius:1px; background:linear-gradient(to right, #000, #888, #fff); margin-right:6px; flex-shrink:0;"></div>
            <span style="font-size:9.5px; color:var(--text-tertiary);">SAR Backscatter Intensity (-22 to +2 dB)</span>
          </div>
        `;
      } else {
        legendTitle.textContent = 'SAR Intensity Scale';
        html = `
          <div class="legend-row">
            <div style="width:100%; height:8px; border-radius:2px; background:linear-gradient(to right, #000 0%, #777 50%, #fff 100%);"></div>
          </div>
          <div style="display:flex; justify-content:space-between; font-size:9.5px; color:var(--text-tertiary); font-family:var(--font-mono); margin-top:2px;">
            <span>-22.0 dB (Water/Specular)</span>
            <span>+2.0 dB (Rough Terrain)</span>
          </div>
        `;
      }
    } else if (ws === 'change') {
      legendTitle.textContent = 'SAR Change Classification';
      html = `
        <div class="legend-row">
          <div class="legend-swatch flood"></div>
          <span>Candidate Flood Inundation (Δσ° ≤ -3.5 dB)</span>
        </div>
        <div class="legend-row">
          <div class="legend-swatch debris"></div>
          <span>Candidate Surface Debris (Δσ° ≥ +3.5 dB)</span>
        </div>
        <div class="legend-row">
          <div class="legend-swatch perm-water"></div>
          <span>Permanent Water Baseline (σ° ≤ -16 dB)</span>
        </div>
        <div class="legend-row" style="color:var(--text-tertiary); font-size:10px;">
          <div style="width:14px; height:6px; border:1px solid #CCC; background:#FFF;"></div>
          <span>Unchanged Land (100% Transparent)</span>
        </div>
      `;
    } else if (ws === 'exposure') {
      legendTitle.textContent = 'Infrastructure Exposure';
      html = `
        <div class="legend-row"><div class="legend-swatch highway"></div><span>Pasang Lhamu National Highway</span></div>
        <div class="legend-row"><div class="legend-swatch destroyed"></div><span>Surveyed Structure — Destroyed</span></div>
        <div class="legend-row"><div class="legend-swatch damaged"></div><span>Surveyed Structure — Damaged</span></div>
        <div class="legend-row"><div class="legend-swatch flood"></div><span>Road Exposed to Inundation</span></div>
        <div class="legend-row"><div class="legend-swatch debris"></div><span>Road Exposed to Debris</span></div>
      `;
    } else if (ws === 'validation') {
      legendTitle.textContent = 'Validation Benchmark';
      html = `
        <div class="legend-row"><div class="legend-swatch emsr"></div><span>Copernicus EMSR927 Event Footprint</span></div>
        <div class="legend-row"><div class="legend-swatch flood"></div><span>SAR Floodwater Capture (26.89%)</span></div>
        <div class="legend-row"><div class="legend-swatch debris"></div><span>SAR Debris / Scour Capture (10.28%)</span></div>
      `;
    } else if (ws === 'copilot') {
      legendTitle.textContent = 'Grounded Intelligence Cartography';
      html = `
        <div class="legend-row"><div class="legend-swatch flood"></div><span>SAR Candidate Inundation (126.6 km²)</span></div>
        <div class="legend-row"><div class="legend-swatch debris"></div><span>SAR Candidate Debris (108.2 km²)</span></div>
        <div class="legend-row"><div class="legend-swatch highway"></div><span>Pasang Lhamu Highway (9.62 km Exposed)</span></div>
        <div class="legend-row"><div class="legend-swatch road"></div><span>Local Road Network (35.12 km Exposed)</span></div>
        <div class="legend-row"><div class="legend-swatch emsr"></div><span>EMSR927 Delineation (Held-Out Truth)</span></div>
      `;
    }

    legendItems.innerHTML = html;
  }

  // 11. Coordinate Readout on Mouse Move
  const txtCoords = document.getElementById('txtCoords');
  map.on('mousemove', (e) => {
    txtCoords.textContent = `${e.latlng.lat.toFixed(4)}° N, ${e.latlng.lng.toFixed(4)}° E`;
  });

  // 12. Floating Controls & Popover Handlers
  document.getElementById('btnZoomIn').addEventListener('click', () => map.zoomIn());
  document.getElementById('btnZoomOut').addEventListener('click', () => map.zoomOut());
  document.getElementById('btnResetMap').addEventListener('click', () => {
    if (state.activeWorkspace === 'comparison') {
      state.comparisonSector = 'full';
      map.fitBounds(RASTER_BOUNDS, { padding: [10, 10] });
      const selComp = document.getElementById('selCompPreset');
      if (selComp) selComp.value = 'full';
      setTimeout(() => updateSwipeDivider(), 50);
    } else {
      map.fitBounds(EXTENTS.corridor.bounds, { padding: [15, 15] });
    }
  });

  const popover = document.getElementById('layerMenuPopover');
  const btnToggleLayers = document.getElementById('btnToggleLayersMenu');
  btnToggleLayers.addEventListener('click', (e) => {
    e.stopPropagation();
    popover.classList.toggle('open');
  });

  document.addEventListener('click', (e) => {
    if (!popover.contains(e.target) && e.target !== btnToggleLayers) {
      popover.classList.remove('open');
    }
  });

  // Layer Popover Toggles
  document.getElementById('chkWater').addEventListener('change', (e) => {
    if (e.target.checked) rasters.water.addTo(map);
    else map.removeLayer(rasters.water);
  });
  document.getElementById('chkDebris').addEventListener('change', (e) => {
    if (e.target.checked) rasters.debris.addTo(map);
    else map.removeLayer(rasters.debris);
  });
  document.getElementById('chkEmsr').addEventListener('change', (e) => {
    if (e.target.checked) vectorLayers.emsr.addTo(map);
    else map.removeLayer(vectorLayers.emsr);
  });
  document.getElementById('chkBldgs').addEventListener('change', (e) => {
    if (e.target.checked) {
      updateInfrastructureScale();
    } else {
      if (map.hasLayer(clusterMarkersLayer)) map.removeLayer(clusterMarkersLayer);
      if (map.hasLayer(individualBldgsLayer)) map.removeLayer(individualBldgsLayer);
    }
  });
  document.getElementById('chkRoads').addEventListener('change', (e) => {
    if (e.target.checked) vectorLayers.roads.addTo(map);
    else map.removeLayer(vectorLayers.roads);
  });
  document.getElementById('chkHighway').addEventListener('change', (e) => {
    if (e.target.checked) vectorLayers.highway.addTo(map);
    else map.removeLayer(vectorLayers.highway);
  });

  // Basemap Switcher Handlers
  const selBasemap = document.getElementById('selBasemap');
  if (selBasemap) {
    selBasemap.addEventListener('change', (e) => setBasemap(e.target.value));
  }
  const btnToggleBasemapStatus = document.getElementById('btnToggleBasemapStatus');
  if (btnToggleBasemapStatus) {
    btnToggleBasemapStatus.addEventListener('click', () => {
      setBasemap(state.activeBasemap === 'topo' ? 'satellite' : 'topo');
    });
  }

  // Collapsible Analysis Panel
  const panel = document.getElementById('analysisPanel');
  document.getElementById('btnTogglePanel').addEventListener('click', () => {
    state.panelOpen = !state.panelOpen;
    panel.classList.toggle('collapsed', !state.panelOpen);
    setTimeout(() => map.invalidateSize(), 300);
  });

  // Responsive Layout & Map Resizing Listeners
  window.addEventListener('resize', () => {
    map.invalidateSize();
  });

  const mapViewportEl = document.querySelector('.map-viewport');
  if (mapViewportEl && window.ResizeObserver) {
    const ro = new ResizeObserver(() => {
      map.invalidateSize();
    });
    ro.observe(mapViewportEl);
  }

  // 13. App Bootstrap
  async function init() {
    await loadVectorData();

    // Check URL hash or search params
    const hash = window.location.hash;
    const matchWs = hash.match(/workspace=([a-z]+)/);
    const matchSector = hash.match(/sector=([a-z0-9]+)/);
    const matchMmu = hash.match(/mmu=([a-z0-9]+)/);

    if (matchMmu && ['all', 'mmu1000'].includes(matchMmu[1])) {
      state.mmuFilter = matchMmu[1];
    }

    const matchMode = hash.match(/mode=([a-z]+)/);
    if (matchMode && ['swipe', 'pre', 'post'].includes(matchMode[1])) {
      state.comparisonMode = matchMode[1];
    }

    const matchSwipe = hash.match(/swipe=([0-9.]+)/);
    if (matchSwipe) {
      state.swipePosition = parseFloat(matchSwipe[1]);
    }

    const initialWs = (matchWs && ['comparison', 'change', 'exposure', 'validation'].includes(matchWs[1]))
      ? matchWs[1]
      : 'comparison';

    const initialSector = (matchSector && ['all', 'corridor', 'aoi03', 'aoi01', 'aoi02'].includes(matchSector[1]))
      ? matchSector[1]
      : 'corridor';

    switchWorkspace(initialWs, true);

    if (initialWs === 'comparison') {
      map.fitBounds(RASTER_BOUNDS, { padding: [10, 10] });
    } else if (initialSector !== 'corridor') {
      zoomToSector(initialSector);
    } else {
      map.fitBounds(EXTENTS.corridor.bounds, { padding: [15, 15] });
    }

    const matchScroll = window.location.search.includes('scroll=bottom') || window.location.hash.includes('scroll=bottom');
    if (matchScroll) {
      const pb = document.getElementById('panelBody');
      if (pb) {
        pb.scrollTop = pb.scrollHeight;
      }
    }

    setTimeout(() => {
      if (state.activeWorkspace === 'comparison') {
        updateSwipeDivider();
      }
    }, 100);

    window.__varuna = { state, rasters, map, updateSwipeDivider, switchWorkspace };
    console.log('VARUNA Earth Observation Workspace initialized with workspace:', initialWs, 'sector:', initialSector);
  }

  init();

})();
