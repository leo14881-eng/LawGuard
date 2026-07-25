<script setup lang="ts">
import PageHeader from '../components/PageHeader.vue'
import LegalDisclaimer from '../components/LegalDisclaimer.vue'
import SourceCitationCard from '../components/SourceCitationCard.vue'
import { legalSources } from '../data/legal_sources'
</script>

<template>
  <div class="container section">
    <PageHeader
      title="法律来源与版本记录"
      description="本页面记录法护内容对应的法律依据来源、版本与核验状态，未完成核验的内容不会标注为已核验。"
    />

    <LegalDisclaimer />

    <section class="section">
      <h2>内容依据原则</h2>
      <ul>
        <li>所有正式法律内容必须来自可核验的公开正式文本；</li>
        <li>不得仅凭模型记忆作为发布依据；</li>
        <li>未经执业律师审核前，统一标注为"待法律复核"。</li>
      </ul>
    </section>

    <section class="section">
      <h2>版本记录</h2>
      <p class="lead">
        当前为 V1 初始版本，以下为候选官方来源记录。每条记录呈现顺序统一为
        "官方来源 → LawGuard 解释 → 辅助说明"：先展示官方来源名称、链接、版本与最后核验日期，
        再展示 LawGuard 的说明文字，最后展示辅助提示。链接、版本与核验日期在完成人工核验前
        均标注为"待核验"，不作为已核验的法律条文引用。
      </p>
      <div class="grid grid-2">
        <SourceCitationCard
          v-for="source in legalSources"
          :key="source.id"
          :source-name="source.title"
          :source-ref="source.url"
          :version="source.version"
          :verified-date="source.lastVerifiedDate"
          :status="source.status"
        >
          <p class="source-explanation">{{ source.explanation }}</p>
          <p class="source-note">{{ source.note }}</p>
        </SourceCitationCard>
      </div>
    </section>
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
</style>
