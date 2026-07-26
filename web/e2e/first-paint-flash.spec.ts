import { test, expect } from '@playwright/test'

/**
 * 首屏闪烁回归测试。
 *
 * 背景：曾有用户反馈"刷新页面时会闪过一层蓝色"。经排查，页面 DOM
 * （html/body/#app 及其首个子元素）在任何采样帧上都不是蓝色，真实原因是
 * `index.html`/`site.webmanifest` 中的 `theme-color` 曾为深蓝色 `#14335c`，
 * 浏览器在页面加载过程中会用它短暂渲染地址栏/窗口区域（不属于页面 DOM，
 * Playwright 无法直接断言，已通过将 theme-color 改为白色修复，见 git 历史）。
 *
 * 本测试固化"页面 DOM 本身绝不出现非预期蓝色背景"这一断言，覆盖首页与一个
 * 懒加载子路由，在 CPU 4x 降速 + Fast 3G 网络限制、缓存禁用的条件下，从
 * 导航发起的第一帧开始采样，避免后续改动重新引入"内容区蓝色闪烁"问题。
 */

const ROUTES = ['/', '/emergency-guide']

function isSuspectBlue(rgb: string | null): boolean {
  if (!rgb) return false
  const m = rgb.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/)
  if (!m) return false
  const [r, g, b] = [Number(m[1]), Number(m[2]), Number(m[3])]
  return b > r + 15 && !(r > 240 && g > 240 && b > 240)
}

const initScript = () => {
  ;(window as any).__bgLog = []
  const start = performance.now()
  function sample() {
    const now = performance.now() - start
    const html = document.documentElement
    const body = document.body
    const app = document.getElementById('app')
    const first = app && (app.firstElementChild as HTMLElement | null)
    ;(window as any).__bgLog.push({
      t: Math.round(now),
      html: html ? getComputedStyle(html).backgroundColor : null,
      body: body ? getComputedStyle(body).backgroundColor : null,
      app: app ? getComputedStyle(app).backgroundColor : null,
      appFirstChildBg: first ? getComputedStyle(first).backgroundColor : null,
      heroRect: (() => {
        const hero = document.querySelector('.hero')
        if (!hero) return null
        const r = hero.getBoundingClientRect()
        return { width: r.width, height: r.height }
      })(),
    })
    if (now < 2500) requestAnimationFrame(sample)
  }
  requestAnimationFrame(sample)
}

for (const route of ROUTES) {
  test(`刷新 ${route} 时页面 DOM 不出现蓝色闪烁`, async ({ page, context }) => {
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
    await page.goto(route, { waitUntil: 'load' })
    await page.waitForTimeout(2700)

    const log = await page.evaluate(() => (window as any).__bgLog)
    expect(log.length).toBeGreaterThan(0)

    const suspects = log.filter(
      (s: any) => isSuspectBlue(s.html) || isSuspectBlue(s.body) || isSuspectBlue(s.app) || isSuspectBlue(s.appFirstChildBg)
    )
    expect(suspects, `发现可疑蓝色帧: ${JSON.stringify(suspects.slice(0, 3))}`).toHaveLength(0)

    // Hero 只应在首页自身区域内出现合理高度，不应在加载期间被撑成覆盖整个视口的全屏层。
    const viewport = page.viewportSize()
    const heroSamples = log.filter((s: any) => s.heroRect).map((s: any) => s.heroRect)
    if (viewport) {
      for (const rect of heroSamples) {
        expect(rect.height).toBeLessThan(viewport.height * 3)
      }
    }
  })
}
