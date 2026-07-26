<script setup lang="ts">
/**
 * 统一详情页骨架：诉讼阶段详情、权利指引详情等"详情页"共用同一结构，
 * 避免各详情页各自拼写标题/摘要/来源/打印/返回，出现结构或视觉不一致
 * （见 LAWGUARD_SOT.md P3.4/P3.5 与本次任务"统一详情页模板"要求）。
 *
 * 固定顺序：PageHeader（含一句摘要）→ 关键结论 → 正文 → 下一步 →
 * 官方来源 → 打印 → 边界说明（LegalDisclaimer）→ 返回。
 */
import PageHeader from './PageHeader.vue'
import PrintPageButton from './PrintPageButton.vue'
import PrintFooter from './PrintFooter.vue'
import TrustBanner from './TrustBanner.vue'
import LegalDisclaimer from './LegalDisclaimer.vue'
import StatusBadge, { type StatusKind } from './StatusBadge.vue'

withDefaults(
  defineProps<{
    title: string
    /** 一句话摘要，展示在标题正下方 */
    summary: string
    /** 打印/另存为 PDF 时的中文页面标题 */
    printTitle: string
    /** 返回链接目标路径 */
    backTo: string
    /** 返回链接文案 */
    backLabel: string
    /** 内容审核状态徽标，留空则不展示 */
    status?: StatusKind
  }>(),
  { status: undefined }
)
</script>

<template>
  <div class="container section detail-page">
    <TrustBanner variant="print" />

    <PageHeader :title="title" :description="summary">
      <template #actions>
        <StatusBadge v-if="status" :status="status" />
      </template>
    </PageHeader>

    <TrustBanner variant="compact" class="no-print" />

    <section class="detail-block detail-block--key" aria-labelledby="detail-key-heading">
      <h2 id="detail-key-heading">关键结论</h2>
      <slot name="key-takeaway" />
    </section>

    <section class="detail-block" aria-labelledby="detail-body-heading">
      <h2 id="detail-body-heading">正文</h2>
      <slot name="body" />
    </section>

    <section class="detail-block" aria-labelledby="detail-next-heading">
      <h2 id="detail-next-heading">下一步建议</h2>
      <slot name="next-steps" />
    </section>

    <section class="detail-block" aria-labelledby="detail-source-heading">
      <h2 id="detail-source-heading">官方法律依据</h2>
      <slot name="sources" />
    </section>

    <section class="detail-block detail-block--print no-print">
      <PrintPageButton :page-title="printTitle" />
    </section>

    <section class="detail-block">
      <LegalDisclaimer expanded />
    </section>

    <div class="detail-page__back no-print">
      <RouterLink :to="backTo" class="btn btn-secondary">← {{ backLabel }}</RouterLink>
    </div>

    <PrintFooter />
  </div>
</template>

<style scoped>
.detail-page {
  max-width: 840px;
}

.detail-block {
  margin-top: var(--space-8);
}

.detail-block :deep(h2) {
  margin-bottom: var(--space-3);
}

.detail-block--key {
  padding: var(--space-5);
  background: var(--color-surface-alt);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
}

.detail-block--key :deep(h2) {
  margin-bottom: var(--space-2);
}

.detail-page__back {
  margin-top: var(--space-8);
}
</style>
