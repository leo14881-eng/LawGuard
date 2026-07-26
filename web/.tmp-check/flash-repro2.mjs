import { chromium } from 'playwright'
import fs from 'node:fs'

const OUT = 'C:/Users/LENOVO/AppData/Local/Temp/claude/D--SOFT-LawGuard/cbe3e663-5863-41b8-9a96-bb246feed02d/scratchpad/flash2'
fs.mkdirSync(OUT, { recursive: true })

const targets = [
  ['dev', 'http://localhost:5196'],
  ['preview', 'http://localhost:5195'],
]
const routes = ['/', '/about', '/stages', '/rights-guide']

// 采样器：记录 html/body/#app 背景色，并扫描"是否存在覆盖较大视口面积且为
// 蓝色系背景"的元素（不局限于 4 个固定容器），同时单独跟踪 footer 的位置。
const initScript = () => {
  window.__log = []
  const start = performance.now()
  function isBluish(rgb) {
    const m = rgb && rgb.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)/)
    if (!m) return false
    const [r, g, b] = [Number(m[1]), Number(m[2]), Number(m[3])]
    const a = m[4] === undefined ? 1 : Number(m[4])
    if (a === 0) return false
    return b > r + 15 && !(r > 240 && g > 240 && b > 240)
  }
  function sample() {
    const now = performance.now() - start
    const vw = window.innerWidth
    const vh = window.innerHeight
    const html = document.documentElement
    const body = document.body
    const app = document.getElementById('app')
    const footer = document.querySelector('.footer')
    const header = document.querySelector('.header')
    // 扫描所有元素，找出"覆盖视口面积较大 + 背景色偏蓝"的候选者
    let largeBlueEl = null
    const all = document.querySelectorAll('body *')
    for (const el of all) {
      const cs = getComputedStyle(el)
      if (!isBluish(cs.backgroundColor)) continue
      const r = el.getBoundingClientRect()
      const coverage = (Math.max(0, Math.min(r.right, vw) - Math.max(r.left, 0)) * Math.max(0, Math.min(r.bottom, vh) - Math.max(r.top, 0))) / (vw * vh)
      if (coverage > 0.15) {
        largeBlueEl = {
          tag: el.tagName,
          cls: el.className && el.className.toString().slice(0, 60),
          coverage: Math.round(coverage * 100),
          rect: { top: Math.round(r.top), left: Math.round(r.left), width: Math.round(r.width), height: Math.round(r.height) },
          bg: cs.backgroundColor,
        }
        break
      }
    }
    window.__log.push({
      t: Math.round(now),
      html: html ? getComputedStyle(html).backgroundColor : null,
      body: body ? getComputedStyle(body).backgroundColor : null,
      app: app ? getComputedStyle(app).backgroundColor : null,
      footerTop: footer ? Math.round(footer.getBoundingClientRect().top) : null,
      footerVisible: footer ? footer.getBoundingClientRect().top < vh && footer.getBoundingClientRect().bottom > 0 : false,
      footerBg: footer ? getComputedStyle(footer).backgroundColor : null,
      headerVisible: !!header,
      largeBlueEl,
    })
    if (now < 3000) requestAnimationFrame(sample)
  }
  requestAnimationFrame(sample)
}

const browser = await chromium.launch()
const report = []

for (const [envName, base] of targets) {
  for (const route of routes) {
    const context = await browser.newContext({
      viewport: { width: 1440, height: 900 },
      serviceWorkers: 'block',
      recordVideo: { dir: `${OUT}/video-${envName}-${route.replace(/\//g, '_') || 'home'}`, size: { width: 1440, height: 900 } },
    })
    const page = await context.newPage()
    const client = await context.newCDPSession(page)
    await client.send('Network.enable')
    await client.send('Network.setCacheDisabled', { cacheDisabled: true })
    await client.send('Network.emulateNetworkConditions', {
      offline: false,
      latency: 150,
      downloadThroughput: (1.6 * 1024 * 1024) / 8,
      uploadThroughput: (750 * 1024) / 8,
    })
    await client.send('Emulation.setCPUThrottlingRate', { rate: 4 })
    await page.addInitScript(initScript)

    // 场景：先正常打开一次（让浏览器有机会缓存部分资源，更贴近真实用户"已经打开过页面，按 F5 刷新"的场景），
    // 然后清空日志并执行 reload()，这才是用户反馈的"刷新"场景。
    await page.goto(base + route, { waitUntil: 'load', timeout: 60000 })
    await page.evaluate(() => { window.__log = [] })
    await page.reload({ waitUntil: 'load', timeout: 60000 })
    await page.waitForTimeout(3200)

    const log = await page.evaluate(() => window.__log)
    const footerVisibleEarly = log.filter((s) => s.t < 1500 && s.footerVisible)
    const blueSuspects = log.filter((s) => s.largeBlueEl)

    report.push({
      env: envName,
      route,
      totalSamples: log.length,
      footerVisibleEarlyCount: footerVisibleEarly.length,
      footerVisibleEarlySamples: footerVisibleEarly.slice(0, 5),
      blueSuspectCount: blueSuspects.length,
      blueSuspectSamples: blueSuspects.slice(0, 5),
      first10: log.slice(0, 10),
    })

    await context.close()
  }
}

await browser.close()
fs.writeFileSync(`${OUT}/report.json`, JSON.stringify(report, null, 2))

console.log('=== Footer 在刷新后 1.5s 内出现在视口内的场景 ===')
for (const r of report) {
  if (r.footerVisibleEarlyCount > 0) {
    console.log(`[${r.env}] ${r.route}: footer 在 ${r.footerVisibleEarlyCount}/${r.totalSamples} 帧内可见，示例:`, JSON.stringify(r.footerVisibleEarlySamples[0]))
  }
}
console.log('=== 大面积蓝色元素可疑场景 ===')
for (const r of report) {
  if (r.blueSuspectCount > 0) {
    console.log(`[${r.env}] ${r.route}: ${r.blueSuspectCount} 帧发现大面积蓝色元素，示例:`, JSON.stringify(r.blueSuspectSamples[0]))
  }
}
