const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const BASE_URL = 'http://localhost:8888';
const OUTPUT_DIR = path.resolve(__dirname, '..', 'reports', 'demo_recording');
const RAW_DIR = path.join(OUTPUT_DIR, '.playwright_raw');
const VIEWPORT = { width: 1920, height: 1080 };

fs.mkdirSync(RAW_DIR, { recursive: true });

const pause = (page, ms) => page.waitForTimeout(ms);

async function moveOver(page, x, y, duration = 700, steps = 35) {
  const current = await page.evaluate(() => ({ x: window.__cursorX || 960, y: window.__cursorY || 540 }));
  for (let i = 1; i <= steps; i += 1) {
    const t = i / steps;
    const eased = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
    const nx = current.x + (x - current.x) * eased;
    const ny = current.y + (y - current.y) * eased;
    await page.mouse.move(nx, ny);
    await page.evaluate(([cx, cy]) => { window.__cursorX = cx; window.__cursorY = cy; }, [nx, ny]);
    await page.waitForTimeout(Math.max(1, Math.floor(duration / steps)));
  }
}

async function moveToLocator(page, locator, duration = 700) {
  const box = await locator.boundingBox();
  if (!box) throw new Error(`Locator is not visible: ${locator}`);
  await moveOver(page, box.x + box.width / 2, box.y + box.height / 2, duration);
  return box;
}

async function hoverClick(page, selectorOrLocator, duration = 650) {
  const locator = typeof selectorOrLocator === 'string' ? page.locator(selectorOrLocator) : selectorOrLocator;
  await moveToLocator(page, locator, duration);
  await pause(page, 250);
  await page.mouse.down();
  await pause(page, 120);
  await page.mouse.up();
}

async function openDashboard(page) {
  await page.goto(BASE_URL, { waitUntil: 'networkidle', timeout: 60000 });
  await page.locator('#map').waitFor({ state: 'visible' });
  await pause(page, 1800);
}

async function saveVideo(video, destination) {
  await video.saveAs(path.join(RAW_DIR, destination));
}

async function recordDashboardClip(browser, filename, action) {
  const context = await browser.newContext({
    viewport: VIEWPORT,
    recordVideo: { dir: RAW_DIR, size: VIEWPORT },
    deviceScaleFactor: 1,
  });
  const page = await context.newPage();
  const video = page.video();
  await openDashboard(page);
  await action(page);
  await page.close();
  await context.close();
  await saveVideo(video, filename);
  process.stdout.write(`RECORDED ${filename}\n`);
}

async function recordPdfClip(browser, filename, triggerSelector, action) {
  const context = await browser.newContext({
    viewport: VIEWPORT,
    recordVideo: { dir: RAW_DIR, size: VIEWPORT },
    deviceScaleFactor: 1,
  });
  const page = await context.newPage();
  await openDashboard(page);
  const popupPromise = page.waitForEvent('popup');
  await hoverClick(page, triggerSelector);
  const popup = await popupPromise;
  const video = popup.video();
  await popup.waitForTimeout(5000);
  await action(popup);
  await popup.close();
  await page.close();
  await context.close();
  await saveVideo(video, filename);
  process.stdout.write(`RECORDED ${filename}\n`);
}

