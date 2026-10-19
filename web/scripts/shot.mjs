// Dev helper: screenshot UI pages with the system Chrome and print console errors.
// node scripts/shot.mjs <outdir> <width>x<height> <url> [<url> ...]
import { chromium } from 'playwright-core'

const [outDir, size, ...urls] = process.argv.slice(2)
const [width, height] = size.split('x').map(Number)
const browser = await chromium.launch({ executablePath: process.env.CHROME || '/usr/bin/google-chrome' })
const page = await browser.newPage({ viewport: { width, height } })
page.on('console', (m) => { if (m.type() === 'error' || m.type() === 'warning') console.log(`[${m.type()}] ${m.text()}`) })
page.on('pageerror', (e) => console.log(`[pageerror] ${e.message}`))
for (const [i, url] of urls.entries()) {
  await page.goto(url, { waitUntil: 'domcontentloaded' })
  await page.waitForTimeout(2500)
  const file = `${outDir}/shot_${i}.png`
  await page.screenshot({ path: file, fullPage: process.env.FULL === '1' })
  console.log('saved', file, url)
}
await browser.close()
