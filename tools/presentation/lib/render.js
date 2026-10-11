// Shared output step for the diagram scripts: write the SVG and a 2x PNG rendered by Chromium.
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..", "..", "..");

// Use CHROME_PATH, else any Chromium Playwright has downloaded (the bundled revision may differ).
function findChromium() {
  if (process.env.CHROME_PATH) return process.env.CHROME_PATH;
  const base = path.join(process.env.LOCALAPPDATA || "", "ms-playwright");
  if (!fs.existsSync(base)) return undefined;
  for (const d of fs.readdirSync(base).filter((n) => /^chromium-\d+$/.test(n)).sort().reverse()) {
    const exe = path.join(base, d, "chrome-win64", "chrome.exe");
    if (fs.existsSync(exe)) return exe;
  }
  return undefined;
}

async function renderSvg(svg, width, height, outSvg, outPng) {
  fs.mkdirSync(path.dirname(outSvg), { recursive: true });
  fs.writeFileSync(outSvg, svg);
  const { chromium } = require(path.join(ROOT, "frontend", "node_modules", "playwright-core"));
  const browser = await chromium.launch({ executablePath: findChromium() });
  try {
    const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 2 });
    await page.setContent(`<html><body style="margin:0">${svg}</body></html>`);
    await page.screenshot({ path: outPng, clip: { x: 0, y: 0, width, height } });
  } finally {
    await browser.close();
  }
  console.log("wrote", outSvg, "and", outPng);
}

module.exports = { ROOT, renderSvg };
