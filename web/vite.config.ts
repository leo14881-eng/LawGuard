import { loadEnv, type Plugin } from 'vite'
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const dirname = path.dirname(fileURLToPath(import.meta.url))

/**
 * 仅收录公开、稳定、可索引的页面，不包含结果页或带用户输入状态的路径
 * （如紧急指引的分步/结果状态本就不写入 URL，见 utils/seo.ts 的
 * getShareableUrl）。
 *
 * STAGE_IDS / RIGHTS_GUIDE_IDS 必须与 `src/data/stages.ts` / `src/data/
 * rightsGuide.ts` 的 id 保持一致（新增/删除阶段或权利指引条目时同步更新）。
 * 没有直接 `import` 这两个数据文件，是因为 vite.config.ts 走的是
 * tsconfig.node.json（module: nodenext），而 src/ 下的文件走
 * tsconfig.app.json（bundler 模式），两者对相对导入是否需要文件扩展名的要求
 * 冲突（nodenext 要求显式扩展名），跨项目导入会导致 vue-tsc -b 报错；用
 * 一份显式同步的 id 列表比在构建配置里绕开这层类型检查更简单可靠。
 */
const STAGE_IDS = ['taken-or-summoned', 'interrogation', 'document-signing', 'prosecution-review', 'trial', 'post-verdict']
const RIGHTS_GUIDE_IDS = STAGE_IDS

const PUBLIC_ROUTES = [
  '/',
  '/emergency-guide',
  '/stages',
  ...STAGE_IDS.map((id) => `/stages/${id}`),
  '/rights-guide',
  ...RIGHTS_GUIDE_IDS.map((id) => `/rights-guide/${id}`),
  '/documents',
  '/official-channels',
  '/about',
  '/privacy',
  '/disclaimer',
  '/legal-sources',
]

/**
 * 生产构建时，如果配置了 VITE_SITE_URL，则：
 * 1. 在 dist/robots.txt 末尾追加 `Sitemap: <SITE_URL>/sitemap.xml`；
 * 2. 生成 dist/sitemap.xml（sitemap 协议要求 <loc> 必须是绝对地址）。
 *
 * 未配置 VITE_SITE_URL 时不生成/不追加任何内容——sitemap.xml 不写入绝对 URL
 * 就不合法，与其编造一个不存在的域名，不如干脆不生成，避免发布虚假地址。
 */
function siteFilesPlugin(siteUrl: string | undefined): Plugin {
  return {
    name: 'lawguard-site-files',
    apply: 'build',
    closeBundle() {
      if (!siteUrl) return
      const outDir = path.resolve(dirname, 'dist')
      if (!fs.existsSync(outDir)) return
      const base = siteUrl.replace(/\/+$/, '')

      const robotsPath = path.join(outDir, 'robots.txt')
      if (fs.existsSync(robotsPath)) {
        fs.appendFileSync(robotsPath, `\nSitemap: ${base}/sitemap.xml\n`)
      }

      const urlEntries = PUBLIC_ROUTES.map((route) => `  <url><loc>${base}${route}</loc></url>`).join('\n')
      const sitemap =
        '<?xml version="1.0" encoding="UTF-8"?>\n' +
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
        `${urlEntries}\n` +
        '</urlset>\n'
      fs.writeFileSync(path.join(outDir, 'sitemap.xml'), sitemap, 'utf-8')
    },
  }
}

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  return {
    plugins: [vue(), siteFilesPlugin(env.VITE_SITE_URL)],
    test: {
      environment: 'jsdom',
      // e2e/ 下是 @playwright/test 用例（真实浏览器，需配合 `npm run test:e2e`
      // 单独运行），不属于 Vitest/jsdom 单元测试范围，需排除，否则会被 Vitest
      // 默认的 *.spec.ts 匹配规则一并收录导致报错。
      exclude: ['node_modules/**', 'e2e/**'],
    },
  }
})
