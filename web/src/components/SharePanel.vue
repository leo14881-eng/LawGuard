<script setup lang="ts">
/**
 * 全站统一分享入口：系统原生分享 / 复制链接降级 / 本地二维码 / 本地生成的公益
 * 分享卡片图片。禁止各页面各自实现分享逻辑，新增分享入口一律复用本组件。
 *
 * 隐私与安全：
 * - 分享内容只包含固定文案 + 当前页面的规范 URL（不带 query/hash，见
 *   utils/seo.ts 的 getShareableUrl），不采集、不上传任何用户数据；
 * - 二维码与分享卡片图片均在浏览器本地生成，不调用第三方在线接口；
 * - 不记录分享/复制/二维码下载次数，不接入任何统计或追踪脚本。
 */
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import QRCode from 'qrcode'
import { getShareableUrl } from '../utils/seo'
import { generateShareCard } from '../utils/shareCard'
import { downloadDataUrl } from '../utils/downloadDataUrl'

withDefaults(
  defineProps<{
    variant?: 'primary' | 'compact'
  }>(),
  { variant: 'primary' }
)

const SHARE_TITLE = 'LawGuard｜刑事案件公益应急导航平台'
const SHARE_TEXT =
  '我发现了一个面向刑事案件当事人及家属的纯公益应急导航平台。永久免费，不主动联系用户，不收集个人信息。'

const route = useRoute()
const shareUrl = computed(() => getShareableUrl(route.path))

const feedback = ref('')
const qrOpen = ref(false)
const qrDataUrl = ref('')
const qrLoading = ref(false)
const cardGenerating = ref(false)

function supportsNativeShare(): boolean {
  return typeof navigator !== 'undefined' && typeof navigator.share === 'function'
}

async function handleShare() {
  feedback.value = ''
  if (supportsNativeShare()) {
    try {
      await navigator.share({ title: SHARE_TITLE, text: SHARE_TEXT, url: shareUrl.value })
      return
    } catch (err) {
      // 用户主动取消分享（AbortError）不视为错误，不提示、不降级；
      // 其它失败原因（例如系统分享面板异常）才降级为复制链接。
      if ((err as DOMException)?.name === 'AbortError') {
        return
      }
    }
  }
  await copyLink()
}

async function copyLink() {
  try {
    if (navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
      await navigator.clipboard.writeText(shareUrl.value)
    } else {
      legacyCopy(shareUrl.value)
    }
    feedback.value = '链接已复制，可以发送给需要的人。'
  } catch {
    feedback.value = '复制失败，请手动复制浏览器地址。'
  }
}

/** Clipboard API 不可用时的兼容降级：借助隐藏的可选中文本框 + execCommand('copy')。 */
function legacyCopy(text: string) {
  const textarea = document.createElement('textarea')
  textarea.value = text
  textarea.style.position = 'fixed'
  textarea.style.opacity = '0'
  document.body.appendChild(textarea)
  textarea.focus()
  textarea.select()
  document.execCommand('copy')
  document.body.removeChild(textarea)
}

async function toggleQrCode() {
  qrOpen.value = !qrOpen.value
  if (qrOpen.value && !qrDataUrl.value) {
    qrLoading.value = true
    try {
      qrDataUrl.value = await QRCode.toDataURL(shareUrl.value, { margin: 1, width: 240 })
    } catch {
      feedback.value = '二维码生成失败，请稍后重试。'
    } finally {
      qrLoading.value = false
    }
  }
}

function downloadQrCode() {
  if (!qrDataUrl.value) return
  downloadDataUrl(qrDataUrl.value, 'lawguard-公益应急导航-二维码.png')
}

async function downloadShareCard() {
  feedback.value = ''
  cardGenerating.value = true
  try {
    const dataUrl = await generateShareCard(shareUrl.value)
    downloadDataUrl(dataUrl, 'lawguard-公益应急导航.png')
  } catch {
    feedback.value = '生成分享图片失败，请稍后重试。'
  } finally {
    cardGenerating.value = false
  }
}
</script>

<template>
  <div class="share-panel" :class="`share-panel--${variant}`">
    <div class="share-panel__actions">
      <button type="button" class="btn btn-primary" @click="handleShare">分享给需要的人</button>
      <button type="button" class="btn btn-secondary" @click="toggleQrCode">
        {{ qrOpen ? '收起二维码' : '显示二维码' }}
      </button>
      <button type="button" class="btn btn-secondary" :disabled="cardGenerating" @click="downloadShareCard">
        {{ cardGenerating ? '生成中…' : '下载分享图片' }}
      </button>
    </div>

    <p v-if="variant === 'primary'" class="share-panel__hint">
      如果你觉得 LawGuard 对你有帮助，欢迎分享给真正需要的人。LawGuard 永久免费。
    </p>

    <p v-if="feedback" class="share-panel__feedback" role="status" aria-live="polite">{{ feedback }}</p>

    <div v-if="qrOpen" class="share-panel__qr">
      <p v-if="qrLoading" class="share-panel__hint">正在生成二维码…</p>
      <template v-else-if="qrDataUrl">
        <img :src="qrDataUrl" alt="扫码打开当前页面的二维码" width="160" height="160" />
        <p class="share-panel__qr-caption">扫码打开当前页面</p>
        <p class="share-panel__hint">二维码仅包含当前页面链接，不包含个人信息。</p>
        <button type="button" class="btn btn-secondary share-panel__qr-download" @click="downloadQrCode">
          下载二维码 PNG
        </button>
      </template>
    </div>
  </div>
</template>

<style scoped>
.share-panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.share-panel__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
}

.share-panel--compact .share-panel__actions .btn {
  font-size: var(--font-size-caption);
  padding: var(--space-2) var(--space-4);
}

.share-panel__hint {
  margin: 0;
  font-size: var(--font-size-caption);
  color: var(--color-text-muted);
}

.share-panel__feedback {
  margin: 0;
  font-size: var(--font-size-caption);
  font-weight: 600;
  color: var(--color-success-text);
}

.share-panel__qr {
  margin-top: var(--space-2);
  padding: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-surface);
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--space-2);
}

.share-panel__qr img {
  border-radius: var(--radius-sm);
  background: var(--color-bg);
}

.share-panel__qr-caption {
  margin: 0;
  font-size: var(--font-size-caption);
  font-weight: 600;
  color: var(--color-text);
}

.share-panel__qr-download {
  margin-top: var(--space-1);
}
</style>
