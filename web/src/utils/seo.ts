/**
 * 页面级 SEO：根据当前路由动态更新 document.title、meta description、canonical、
 * Open Graph 与 Twitter Card 基础字段。项目为纯前端 SPA（无 SSR），由
 * router.afterEach（见 router/index.ts）在每次路由跳转后调用 applyRouteSeo()，
 * 因此切换路由或返回首页时 metadata 都会同步更新为对应页面的内容。
 *
 * canonical / og:url / og:image 的绝对地址依赖 VITE_SITE_URL 环境变量：
 * - 未配置时（本地开发默认情况）不生成 canonical/og:url，避免把 localhost 写成
 *   对外公开的规范地址；og:image 退化为站内相对路径。
 * - 生产构建必须在环境变量中配置 VITE_SITE_URL（例如
 *   `VITE_SITE_URL=https://lawguard.example.com`），否则打包产物同样不会包含
 *   canonical/og:url，而不是猜测或拼接一个不可靠的地址。
 */
import { defaultRouteSeo, routeSeoMap } from '../data/seo'

export const DEFAULT_OG_IMAGE_PATH = '/og-image.svg'

/** 读取并规范化 VITE_SITE_URL；未配置或为空时返回 null。 */
export function getSiteUrl(): string | null {
  const raw = (import.meta.env.VITE_SITE_URL as string | undefined)?.trim()
  if (!raw) return null
  return raw.replace(/\/+$/, '')
}

/**
 * 生成可安全对外分享/索引的当前页面地址：只使用路由的规范路径本身，不带
 * query/hash，避免把紧急行动指引等页面里用户本地选择的状态编码进可分享链接
 * （本项目的步骤/结果状态本就只保存在组件内存与 localStorage，不写入 URL，
 * 这里再次显式只取 path 作为防御性保证）。
 */
export function getShareableUrl(routePath: string): string {
  const path = routePath.split('?')[0]!.split('#')[0]!
  const siteUrl = getSiteUrl()
  const origin = siteUrl ?? (typeof window !== 'undefined' ? window.location.origin : '')
  return `${origin}${path}`
}

function setMetaTag(attr: 'name' | 'property', key: string, content: string): void {
  let el = document.head.querySelector<HTMLMetaElement>(`meta[${attr}="${key}"]`)
  if (!el) {
    el = document.createElement('meta')
    el.setAttribute(attr, key)
    document.head.appendChild(el)
  }
  el.setAttribute('content', content)
}

function setCanonical(href: string | null): void {
  const existing = document.head.querySelector<HTMLLinkElement>('link[rel="canonical"]')
  if (!href) {
    existing?.remove()
    return
  }
  const el = existing ?? document.createElement('link')
  el.setAttribute('rel', 'canonical')
  el.setAttribute('href', href)
  if (!existing) {
    document.head.appendChild(el)
  }
}

/** 供 router.afterEach 调用：根据路由 name 与 path 应用该页面的 SEO metadata。 */
export function applyRouteSeo(routeName: string | undefined, routePath: string): void {
  const entry = (routeName && routeSeoMap[routeName]) || defaultRouteSeo
  document.title = entry.title
  setMetaTag('name', 'description', entry.description)
  setMetaTag('name', 'robots', entry.noindex ? 'noindex, nofollow' : 'index, follow')

  const siteUrl = getSiteUrl()
  const canonicalUrl = siteUrl ? `${siteUrl}${routePath.split('?')[0]!.split('#')[0]!}` : null
  setCanonical(canonicalUrl)

  const ogImage = siteUrl ? `${siteUrl}${DEFAULT_OG_IMAGE_PATH}` : DEFAULT_OG_IMAGE_PATH

  setMetaTag('property', 'og:title', entry.title)
  setMetaTag('property', 'og:description', entry.description)
  setMetaTag('property', 'og:type', 'website')
  setMetaTag('property', 'og:locale', 'zh_CN')
  setMetaTag('property', 'og:site_name', 'LawGuard')
  setMetaTag('property', 'og:image', ogImage)
  if (canonicalUrl) {
    setMetaTag('property', 'og:url', canonicalUrl)
  }

  setMetaTag('name', 'twitter:card', 'summary_large_image')
  setMetaTag('name', 'twitter:title', entry.title)
  setMetaTag('name', 'twitter:description', entry.description)
  setMetaTag('name', 'twitter:image', ogImage)
}
