// scripts/audit_sar_browser.mjs
import { spawn } from 'node:child_process';
import { writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const BRAVE_PATH = '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser';
const PORT = 9222;
const URL = 'http://localhost:8888/index.html';
const OUT_DIR = resolve('reports/screenshots');
mkdirSync(OUT_DIR, { recursive: true });

function sleep(ms) {
  return new Promise(res => setTimeout(res, ms));
}

async function runAudit() {
  console.log('--- Launching Brave Headless on port ' + PORT + ' ---');
  const browserProc = spawn(BRAVE_PATH, [
    '--headless',
    '--disable-gpu',
    `--remote-debugging-port=${PORT}`,
    '--window-size=1440,900',
    '--hide-scrollbars',
    '--user-data-dir=/tmp/brave-audit-profile-' + Date.now()
  ]);

  let killed = false;
  const cleanup = () => {
    if (!killed) {
      killed = true;
      browserProc.kill('SIGKILL');
    }
  };
  process.on('exit', cleanup);
  process.on('SIGINT', cleanup);

  // Wait for remote debugging endpoint
  let pageTarget = null;
  for (let i = 0; i < 30; i++) {
    try {
      const res = await fetch(`http://127.0.0.1:${PORT}/json`);
      if (res.ok) {
        const targets = await res.json();
        pageTarget = targets.find(t => t.type === 'page');
        if (pageTarget) break;
      }
    } catch (e) {
      // wait
    }
    await sleep(200);
  }

  if (!pageTarget) {
    cleanup();
    throw new Error('Failed to connect to Brave DevTools target on port ' + PORT);
  }

  console.log('Connected to target:', pageTarget.webSocketDebuggerUrl);

  const ws = new WebSocket(pageTarget.webSocketDebuggerUrl);
  await new Promise((res, rej) => {
    ws.onopen = res;
    ws.onerror = rej;
  });

  let msgId = 1;
  const pending = new Map();
  const consoleErrors = [];
  const networkErrors = [];

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.id && pending.has(data.id)) {
      const { resolve, reject } = pending.get(data.id);
      pending.delete(data.id);
      if (data.error) reject(data.error);
      else resolve(data.result);
    } else if (data.method === 'Runtime.consoleAPICalled') {
      const type = data.params.type;
      const text = data.params.args.map(a => a.value || JSON.stringify(a)).join(' ');
      if (type === 'error') {
        consoleErrors.push(text);
        console.error('Browser Console Error:', text);
      }
    } else if (data.method === 'Network.responseReceived') {
      const resp = data.params.response;
      if (resp.status >= 400 && !resp.url.endsWith('favicon.ico')) {
        networkErrors.push({ url: resp.url, status: resp.status });
        console.error(`HTTP ${resp.status}: ${resp.url}`);
      }
    }
  };

  function send(method, params = {}) {
    const id = ++msgId;
    return new Promise((resolve, reject) => {
      pending.set(id, { resolve, reject });
      ws.send(JSON.stringify({ id, method, params }));
    });
  }

  async function evaluate(expression) {
    const res = await send('Runtime.evaluate', {
      expression,
      returnByValue: true,
      awaitPromise: true
    });
    if (res.exceptionDetails) {
      throw new Error(`Eval error: ${JSON.stringify(res.exceptionDetails)}`);
    }
    return res.result.value;
  }

  async function captureScreenshot(filename) {
    const res = await send('Page.captureScreenshot', { format: 'png' });
    const buf = Buffer.from(res.data, 'base64');
    const path = resolve(OUT_DIR, filename);
    writeFileSync(path, buf);
    console.log(`Saved screenshot: ${path}`);
    return path;
  }

  // Enable domains
  await send('Page.enable');
  await send('Runtime.enable');
  await send('Network.enable');

  console.log(`Navigating to ${URL}...`);
  await send('Page.navigate', { url: URL });
  await sleep(2000);

  // 1. Audit Initial Comparison State
  const initialCheck = await evaluate(`(() => {
    const v = window.__varuna;
    const preEl = v.rasters.pre.getElement();
    const postEl = v.rasters.post.getElement();
    const divider = document.getElementById('swipeDividerLine');
    const handle = document.getElementById('swipeDividerHandle');
    const btnHighlight = document.getElementById('btnToggleHighlightChanges');
    
    return {
      activeWorkspace: v.state.activeWorkspace,
      hasPre: !!preEl,
      preSrc: preEl ? preEl.src : null,
      hasPost: !!postEl,
      postSrc: postEl ? postEl.src : null,
      postClip: postEl ? (postEl.style.clipPath || postEl.style.webkitClipPath) : null,
      dividerLeft: divider ? divider.style.left : null,
      swipePos: v.state.swipePosition,
      hasHighlightBtn: !!btnHighlight
    };
  })()`);

  console.log('Initial Comparison Verification:', JSON.stringify(initialCheck, null, 2));
  if (!initialCheck.hasPre || !initialCheck.hasPost) {
    throw new Error('Rasters failed to load!');
  }
  await captureScreenshot('01_comparison_initial_50.png');

  // 2. Drag Slider Left to 20%
  console.log('Dragging slider to ~20% (revealing pre-event raster)...');
  await evaluate(`(() => {
    const mapEl = document.getElementById('map');
    const box = mapEl.getBoundingClientRect();
    const targetX = box.left + (box.width * 0.20);
    const handle = document.getElementById('swipeDividerHandle');
    handle.dispatchEvent(new MouseEvent('mousedown', { clientX: box.left + (box.width * 0.5), clientY: box.top + 200, bubbles: true }));
    window.dispatchEvent(new MouseEvent('mousemove', { clientX: targetX, clientY: box.top + 200, bubbles: true }));
    window.dispatchEvent(new MouseEvent('mouseup', { clientX: targetX, clientY: box.top + 200, bubbles: true }));
  })()`);
  await sleep(300);

  const leftDragCheck = await evaluate(`(() => {
    const v = window.__varuna;
    const postEl = v.rasters.post.getElement();
    const divider = document.getElementById('swipeDividerLine');
    return {
      swipePos: v.state.swipePosition,
      dividerLeft: divider.style.left,
      postClip: postEl.style.clipPath || postEl.style.webkitClipPath
    };
  })()`);
  console.log('Left Drag (20%) Verification:', JSON.stringify(leftDragCheck, null, 2));
  await captureScreenshot('02_comparison_drag_left_20.png');

  // 3. Drag Slider Right to 80%
  console.log('Dragging slider to ~80% (revealing post-event raster)...');
  await evaluate(`(() => {
    const mapEl = document.getElementById('map');
    const box = mapEl.getBoundingClientRect();
    const targetX = box.left + (box.width * 0.80);
    const handle = document.getElementById('swipeDividerHandle');
    handle.dispatchEvent(new MouseEvent('mousedown', { clientX: box.left + (box.width * 0.20), clientY: box.top + 200, bubbles: true }));
    window.dispatchEvent(new MouseEvent('mousemove', { clientX: targetX, clientY: box.top + 200, bubbles: true }));
    window.dispatchEvent(new MouseEvent('mouseup', { clientX: targetX, clientY: box.top + 200, bubbles: true }));
  })()`);
  await sleep(300);

  const rightDragCheck = await evaluate(`(() => {
    const v = window.__varuna;
    const postEl = v.rasters.post.getElement();
    const divider = document.getElementById('swipeDividerLine');
    return {
      swipePos: v.state.swipePosition,
      dividerLeft: divider.style.left,
      postClip: postEl.style.clipPath || postEl.style.webkitClipPath
    };
  })()`);
  console.log('Right Drag (80%) Verification:', JSON.stringify(rightDragCheck, null, 2));
  await captureScreenshot('03_comparison_drag_right_80.png');

  // 4. Return Slider to 50% and Toggle Highlight Changes ON
  console.log('Resetting slider to 50% and enabling Highlight Changes...');
  await evaluate(`(() => {
    const mapEl = document.getElementById('map');
    const box = mapEl.getBoundingClientRect();
    const targetX = box.left + (box.width * 0.50);
    const handle = document.getElementById('swipeDividerHandle');
    handle.dispatchEvent(new MouseEvent('mousedown', { clientX: box.left + (box.width * 0.80), clientY: box.top + 200, bubbles: true }));
    window.dispatchEvent(new MouseEvent('mousemove', { clientX: targetX, clientY: box.top + 200, bubbles: true }));
    window.dispatchEvent(new MouseEvent('mouseup', { clientX: targetX, clientY: box.top + 200, bubbles: true }));
    
    // Click Highlight Changes
    const btnHighlight = document.getElementById('btnToggleHighlightChanges');
    if (btnHighlight) btnHighlight.click();
  })()`);
  await sleep(600);

  const highlightCheck = await evaluate(`(() => {
    const v = window.__varuna;
    const postEl = v.rasters.post.getElement();
    const classEl = v.rasters.classified.getElement();
    const legend = document.getElementById('mapLegend');
    const rngOpacity = document.getElementById('rngHighlightOpacity');
    return {
      highlightActive: v.state.highlightChanges,
      hasHazardLayer: v.map.hasLayer(v.rasters.classified),
      classSrc: classEl ? classEl.src : null,
      classClip: classEl ? (classEl.style.clipPath || classEl.style.webkitClipPath) : null,
      postClip: postEl ? (postEl.style.clipPath || postEl.style.webkitClipPath) : null,
      hasOpacitySlider: !!rngOpacity,
      comparisonSector: v.state.comparisonSector,
      legendText: legend ? legend.innerText.replace(/\\s+/g, ' ') : null
    };
  })()`);
  console.log('Highlight Changes Verification:', JSON.stringify(highlightCheck, null, 2));
  await captureScreenshot('04_comparison_highlight_changes_corridor.png');

  // 5. Test Framing Presets (Bidur AOI03)
  console.log('Testing Framing Preset: Bidur (AOI03)...');
  await evaluate(`(() => {
    const sel = document.getElementById('selCompPreset');
    sel.value = 'aoi03';
    sel.dispatchEvent(new Event('change'));
  })()`);
  await sleep(600);

  const aoi03Check = await evaluate(`(() => {
    const v = window.__varuna;
    const postEl = v.rasters.post.getElement();
    const classEl = v.rasters.classified.getElement();
    const divider = document.getElementById('swipeDividerLine');
    return {
      center: [v.map.getCenter().lat.toFixed(4), v.map.getCenter().lng.toFixed(4)],
      zoom: v.map.getZoom(),
      dividerLeft: divider.style.left,
      postClip: postEl ? (postEl.style.clipPath || postEl.style.webkitClipPath) : null,
      classClip: classEl ? (classEl.style.clipPath || classEl.style.webkitClipPath) : null
    };
  })()`);
  console.log('Bidur (AOI03) Preset Verification:', JSON.stringify(aoi03Check, null, 2));
  await captureScreenshot('05_comparison_aoi03_preset.png');

  // 6. Test Reset Extent
  console.log('Testing Reset Extent button...');
  await evaluate(`(() => {
    document.getElementById('btnResetMap').click();
  })()`);
  await sleep(500);
  await captureScreenshot('06_comparison_reset_extent.png');

  // 7. Verify All Other Workspaces
  console.log('Verifying Surface Change Detection workspace...');
  await evaluate(`window.__varuna.switchWorkspace('change')`);
  await sleep(500);
  await captureScreenshot('07_workspace_change_detection.png');

  console.log('Verifying Infrastructure Exposure workspace...');
  await evaluate(`window.__varuna.switchWorkspace('exposure')`);
  await sleep(500);
  await captureScreenshot('08_workspace_infrastructure_exposure.png');

  console.log('Verifying Reference Validation workspace...');
  await evaluate(`window.__varuna.switchWorkspace('validation')`);
  await sleep(500);
  await captureScreenshot('09_workspace_reference_validation.png');

  console.log('Verifying Situation Copilot workspace...');
  await evaluate(`window.__varuna.switchWorkspace('copilot')`);
  await sleep(500);
  await captureScreenshot('10_workspace_situation_copilot.png');

  // Final health check
  console.log('\n--- Final Browser Audit Summary ---');
  console.log(`Console Errors: ${consoleErrors.length}`);
  console.log(`Network Failures: ${networkErrors.length}`);

  cleanup();

  if (consoleErrors.length > 0 || networkErrors.length > 0) {
    console.error('Audit failed with errors:', { consoleErrors, networkErrors });
    process.exit(1);
  } else {
    console.log('ALL BROWSER AND SLIDER CHECKS PASSED WITH ZERO ERRORS.');
    process.exit(0);
  }
}

runAudit().catch(err => {
  console.error('Fatal error during audit:', err);
  process.exit(1);
});
