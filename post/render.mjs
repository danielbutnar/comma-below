// Render HTML files in post/ to PNG at their body size, at 2x.
// Usage: node post/render.mjs post/chart-hero-v2.html [more.html ...]
//
// Needs playwright-core (or playwright): `npm i playwright-core` here, or set PLAYWRIGHT_FROM to a folder
// whose node_modules has it, ending in a slash (PLAYWRIGHT_FROM=/opt/node-tools/node_modules/).
// Browser: CHROME_PATH if it is set (any Chromium build), else the installed Google Chrome.
//
// Fonts: the charts ask for "Segoe UI", then Inter, then the system font. The PNGs without a -vN suffix
// were rendered on Windows with Segoe UI; chart-*-v2 and chart-fixes-v5 on Linux with Inter 4 (the
// fonts-inter package). Other fonts have other widths, so look at every PNG for clipped labels. The covers
// load Source Serif 4 and IBM Plex Mono from Google Fonts, so they need a network connection.
import { createRequire } from "node:module";
import path from "node:path";
import { pathToFileURL } from "node:url";

const require = createRequire(process.env.PLAYWRIGHT_FROM ?? import.meta.url);
let playwright;
try {
  playwright = require("playwright-core");
} catch {
  playwright = require("playwright");
}
const { chromium } = playwright;

const files = process.argv.slice(2);
const exe = process.env.CHROME_PATH;
const browser = await chromium.launch(exe ? { executablePath: exe } : { channel: "chrome" });
const page = await browser.newPage({ deviceScaleFactor: 2 });
for (const f of files) {
  const abs = path.resolve(f);
  await page.goto(pathToFileURL(abs).href, { waitUntil: "networkidle" });
  await page.evaluate(() => document.fonts.ready);
  const size = await page.evaluate(() => ({
    width: Math.ceil(document.body.scrollWidth),
    height: Math.ceil(document.body.scrollHeight),
  }));
  await page.setViewportSize(size);
  const out = abs.replace(/\.html$/, ".png");
  await page.screenshot({ path: out, clip: { x: 0, y: 0, ...size } });
  console.log("wrote", out, size);
}
await browser.close();
