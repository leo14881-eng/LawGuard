<script setup lang="ts">
/**
 * 权利指引列表页：说明"不同诉讼阶段一般享有哪些合法权利"，与「诉讼阶段」
 * 模块（说明"案件现在走到哪个程序环节"）完全独立维护，不共用同一页面。
 */
import RightsGuideCard from '../components/RightsGuideCard.vue'
import PageHeader from '../components/PageHeader.vue'
import PrintPageButton from '../components/PrintPageButton.vue'
import PrintFooter from '../components/PrintFooter.vue'
import TrustBanner from '../components/TrustBanner.vue'
import SharePanel from '../components/SharePanel.vue'
import { rightsGuide } from '../data/rightsGuide'
</script>

<template>
  <div class="container section">
    <TrustBanner variant="print" />

    <PageHeader
      title="权利指引"
      description="按诉讼阶段说明当事人一般享有哪些合法权利，帮助家属了解可以关注的权利要点。若想了解案件现在处于哪个程序环节，请查看「诉讼阶段」页面。"
    >
      <template #actions>
        <PrintPageButton page-title="权利指引 - 法护 LawGuard" />
      </template>
    </PageHeader>

    <SharePanel variant="compact" class="no-print" />

    <TrustBanner variant="compact" />

    <p class="status-note">以下权利说明为一般性表述，尚未经过执业律师逐条核验，统一标注"待法律复核"。</p>

    <div class="grid grid-3 rights-grid">
      <RightsGuideCard v-for="entry in rightsGuide" :key="entry.id" :entry="entry" />
    </div>

    <PrintFooter />
  </div>
</template>

<style scoped>
.rights-grid {
  margin-top: var(--space-6);
}
</style>
