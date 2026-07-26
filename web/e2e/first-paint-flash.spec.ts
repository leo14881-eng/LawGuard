import { test, expect } from '@playwright/test'

/**
 * 首屏闪烁回归测试。
 *
 * 背景：用户反馈"刷新页面时会闪过一层蓝色"，且明确只在浏览器刷新（reload）
 * 时出现，站内路由跳转不会。排查过程：
 *
 * 1. 第一轮怀疑 index.html/site.webmanifest 的 theme-color（曾为深蓝色
 *    #14335c），浏览器会用它短暂渲染地址栏/窗口区域；已改为白色，但这不属于
 *    页面 DOM，本测试无法直接断言。
 * 2. 用 CDP 逐帧采样确认 html/body/#app 及其"第一个子元素"背景色从未变蓝，
 *    但这个断言范围本身有漏洞——它只查了 #app 的第一个子元素（AppHeader），
 *    没有查最后一个子元素 AppFooter。
 * 3. 真正的根因：刷新页面后最初的一段时间里（CPU 降速/弱网下可达
 *    300～900ms），`<RouterView v-slot="{ Component }">` 的 Component 还是
 *    undefined（路由未解析完成），<Suspense> 相当于没有子节点，不会触发
 *    pending/resolve；这段时间 <main> 内容区高度为 0，而 AppFooter（深蓝色
 *    通栏 #0B2545）已经渲染在其后，紧贴 Header 下方短暂出现在视口顶部，内容
 *    到位后又被推到页面底部——这才是"刷新时蓝色一闪而过"的真实来源。只在
 *    刷新时出现，是因为站内路由跳转时目标 chunk 通常已加载，这段空档极短，
 *    刷新时要重新加载整个模块图，空档明显更长。
 * 4. 修复：App.vue 把 <main> 移到 <RouterView v-slot> 内部，用
 *    `!Component || loading` 驱动 `.main--loading`（占满剩余视口高度），
 *    Component 为空或 Suspense 处于 pending 时都生效，避免 Footer 提前可见。
 *
 * 本测试用"先 goto 再 reload"复现真实的刷新场景，在 CPU 4x 降速 + Fast 3G +
 * 缓存禁用条件下逐帧采样，断言：
 * - 不存在覆盖视口较大面积且为蓝色系背景的元素（不局限于固定的几个容器）；
 * - AppFooter 在页面刚刷新的早期阶段不应出现在可视区域内。
 */

const ROUTES = ['/', '/about', '/stages', '/rights-guide']

const initScript = () => {
  // isSuspectBlue 必须定义在这个函数内部：page.addInitScript(fn) 会把 fn
  // 序列化后注入浏览器上下文执行，外层作用域的函数/变量不会一并带入；此前
  // 把它放在外面，导致浏览器里调用时报 ReferenceError（在 requestAnimationFrame
  // 回调里被静默吞掉），采样从未真正写入 __log，log.length 恒为 0。
  function isSuspectBlue(rgb: string | null): boolean {
    if (!rgb) return false
    const m = rgb.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)/)
    if (!m) return false
    const [r, g, b] = [Number(m[1]), Number(m[2]), Number(m[3])]
    const a = m[4] === undefined ? 1 : Number(m[4])
    if (a === 0) return false
    return b > r + 15 && !(r > 240 && g > 240 && b > 240)
  }

  ;(window as any).__log = []
  const start = performance.now()
  function sample() {
    const now = performance.now() - start
    const vw = window.innerWidth
    const vh = window.innerHeight
    const html = document.documentElement
    const body = document.body
    const app = document.getElementById('app')
    const footer = document.querySelector('.footer')

    let largeBlueEl: unknown = null
    const all = document.querySelectorAll('body *')
    for (const el of Array.from(all)) {
      const cs = getComputedStyle(el)
      if (!isSuspectBlue(cs.backgroundColor)) continue
      const r = el.getBoundingClientRect()
      const coverage =
        (Math.max(0, Math.min(r.right, vw) - Math.max(r.left, 0)) * Math.max(0, Math.min(r.bottom, vh) - Math.max(r.top, 0))) /
        (vw * vh)
      if (coverage > 0.15) {
        largeBlueEl = { tag: el.tagName, cls: (el.className || '').toString().slice(0, 60), coverage: Math.round(coverage * 100) }
        break
      }
    }

    ;(window as any).__log.push({
      t: Math.round(now),
      html: html ? getComputedStyle(html).backgroundColor : null,
      body: body ? getComputedStyle(body).backgroundColor : null,
      app: app ? getComputedStyle(app).backgroundColor : null,
      footerVisible: footer ? footer.getBoundingClientRect().top < vh && footer.getBoundingClientRect().bottom > 0 : false,
      largeBlueEl,
    })
    if (now < 2500) requestAnimationFrame(sample)
  }
  requestAnimationFrame(sample)
}

for (const route of ROUTES) {
  test(`刷新 ${route} 时不出现蓝色闪烁（Footer 不提前进入视口）`, async ({ page, context }) => {
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

    // 先正常打开一次，再 reload()——这才是用户描述的"刷新页面"场景，
    // 而不是从空白上下文直接 goto（两者在路由解析时机上表现不完全一致）。
    await page.goto(route, { waitUntil: 'load' })
    await page.evaluate(() => {
      ;(window as any).__log = []
    })
    await page.reload({ waitUntil: 'load' })
    await page.waitForTimeout(2700)

    const log = await page.evaluate(() => (window as any).__log)
    expect(log.length).toBeGreaterThan(0)

    const blueSuspects = log.filter((s: any) => s.largeBlueEl)
    expect(blueSuspects, `发现覆盖视口较大面积的蓝色元素: ${JSON.stringify(blueSuspects.slice(0, 3))}`).toHaveLength(0)

    const footerVisibleEarly = log.filter((s: any) => s.t < 1500 && s.footerVisible)
    expect(footerVisibleEarly, `Footer 在刷新早期即出现在视口内: ${JSON.stringify(footerVisibleEarly.slice(0, 3))}`).toHaveLength(0)
  })
}
