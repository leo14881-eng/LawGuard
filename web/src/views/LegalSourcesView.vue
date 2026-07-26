<script setup lang="ts">
import PageHeader from '../components/PageHeader.vue'
import LegalDisclaimer from '../components/LegalDisclaimer.vue'
import SourceCitationCard from '../components/SourceCitationCard.vue'
import PrintPageButton from '../components/PrintPageButton.vue'
import PrintFooter from '../components/PrintFooter.vue'
import { legalSources } from '../data/legal_sources'
</script>

<template>
  <div class="container section">
    <PageHeader
      title="法律来源与版本记录"
      description="本页面记录法护内容对应的法律依据来源、版本与核验状态，未完成核验的内容不会标注为已核验。"
    >
      <template #actions>
        <PrintPageButton page-title="法律来源与版本记录 - 法护 LawGuard" />
      </template>
    </PageHeader>

    <LegalDisclaimer />

    <section class="section">
      <h2>内容依据原则</h2>
      <ul>
        <li>所有正式法律内容必须来自可核验的公开正式文本；</li>
        <li>不得仅凭模型记忆作为发布依据；</li>
        <li>未经执业律师审核前，统一标注为"待法律复核"。</li>
      </ul>
    </section>

    <section class="section" aria-labelledby="version-record-heading">
      <h2 id="version-record-heading">版本记录</h2>
      <p class="lead" id="version-record-desc">
        当前为 V1 初始版本，以下为候选官方来源记录。每条记录呈现顺序统一为
        "官方来源 → LawGuard 解释 → 辅助说明"：先展示官方来源名称、链接、版本与最后核验日期，
        再展示 LawGuard 的说明文字，最后展示辅助提示。链接、版本与核验日期在完成人工核验前
        均标注为"待核验"，不作为已核验的法律条文引用。
      </p>
      <div
        class="grid grid-2 source-list"
        role="list"
        aria-describedby="version-record-desc"
      >
        <SourceCitationCard
          v-for="source in legalSources"
          :key="source.id"
          role="listitem"
          :source-name="source.title"
          :source-ref="source.url"
          :version="source.version"
          :verified-date="source.lastVerifiedDate"
          :status="source.status"
        >
          <h4 class="sr-only">LawGuard 解释</h4>
          <p class="source-explanation">{{ source.explanation }}</p>
          <h4 class="sr-only">辅助说明</h4>
          <p class="source-note">{{ source.note }}</p>
        </SourceCitationCard>
      </div>
    </section>

    <PrintFooter />
  </div>
</template>

<style scoped>
.lead {
  color: var(--color-text-muted);
  max-width: 640px;
  margin-bottom: var(--space-5);
}

.source-explanation {
  margin: 0 0 var(--space-2);
}

.source-note {
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-label);
}

/* 仅供屏幕阅读器识别的辅助小标题，视觉上不可见 */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* 平板（>= 640px）：来源卡片列表间距略微放宽 */
@media (min-width: 640px) {
  .source-list {
    gap: var(--space-5);
  }
}

/* 桌面端（>= 960px）：来源卡片列表间距进一步放宽，呼应卡片内边距的增加 */
@media (min-width: 960px) {
  .source-list {
    gap: var(--space-6);
  }
}
</style>
