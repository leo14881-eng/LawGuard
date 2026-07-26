<script setup lang="ts">
/**
 * 打印专用页脚：仅在打印/另存为 PDF 时显示（复用全局 .print-only 工具类），
 * 屏幕上不可见。内容为强制性免责声明与打印日期，不得被隐藏或省略，
 * 用于满足"打印材料需自带法律边界说明"的要求，覆盖各页面的打印输出。
 */
const printedAt = new Date().toISOString().slice(0, 10)
</script>

<template>
  <footer class="print-footer print-only">
    <p class="print-footer__brand">法护 LawGuard</p>
    <p>
      本材料由 LawGuard 根据公开法律法规和官方信息整理，仅提供一般性法律信息，不构成针对具体案件的法律意见，
      也不能替代律师、法律援助机构或办案机关的正式意见。法律规定和案件状态可能发生变化，请核对官方来源及最后核验日期。
    </p>
    <p>被羁押人员能否接收、持有或阅读本材料，应以具体监管场所和办案机关的现行规定为准。</p>
    <p class="print-footer__meta">打印/生成日期：{{ printedAt }}</p>
  </footer>
</template>

<!-- 屏幕上的隐藏/打印时的显示与排版统一由全局 .print-only 工具类与
     style.css 中的 @media print 规则控制，本组件不再重复定义。 -->
