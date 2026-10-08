// Dev e2e: comment on a beat, edit + save a new version, compare. Run against a COPY of a session.
// node scripts/e2e-episode.mjs <base-url> <slug> <sid> <outdir>
import { chromium } from 'playwright-core'

const [baseUrl, slug, sid, out] = process.argv.slice(2)
const browser = await chromium.launch({ executablePath: process.env.CHROME || '/usr/bin/google-chrome' })
const page = await browser.newPage({ viewport: { width: 1600, height: 1100 } })
const errors = []
page.on('pageerror', (e) => errors.push(e.message))
page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()) })
const step = (s) => console.log('•', s)

await page.goto(`${baseUrl}/ui/p/${slug}/${sid}/ep/3`)
await page.getByText('SÁU NHÀ, SÁU ĐỒNG HỒ', { exact: true }).first().waitFor()
step('episode loaded')

const beat = page.locator('#beat-SC1-5')
await beat.hover()
await beat.getByRole('button', { name: /Góp ý/ }).click()
await page.getByPlaceholder('Cần sửa gì ở đoạn này?').fill('Đạt nên giận dữ hơn, đập kính hai lần')
await page.getByRole('button', { name: 'Lưu góp ý' }).click()
await page.getByText('Đạt nên giận dữ hơn, đập kính hai lần').first().waitFor()
step('comment saved and shown')
await page.screenshot({ path: `${out}/e2e_1_comment.png` })

await page.getByRole('button', { name: /Sửa trực tiếp/ }).click()
const action = page.locator('textarea').first()
await action.fill('Dòng nước từ vòi bếp tắt giữa chừng. Giọt cuối rơi xuống bồn, vỡ thành tiếng động duy nhất trong bếp.')
await page.getByPlaceholder('Ghi chú cho lần sửa (không bắt buộc)').fill('thử sửa tay')
await page.getByText('1 đoạn đã đổi').waitFor()
step('edit mode, 1 change counted')
await page.screenshot({ path: `${out}/e2e_2_edit.png` })
await page.getByRole('button', { name: /Lưu thành v2/ }).click()
await page.getByText('Đã lưu thành v2').waitFor()
step('saved as v2')

await page.getByRole('button', { name: /So sánh phiên bản/ }).click()
await page.getByText(/đoạn thay đổi/).waitFor()
step('compare view')
await page.screenshot({ path: `${out}/e2e_3_compare.png` })

console.log(errors.length ? `ERRORS:\n${errors.join('\n')}` : 'no console errors')
await browser.close()
