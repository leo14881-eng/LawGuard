<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import DetailPageLayout from '../components/DetailPageLayout.vue'
import SourceCitationCard from '../components/SourceCitationCard.vue'
import PageHeader from '../components/PageHeader.vue'
import { getRightsGuideById } from '../data/rightsGuide'
import { legalSources } from '../data/legal_sources'
import { statusToBadgeKind } from '../utils/statusToBadgeKind'

const route = useRoute()
const entry = computed(() => getRightsGuideById(String(route.params.id)))
const sources = computed(
  () => entry.value?.legalSourceIds.map((id) => legalSources.find((source) => source.id === id)).filter(Boolean) ?? []
)
</script>

<template>
  <div v-if="entry" class="container">
    <DetailPageLayout
      :title="entry.title"
      :summary="entry.summary"
      :print-title="`${entry.title} - 权利指引 - 法护 LawGuard`"
      back-to="/rights-guide"
      back-label="返回权利指引列表"
      :status="statusToBadgeKind(entry.status)"
    >
      <template #key-takeaway>
        <ul class="list">
          <li v-for="item in entry.keyRights" :key="item">{{ item }}</li>
        </ul>
      </template>

      <template #body>
        <div v-for="right in entry.rightsDetail" :key="right.title" class="detail-group">
          <h3>{{ right.title }}</h3>
          <p>{{ right.description }}</p>
        </div>
        <p class="detail-group__more">
          想了解案件目前处于什么程序环节，请查看
          <RouterLink :to="`/stages/${entry.id}`">诉讼阶段 · {{ entry.title.replace('的一般性权利', '') }}</RouterLink>
        </p>
      </template>

      <template #next-steps>
        <ul class="list">
          <li v-for="item in entry.howToExercise" :key="item">{{ item }}</li>
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
    <PageHeader title="未找到该权利指引" description="该条目可能已被调整，请返回权利指引列表重新选择。" />
    <RouterLink to="/rights-guide" class="btn btn-primary">返回权利指引列表</RouterLink>
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
