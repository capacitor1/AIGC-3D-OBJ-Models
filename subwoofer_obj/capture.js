const { chromium } = require('playwright-core');
const path = require('path');

const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const BASE = 'http://127.0.0.1:8765/viewer.html';

(async () => {
  const browser = await chromium.launch({
    executablePath: EDGE,
    headless: true,
    args: [
      '--use-angle=swiftshader',
      '--enable-unsafe-swiftshader',
      '--disable-gpu-sandbox',
      '--ignore-gpu-blocklist',
      '--enable-webgl',
      '--disable-dev-shm-usage'
    ]
  });
  const page = await browser.newPage({ viewport: { width: 1400, height: 1100 }, deviceScaleFactor: 1 });
  page.on('console', msg => console.log('PAGE', msg.type(), msg.text()));
  page.on('pageerror', err => console.log('PAGEERROR', err.message));
  for (const view of ['hero', 'front', 'side', 'rear', 'detail', 'top']) {
    await page.goto(`${BASE}?screenshot=1&view=${view}`, { waitUntil: 'load', timeout: 120000 });
    await page.waitForFunction('window.__READY__ === true', null, { timeout: 120000 });
    await page.waitForTimeout(900);
    const out = path.join(__dirname, 'renders', `sw12_${view}.png`);
    await page.screenshot({ path: out });
    console.log('saved', out);
  }
  await browser.close();
})().catch(err => { console.error(err); process.exit(1); });
