// Dev e2e: looks pages (approve, bulk review, edit -> new registry version, lightbox) and the
// screenplay links into them. Never generates images. Run on a COPY: hollow-pine/zz-uitest.
// node scripts/e2e-looks.mjs <base-url> <outdir>
import { chromium } from 'playwright-core'

const [baseUrl, out] = process.argv.slice(2)
const P = `${baseUrl}/ui/p/hollow-pine/zz-uitest`
const browser = await chromium.launch({ executablePath: process.env.CHROME || '/usr/bin/google-chrome' })
const page = await browser.newPage({ viewport: { width: 1500, height: 1000 } })
const errors = []
page.on('pageerror', (e) => errors.push(e.message))
page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()) })
const step = (s) => console.log('•', s)

await page.goto(`${P}/looks/characters`)
await page.getByRole('heading', { name: 'Ngoại hình' }).waitFor()
await page.locator('#char_02').scrollIntoViewIfNeeded()
await page.waitForTimeout(800)
await page.screenshot({ path: `${out}/looks_chars.png` })
step('characters tab')

await page.locator('#char_02 figure button').first().click()
await page.getByRole('button', { name: /Duyệt làm ảnh chuẩn/ }).click()
await page.getByRole('dialog').getByText('Đã duyệt').first().waitFor()
await page.keyboard.press('Escape')
step('lightbox approve')

await page.goto(`${P}/looks/review`)
await page.getByText(/ảnh chờ duyệt/).waitFor()
await page.getByRole('button', { name: 'Chọn tất cả' }).click()
await page.screenshot({ path: `${out}/looks_review.png` })
await page.getByRole('button', { name: /^Duyệt \d+/ }).click()
await page.getByText('Không có ảnh nào chờ duyệt.').waitFor()
step('bulk approve')

await page.goto(`${P}/looks/characters#char_05`)
await page.locator('#char_05').getByRole('button', { name: /Sửa/ }).click()
const hair = page.getByRole('dialog').locator('label', { hasText: 'Tóc' }).locator('input')
await hair.fill('tóc ngắn ngang tai, kẹp một bên')
await page.getByRole('button', { name: 'Lưu thành phiên bản mới' }).click()
await page.getByText(/Đã lưu thành assets_v\d+\.json/).waitFor()
await page.locator('#char_05').getByText('tóc ngắn ngang tai, kẹp một bên').waitFor()
step('edit character -> new registry version')

await page.goto(`${P}/looks/locations`)
await page.locator('#loc_02').waitFor()
await page.screenshot({ path: `${out}/looks_locs.png` })
await page.goto(`${P}/looks/issues`)
await page.getByText('Cách sửa:').first().waitFor()
step('locations + issues tabs')

await page.goto(`${P}/ep/3`)
await page.getByRole('link', { name: /Bếp kính/ }).first().waitFor()
await page.screenshot({ path: `${out}/looks_ep.png` })
await page.getByRole('link', { name: /Bếp kính/ }).first().click()
await page.waitForURL(/looks\/locations#/)
step('screenplay scene -> location link')

console.log(errors.length ? `ERRORS:\n${errors.join('\n')}` : 'no console errors')
await browser.close()
