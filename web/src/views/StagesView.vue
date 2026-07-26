<script setup lang="ts">
import StageCard from '../components/StageCard.vue'
import PageHeader from '../components/PageHeader.vue'
import PrintPageButton from '../components/PrintPageButton.vue'
import PrintFooter from '../components/PrintFooter.vue'
import TrustBanner from '../components/TrustBanner.vue'
import SharePanel from '../components/SharePanel.vue'
import { stages } from '../data/stages'
</script>

<template>
  <div class="container section">
    <TrustBanner variant="print" />

    <PageHeader
      title="刑事诉讼阶段导航"
      description="以下六个阶段仅为页面信息分类，用于组织通俗普法内容，不代表对任何具体案件的程序状态作出判断。"
    >
      <template #actions>
        <PrintPageButton page-title="刑事诉讼阶段导航 - 法护 LawGuard" />
      </template>
    </PageHeader>

    <SharePanel variant="compact" class="no-print" />

    <TrustBanner variant="compact" />

    <p class="status-note">各阶段详情为一般性表述，尚未经过执业律师逐条核验，统一标注"待法律复核"。</p>

    <div class="grid grid-3 stages-grid">
      <StageCard v-for="stage in stages" :key="stage.id" :stage="stage" />
    </div>

    <PrintFooter />
  </div>
</template>

<style scoped>
.stages-grid {
  margin-top: var(--space-6);
}
</style>
