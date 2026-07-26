<script setup lang="ts">
import { computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import DetailPageLayout from '../components/DetailPageLayout.vue'
import SourceCitationCard from '../components/SourceCitationCard.vue'
import PageHeader from '../components/PageHeader.vue'
import { getStageById } from '../data/stages'
import { legalSources } from '../data/legal_sources'
import { statusToBadgeKind } from '../utils/statusToBadgeKind'
import { applyPageSeoOverride } from '../utils/seo'

const route = useRoute()
const stage = computed(() => getStageById(String(route.params.id)))
const sources = computed(
  () => stage.value?.legalSourceIds.map((id) => legalSources.find((source) => source.id === id)).filter(Boolean) ?? []
)

/**
 * routeSeoMap 里 stage-detail 只有一条通用兜底文案（同一路由 name 对应 6 个
 * 不同阶段），这里用具体阶段的标题/摘要覆盖，避免 6 个详情页共用一模一样的
 * 搜索结果标题和分享标题。
 */
watch(
  stage,
  (value) => {
    if (!value) return
    applyPageSeoOverride({
      title: `${value.name} - 诉讼阶段详情｜LawGuard`,
      description: value.summary,
    })
  },
  { immediate: true }
)
</script>

<template>
  <div v-if="stage" class="container">
    <DetailPageLayout
      :title="stage.name"
      :summary="stage.summary"
      :print-title="`${stage.name} - 诉讼阶段指引 - 法护 LawGuard`"
      back-to="/stages"
      back-label="返回诉讼阶段列表"
      :status="statusToBadgeKind(stage.status)"
    >
      <template #key-takeaway>
        <p>{{ stage.whatIsThisStage }}</p>
      </template>

      <template #body>
        <div class="detail-group">
          <h3>一般会发生什么</h3>
          <ul class="list">
            <li v-for="item in stage.whatGenerallyHappens" :key="item">{{ item }}</li>
          </ul>
        </div>
        <div class="detail-group">
          <h3>家属通常可以关注什么</h3>
          <ul class="list">
            <li v-for="item in stage.familyFocus" :key="item">{{ item }}</li>
          </ul>
        </div>
        <div class="detail-group">
          <h3>一般性权利</h3>
          <ul class="list">
            <li v-for="item in stage.generalRights" :key="item">{{ item }}</li>
          </ul>
          <p class="detail-group__more">
            完整的权利说明见
            <RouterLink :to="`/rights-guide/${stage.id}`">权利指引 · {{ stage.name }}</RouterLink>
          </p>
        </div>
      </template>

      <template #next-steps>
        <ul class="list">
          <li v-for="item in stage.nextSteps" :key="item">{{ item }}</li>
        </ul>
      </template>

      <template #sources>
        <p class="lead">以下为本页面内容对应的候选官方来源，完成人工核验前统一标注"待核验"。</p>
        <div class="grid sources-grid" role="list">
          <SourceCitationCard
            v-for="source in sources"
            :key="source!.id"
            role="listitem"
            tabindex="0"
            :source-name="source!.title"
            :source-ref="source!.url"
            :version="source!.version"
            :verified-date="source!.lastVerifiedDate"
            :status="source!.status"
          />
        </div>
      </template>
    </DetailPageLayout>
  </div>

  <div v-else class="container section">
    <PageHeader title="未找到该诉讼阶段" description="该阶段可能已被调整，请返回诉讼阶段列表重新选择。" />
    <RouterLink to="/stages" class="btn btn-primary">返回诉讼阶段列表</RouterLink>
  </div>
</template>

<style scoped>
.detail-group {
  margin-bottom: var(--space-5);
}

.detail-group:last-child {
  margin-bottom: 0;
}

.detail-group h3 {
  margin-bottom: var(--space-2);
}

.detail-group__more {
  margin: var(--space-3) 0 0;
  font-size: var(--font-size-caption);
  color: var(--color-text-muted);
}

.list li {
  margin-bottom: var(--space-2);
  color: var(--color-text);
}

.sources-grid {
  margin-top: var(--space-4);
}

@media (min-width: 640px) {
  .sources-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
