<script setup lang="ts">
/**
 * 页面打印/保存入口：调用浏览器原生打印能力（window.print()），
 * 不引入服务端 PDF 生成，不开发自定义打印弹窗。
 * 按钮本身通过全局 .no-print 工具类在打印时隐藏。
 *
 * 浏览器原生打印窗口本身（Print/Destination/Pages/Layout/Color/Cancel 等）
 * 不属于本站 DOM，其界面语言由用户浏览器/系统设置决定，前端无法也不应尝试修改。
 */
const props = withDefaults(
  defineProps<{
    /** 打印/另存为 PDF 时用作默认文件名参考的中文页面标题；不传则不改动 document.title */
    pageTitle?: string
  }>(),
  { pageTitle: '' }
)

function handlePrint() {
  const originalTitle = document.title
  if (props.pageTitle) {
    // 打印前临时切换为中文页面标题，让"另存为 PDF"时浏览器建议的默认文件名
    // 为中文而非通用站点标题；window.print() 同步阻塞，打印/另存对话框关闭后
    // 立即恢复原标题，不影响页面其它展示。
    document.title = props.pageTitle
  }
  window.print()
  document.title = originalTitle
}
</script>

<template>
  <div class="print-page-action no-print">
    <button type="button" class="btn btn-secondary" @click="handlePrint">
      打印或保存本页
    </button>
    <p class="print-page-hint">
      点击后将打开浏览器打印窗口。打印窗口的语言由浏览器设置决定；如需保存文件，请在目标打印机中选择
      "另存为 PDF" 或 "Microsoft Print to PDF"。
    </p>
  </div>
</template>

<style scoped>
.print-page-action {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--space-2);
}

.print-page-hint {
  margin: 0;
  font-size: var(--font-size-caption);
  color: var(--color-text-muted);
  max-width: 480px;
}
</style>
