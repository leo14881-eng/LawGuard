<script setup lang="ts">
import StageCard from '../components/StageCard.vue'
import NoticeBanner from '../components/NoticeBanner.vue'
import { stages } from '../data/stages'
</script>

<template>
  <div class="container section">
    <h1>刑事诉讼阶段导航</h1>
    <p class="lead">
      以下六个阶段仅为页面信息分类，用于组织通俗普法内容，不代表对任何具体案件的程序状态作出判断。
    </p>

    <NoticeBanner tone="caution" title="内容状态说明">
      <p>各阶段详情内容正在依据公开有效法律文件整理，完成法律复核后陆续开放。</p>
    </NoticeBanner>

    <div class="grid grid-3 stages-grid">
      <StageCard v-for="stage in stages" :key="stage.id" :stage="stage" />
    </div>
  </div>
</template>

<style scoped>
.lead {
  color: var(--color-text-muted);
  max-width: 640px;
  margin-bottom: 20px;
}

.stages-grid {
  margin-top: 24px;
}
</style>
