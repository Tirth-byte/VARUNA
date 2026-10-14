const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const BASE_URL = 'https://varuna-c1m7.onrender.com';
const OUTPUT_DIR = path.resolve(__dirname, '..', 'devpost', 'gallery');

if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

const pause = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function run() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1500, height: 1000 },
    deviceScaleFactor: 1
  });
  const page = await context.newPage();

  console.log(`Navigating to ${BASE_URL}...`);
  await page.goto(BASE_URL, { waitUntil: 'networkidle', timeout: 45000 });
  await page.locator('#map').waitFor({ state: 'visible' });
  await pause(3500);

  // ----------------------------------------------------
  // Image 1: Overview Dashboard
  // ----------------------------------------------------
  console.log('Capturing 01-overview.png...');
  // Ensure full extent
  await page.evaluate(() => {
    if (window.__varuna) {
      window.__varuna.switchWorkspace('comparison');
      const RASTER_BOUNDS = [
        [27.8499136746345, 85.04996096098255],
        [28.2500164946345, 85.40002847098255]
      ];
      window.__varuna.map.fitBounds(RASTER_BOUNDS, { padding: [10, 10] });
      window.__varuna.updateSwipeDivider();
    }
  });
  await pause(2500);
  await page.screenshot({ path: path.join(OUTPUT_DIR, '01-overview.png') });
  console.log('✓ Saved 01-overview.png');

  // ----------------------------------------------------
  // Image 2: Satellite Comparison
  // ----------------------------------------------------
  console.log('Capturing 02-satellite-comparison.png...');
  // Set to Trishuli River Corridor framing, set swipe divider to 45%, enable highlight changes for rich SAR visual
  await page.evaluate(() => {
    if (window.__varuna) {
      window.__varuna.switchWorkspace('comparison');
      const sel = document.getElementById('selCompPreset');
      if (sel) {
        sel.value = 'corridor';
        sel.dispatchEvent(new Event('change'));
      }
      const btnHl = document.getElementById('btnToggleHighlightChanges');
      if (btnHl && !window.__varuna.state.highlightChanges) {
        btnHl.click();
      }
      // Position divider line at 46%
      const line = document.getElementById('swipeDividerLine');
      if (line) line.style.left = '46%';
      window.__varuna.state.swipePosition = 0.46;
      window.__varuna.updateSwipeDivider();
    }
  });
  await pause(3000);
  await page.screenshot({ path: path.join(OUTPUT_DIR, '02-satellite-comparison.png') });
  console.log('✓ Saved 02-satellite-comparison.png');

  // ----------------------------------------------------
  // Image 3: Surface Change Analysis
  // ----------------------------------------------------
  console.log('Capturing 03-surface-change.png...');
  await page.evaluate(() => {
    if (window.__varuna) {
      window.__varuna.switchWorkspace('change');
    }
  });
  await pause(3000);
  await page.screenshot({ path: path.join(OUTPUT_DIR, '03-surface-change.png') });
  console.log('✓ Saved 03-surface-change.png');

  // ----------------------------------------------------
  // Image 4: Infrastructure Exposure
  // ----------------------------------------------------
  console.log('Capturing 04-infrastructure-exposure.png...');
  await page.evaluate(() => {
    if (window.__varuna) {
      window.__varuna.switchWorkspace('exposure');
      // Set to Bidur Confluence or corridor with buildings visible
      const sel = document.getElementById('selExposureSector');
      if (sel) {
        sel.value = 'aoi03';
        sel.dispatchEvent(new Event('change'));
      }
    }
  });
  await pause(3500);
  await page.screenshot({ path: path.join(OUTPUT_DIR, '04-infrastructure-exposure.png') });
  console.log('✓ Saved 04-infrastructure-exposure.png');

  // ----------------------------------------------------
  // Image 5: Reference Validation
  // ----------------------------------------------------
  console.log('Capturing 05-reference-validation.png...');
  await page.evaluate(() => {
    if (window.__varuna) {
      window.__varuna.switchWorkspace('validation');
    }
  });
  await pause(3500);
  await page.screenshot({ path: path.join(OUTPUT_DIR, '05-reference-validation.png') });
  console.log('✓ Saved 05-reference-validation.png');

  // ----------------------------------------------------
  // Image 6: Situation Copilot
  // ----------------------------------------------------
  console.log('Capturing 06-situation-copilot.png...');
  await page.evaluate(() => {
    if (window.__varuna) {
      window.__varuna.switchWorkspace('copilot');
    }
  });
  await pause(1500);

  // Ask grounded operational question via UI
  const query = 'What is the road exposure in the corridor?';
  await page.fill('#copilotQueryInput', query);
  await page.click('#btnCopilotSubmit');

  // Wait for response card to be populated
  await page.waitForSelector('.copilot-answer-text', { state: 'visible', timeout: 10000 });
  await pause(2500);

  await page.screenshot({ path: path.join(OUTPUT_DIR, '06-situation-copilot.png') });
  console.log('✓ Saved 06-situation-copilot.png');

  await browser.close();
  console.log('All 6 images successfully captured!');
}

run().catch((err) => {
  console.error('Capture error:', err);
  process.exit(1);
});
