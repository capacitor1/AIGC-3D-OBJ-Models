// Headless Edge screenshot harness for the OBJ model.
const fs = require('fs');
const path = require('path');
const http = require('http');
const puppeteer = require('puppeteer-core');

const ROOT = __dirname;
const PORT = 8123;
const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const VIEWS = process.argv.slice(2).length ? process.argv.slice(2) :
  ['hero', 'top', 'top_angle', 'controller', 'nand', 'connector', 'tail', 'bottom', 'bottom_angle'];

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.obj': 'text/plain; charset=utf-8',
  '.mtl': 'text/plain; charset=utf-8',
  '.png': 'image/png',
  '.json': 'application/json',
};

function serve() {
  return new Promise((resolve) => {
    const server = http.createServer((req, res) => {
      let p = decodeURIComponent(req.url.split('?')[0]);
      if (p === '/') p = '/render.html';
      const file = path.join(ROOT, p);
      if (!file.startsWith(ROOT)) { res.writeHead(403); res.end(); return; }
      fs.readFile(file, (err, data) => {
        if (err) { res.writeHead(404); res.end('not found'); return; }
        res.writeHead(200, { 'Content-Type': MIME[path.extname(file)] || 'application/octet-stream' });
        res.end(data);
      });
    });
    server.listen(PORT, '127.0.0.1', () => resolve(server));
  });
}

(async () => {
  const server = await serve();
  const browser = await puppeteer.launch({
    executablePath: EDGE,
    headless: 'new',
    args: [
      '--no-sandbox',
      '--disable-gpu-sandbox',
      '--use-angle=swiftshader',
      '--enable-unsafe-swiftshader',
      '--hide-scrollbars',
      '--force-device-scale-factor=1',
      '--window-size=1800,1000',
    ],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1800, height: 1000, deviceScaleFactor: 1 });
  page.on('console', (msg) => console.log('[page]', msg.text()));
  page.on('pageerror', (err) => console.error('[pageerror]', err.message));

  for (const v of VIEWS) {
    await page.goto(`http://127.0.0.1:${PORT}/render.html?view=${v}`, { waitUntil: 'load' });
    try {
      await page.waitForFunction('window.__ready === true || window.__error', { timeout: 30000 });
      const err = await page.evaluate('window.__error || null');
      if (err) throw new Error(err);
    } catch (e) {
      console.error(`view ${v} failed:`, e.message);
      continue;
    }
    await new Promise(r => setTimeout(r, 350));
    const out = path.join(ROOT, 'renders', `ssd_${v}.png`);
    await page.screenshot({ path: out });
    console.log('wrote', out);
  }
  await browser.close();
  server.close();
})();
