<script setup lang="ts">
import PageHeader from '../components/PageHeader.vue'
import LegalDisclaimer from '../components/LegalDisclaimer.vue'
import SourceCitationCard from '../components/SourceCitationCard.vue'
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
        当前为 V1 初始版本，尚未收录具体法律条文引用。以下条目将在完成法律复核后逐步补充，
        每条记录会展示官方来源、法律版本与最后核验日期。
      </p>
      <SourceCitationCard
        source-name="V1 尚未收录具体法律条文引用"
        status="pending"
      >
        后续版本将在确认可核验的官方来源并完成法律复核后，逐条补充为独立的来源记录卡片。
      </SourceCitationCard>
    </section>
  </div>
</template>

<style scoped>
.lead {
  color: var(--color-text-muted);
  max-width: 640px;
  margin-bottom: var(--space-5);
}
</style>
