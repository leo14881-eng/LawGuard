import { onMounted, onUnmounted } from 'vue'

/**
 * 向 document.head 注入一段 JSON-LD 结构化数据，组件卸载时移除，避免离开页面
 * （例如从首页跳转到其它路由）后仍残留一份过期的结构化数据。
 * 仅用于站内已确认的事实（见调用方），不得虚构公司/律所/政府机构/官方认证等信息。
 */
export function useJsonLd(data: Record<string, unknown>): void {
  let el: HTMLScriptElement | null = null

  onMounted(() => {
    el = document.createElement('script')
    el.type = 'application/ld+json'
    el.text = JSON.stringify(data)
    document.head.appendChild(el)
  })

  onUnmounted(() => {
    el?.remove()
    el = null
  })
}