(async () => {
  const browser = await chromium.launch({ headless: false });
  try {
    await recordDashboardClip(browser, '01_dashboard_intro.webm', async (page) => {
      await moveToLocator(page, page.locator('.brand-section'), 900);
      await pause(page, 1400);
      await moveToLocator(page, page.locator('#map'), 1200);
      await pause(page, 1800);
      await moveToLocator(page, page.locator('#analysisPanel'), 1100);
      await pause(page, 1700);
    });

    await recordDashboardClip(browser, '02_satellite_comparison.webm', async (page) => {
      const mapBox = await page.locator('#map').boundingBox();
      const handle = page.locator('#swipeDividerHandle');
      const handleBox = await moveToLocator(page, handle, 700);
      await page.mouse.down();
      const y = handleBox.y + handleBox.height / 2;
      for (const [ratio, hold] of [[0.20, 1700], [0.50, 1700], [0.80, 2100]]) {
        await moveOver(page, mapBox.x + mapBox.width * ratio, y, 1500, 55);
        await pause(page, hold);
      }
      await page.mouse.up();
      await hoverClick(page, '#btnToggleHighlightChanges', 800);
      await pause(page, 2600);
      const updatedMap = await page.locator('#map').boundingBox();
      const updatedHandle = page.locator('#swipeDividerHandle');
      const updatedHandleBox = await moveToLocator(page, updatedHandle, 650);
      await page.mouse.down();
      await moveOver(page, updatedMap.x + updatedMap.width * 0.20, updatedHandleBox.y + updatedHandleBox.height / 2, 1800, 65);
      await page.mouse.up();
      await pause(page, 4200);
    });

    await recordDashboardClip(browser, '03_surface_change.webm', async (page) => {
      await hoverClick(page, '#btnWsChange');
      await pause(page, 3300);
      await moveToLocator(page, page.getByText('126.60 km²', { exact: true }).first(), 700);
      await pause(page, 1900);
      await moveToLocator(page, page.getByText('108.21 km²', { exact: true }).first(), 700);
      await pause(page, 1900);
      await hoverClick(page, 'button[data-type="water"]');
      await pause(page, 2500);
      await hoverClick(page, 'button[data-type="debris"]');
      await pause(page, 2500);
      await hoverClick(page, 'button[data-type="classified"]');
      await pause(page, 2900);
    });

    await recordDashboardClip(browser, '04_infrastructure_exposure.webm', async (page) => {
      await hoverClick(page, '#btnWsExposure');
      await pause(page, 3300);
      await moveToLocator(page, page.getByText('1,062', { exact: true }).first(), 700);
      await pause(page, 1700);
      await moveToLocator(page, page.getByText('35.12 km', { exact: true }).first(), 700);
      await pause(page, 1800);
      await hoverClick(page, '#selExposureSector');
      await page.keyboard.press('ArrowDown');
      await page.keyboard.press('Enter');
      await pause(page, 3500);
      await hoverClick(page, '#btnZoomIn');
      await pause(page, 3500);
      await moveToLocator(page, page.locator('#mapLegend'), 900);
      await pause(page, 2100);
    });

    await recordDashboardClip(browser, '05_reference_validation.webm', async (page) => {
      await hoverClick(page, '#btnWsValidation');
      await pause(page, 3600);
      await moveToLocator(page, page.getByText('37.16%', { exact: true }).first(), 800);
      await pause(page, 2600);
      await moveToLocator(page, page.locator('#mapLegend'), 900);
      await pause(page, 2200);
      await hoverClick(page, '#btnToggleSarUnderlay');
      await pause(page, 3100);
      await moveToLocator(page, page.getByText('Observed Event Overlap vs Classifier Accuracy', { exact: true }), 900);
      await pause(page, 3200);
    });

    await recordDashboardClip(browser, '06_situation_copilot.webm', async (page) => {
      await hoverClick(page, '#btnWsCopilot');
      await pause(page, 1900);
      await hoverClick(page, '#copilotQueryInput');
      await page.keyboard.type('How much road infrastructure intersects the detected hazard areas?', { delay: 38 });
      await pause(page, 500);
      await hoverClick(page, '#btnCopilotSubmit', 500);
      await page.getByText('35.12 km', { exact: false }).first().waitFor({ state: 'visible', timeout: 8000 });
      await pause(page, 5200);
      await hoverClick(page, '#btnLangNe', 600);
      await pause(page, 1200);
      await hoverClick(page, page.locator('.copilot-chip').filter({ hasText: 'सडक पूर्वाधार' }), 650);
      await page.getByText('३५.१२', { exact: false }).first().waitFor({ state: 'visible', timeout: 8000 });
      await pause(page, 5200);
    });

    await recordPdfClip(browser, '07_situation_report.webm', '#btnExportSitrep', async (page) => {
      await moveOver(page, 1090, 145, 900);
      await pause(page, 2600);
      await moveOver(page, 1110, 355, 900);
      await pause(page, 2800);
      await moveOver(page, 1110, 790, 900);
      await pause(page, 3000);
    });

    await recordPdfClip(browser, '08_research_report.webm', '#btnExportResearch', async (page) => {
      await moveOver(page, 1120, 200, 900);
      await pause(page, 2500);
      for (let i = 0; i < 3; i += 1) {
        await page.keyboard.press('PageDown');
        await pause(page, 3000);
      }
      await pause(page, 1800);
    });

    await recordDashboardClip(browser, '09_closing_dashboard.webm', async (page) => {
      await hoverClick(page, '#btnToggleHighlightChanges', 700);
      await pause(page, 2500);
      const mapBox = await page.locator('#map').boundingBox();
      const handle = page.locator('#swipeDividerHandle');
      const handleBox = await moveToLocator(page, handle, 700);
      await page.mouse.down();
      await moveOver(page, mapBox.x + mapBox.width * 0.38, handleBox.y + handleBox.height / 2, 1600, 60);
      await page.mouse.up();
      await pause(page, 4200);
    });
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
