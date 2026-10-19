// Dev e2e: learn-a-video page (browse, upload, probe, "already analyzed" dialog - never confirmed),
// video result page, style page. Starts no analysis and no skill build.
// node scripts/e2e-videos.mjs <base-url> <outdir> <small-test-file.mp4>
import { chromium } from 'playwright-core'

const [baseUrl, out, testFile] = process.argv.slice(2)
const browser = await chromium.launch({ executablePath: process.env.CHROME || '/usr/bin/google-chrome' })
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } })
const errors = []
page.on('pageerror', (e) => errors.push(e.message))
page.on('console', (m) => { if (m.type() === 'error' && !/409|400/.test(m.text())) errors.push(m.text()) })
const step = (s) => console.log('•', s)

await page.goto(`${baseUrl}/ui/videos/new`)
await page.getByRole('heading', { name: 'Học một video mẫu' }).waitFor()
await page.getByText(/Chọn cả \d+ video/).click()
await page.getByText(/Ước tính/).waitFor()
await page.screenshot({ path: `${out}/vid_new.png` })
step('browse + probe')
await page.getByRole('button', { name: 'Bắt đầu học video' }).click()
await page.getByRole('heading', { name: /Đã học|Lần trước/ }).waitFor()
step('already-analyzed dialog (not confirmed)')
await page.keyboard.press('Escape')

await page.getByRole('button', { name: 'Tải lên' }).click()
await page.locator('input[type=file]').setInputFiles(testFile)
await page.getByRole('button', { name: /Tải lên 1 video/ }).click()
await page.getByText(/Đã tải lên/).waitFor()
step('upload')

await page.goto(`${baseUrl}/ui/videos/20261002-071408`)
await page.getByText('Vì sao người xem bị cuốn').waitFor()
await page.screenshot({ path: `${out}/vid_page.png`, fullPage: true })
await page.getByRole('button', { name: /Tạo phong cách viết/ }).click()
await page.getByText(/đã có\. Tick để/).waitFor()
step('video page + create-style dialog (not submitted)')
await page.keyboard.press('Escape')

await page.goto(`${baseUrl}/ui/styles/hollow-pine`)
await page.getByRole('heading', { name: 'Phong cách hollow-pine' }).waitFor()
await page.getByText('Phiên bản').waitFor()
await page.screenshot({ path: `${out}/style_page.png` })
step('style page')

console.log(errors.length ? `ERRORS:\n${errors.join('\n')}` : 'no console errors')
await browser.close()
