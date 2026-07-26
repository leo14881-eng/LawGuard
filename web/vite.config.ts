import { loadEnv, type Plugin } from 'vite'
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const dirname = path.dirname(fileURLToPath(import.meta.url))

/** 仅收录公开、稳定、可索引的页面，不包含结果页或带用户输入状态的路径。 */
const PUBLIC_ROUTES = ['/', '/emergency-guide', '/stages', '/documents', '/official-channels', '/about', '/privacy']

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
    },
  }
})
