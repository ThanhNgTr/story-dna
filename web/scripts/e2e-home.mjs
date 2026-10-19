// Dev e2e: home page (filter, hide/restore a project) and the new-series wizard up to the last step
// (does NOT submit, so no Claude job starts). Needs a throwaway session hollow-pine/zz-uitest.
// node scripts/e2e-home.mjs <base-url> <outdir>
import { chromium } from 'playwright-core'

const [baseUrl, out] = process.argv.slice(2)
const browser = await chromium.launch({ executablePath: process.env.CHROME || '/usr/bin/google-chrome' })
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } })
const errors = []
page.on('pageerror', (e) => errors.push(e.message))
page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()) })
const step = (s) => console.log('•', s)

await page.goto(`${baseUrl}/ui/`)
await page.getByRole('heading', { name: 'Dự án của bạn' }).waitFor()
await page.getByRole('heading', { name: 'Phong cách viết' }).waitFor()
await page.getByText('hollow-pine', { exact: true }).first().waitFor()
step('home: projects, styles, reference videos')
await page.screenshot({ path: `${out}/home_1.png`, fullPage: true })

const cards = () => page.locator('a[href*="/p/hollow-pine/"]')
const before = await cards().count()
const testCard = page.locator('div.group', { has: page.locator('a[href$="/p/hollow-pine/zz-uitest"]') })
await testCard.getByRole('button', { name: 'Thêm' }).click()
await page.getByRole('menuitem', { name: /Ẩn dự án/ }).click()
await page.getByText(/Đã ẩn/).first().waitFor()
await page.waitForTimeout(600)
if ((await cards().count()) !== before - 1) throw new Error('project not hidden')
step('hide project')
await page.getByRole('button', { name: /Mục đã ẩn/ }).click()
await page.getByRole('button', { name: /Khôi phục/ }).first().click()
await page.waitForTimeout(800)
await page.keyboard.press('Escape')
if ((await cards().count()) !== before) throw new Error('project not restored')
step('restore project')

await page.getByRole('link', { name: /Series mới/ }).first().click()
await page.getByRole('heading', { name: 'Series mới' }).waitFor()
await page.getByRole('button', { name: /hollow-pine/ }).click()
await page.getByRole('button', { name: 'Tiếp tục' }).click()
await page.getByRole('button', { name: /Dùng mẫu/ }).click()
await page.getByPlaceholder('Ví dụ: Ngôi làng bão').fill('Thử wizard')
await page.locator('textarea').fill('Bối cảnh: một ký túc xá cũ trên núi. Nhân vật: An (20 tuổi) tìm em gái mất tích.')
await page.screenshot({ path: `${out}/wizard_2.png` })
await page.getByRole('button', { name: 'Tiếp tục' }).click()
await page.getByRole('button', { name: '75 giây' }).click()
await page.getByText(/12 tập × 75 giây/).waitFor()
step('wizard: style -> idea -> length (not submitted)')
await page.screenshot({ path: `${out}/wizard_3.png` })

console.log(errors.length ? `ERRORS:\n${errors.join('\n')}` : 'no console errors')
await browser.close()
