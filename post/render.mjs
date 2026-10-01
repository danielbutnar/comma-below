// Render HTML files in post/ to PNG at their body size.
// Usage: node post/render.mjs post/cover.html [more.html ...]
import { createRequire } from "node:module";
import path from "node:path";
import { pathToFileURL } from "node:url";

// playwright-core: `npm i playwright-core` here, or point PLAYWRIGHT_FROM at a package.json that has it.
const require = createRequire(process.env.PLAYWRIGHT_FROM ?? import.meta.url);
const { chromium } = require("playwright-core");

const files = process.argv.slice(2);
const browser = await chromium.launch({ channel: "chrome" });
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
