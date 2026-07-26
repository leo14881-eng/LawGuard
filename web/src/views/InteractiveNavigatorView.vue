<script setup lang="ts">
/**
 * 交互式个人处境导航工具独立页面：复用首页已有的 InteractiveNavigator 组件，
 * 让用户通过分步选择快速定位到当前所处诉讼阶段对应的说明与权利指引入口。
 * 页面本身不新增法律事实，仅结合 stages.ts / rightsGuide.ts 中已核对的静态
 * 数据，在互动工具下方追加一份"阶段与关键权利对照速览"，作为分步引导的
 * 补充演示，不构成对具体案件的判断。
 */
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '../components/PageHeader.vue'
import PrintPageButton from '../components/PrintPageButton.vue'
import PrintFooter from '../components/PrintFooter.vue'
import TrustBanner from '../components/TrustBanner.vue'
import SharePanel from '../components/SharePanel.vue'
import NoticeBanner from '../components/NoticeBanner.vue'
import AppCard from '../components/AppCard.vue'
import InteractiveNavigator from '../components/InteractiveNavigator.vue'
import { stages } from '../data/stages'
import { getRightsGuideById } from '../data/rightsGuide'

const router = useRouter()

/** 组件内点击"返回"时，回到首页而不是留在空白页面 */
function handleClose() {
  router.push('/')
}

/** 结合 stages.ts 与 rightsGuide.ts：按阶段顺序生成"阶段 + 首条关键权利"速览列表 */
const overview = computed(() =>
  stages
    .slice()
    .sort((a, b) => a.order - b.order)
    .map((stage) => ({
      stage,
      rightsEntry: getRightsGuideById(stage.id),
    }))
)
</script>

<template>
  <div class="container section">
    <TrustBanner variant="print" />

    <PageHeader
      title="交互式个人处境导航工具"
      description="回答一个简单问题，快速定位到当前所处诉讼阶段对应的说明与权利指引入口，仅作为入口参考，不对具体案件作出判断。"
    >
      <template #actions>
        <PrintPageButton page-title="交互式个人处境导航工具 - 法护 LawGuard" />
      </template>
    </PageHeader>

    <SharePanel variant="compact" class="no-print" />

    <TrustBanner variant="compact" />

    <NoticeBanner tone="caution" title="使用说明">
      <p>
        本工具仅根据你选择的情况提供内容入口参考，不判断具体案件是否合法、是否构成犯罪，也不提供辩护策略或法律意见。
        具体案件请以官方文书内容和执业律师意见为准。
      </p>
    </NoticeBanner>

    <div class="navigator-slot">
      <InteractiveNavigator @close="handleClose" />
    </div>

    <section class="overview-section" aria-labelledby="overview-heading">
      <h2 id="overview-heading">六个阶段与关键权利速览</h2>
      <p class="overview-lead">
        以下内容对照 stages.ts 与 rightsGuide.ts 中已整理的阶段信息，作为分步引导的补充参考，各条均标注核验状态。
      </p>
      <div class="grid grid-3 overview-grid">
        <AppCard v-for="item in overview" :key="item.stage.id" class="overview-card">
          <p class="overview-card__stage">{{ item.stage.name }}</p>
          <p class="overview-card__summary">{{ item.stage.summary }}</p>
          <p v-if="item.rightsEntry" class="overview-card__right">
            关键权利：{{ item.rightsEntry.keyRights[0] }}
          </p>
          <p class="overview-card__status">
            核验状态：{{ item.rightsEntry ? item.rightsEntry.status : item.stage.status }}
          </p>
          <div class="overview-card__links">
            <RouterLink :to="`/stages/${item.stage.id}`" class="btn btn-secondary">
              查看阶段说明
            </RouterLink>
            <RouterLink :to="`/rights-guide/${item.stage.id}`" class="btn btn-secondary">
              查看权利指引
            </RouterLink>
          </div>
        </AppCard>
      </div>
    </section>

    <PrintFooter />
  </div>
</template>

<style scoped>
.navigator-slot {
  margin: var(--space-6) 0;
}

.overview-section {
  margin-top: var(--space-8);
}

.overview-lead {
  color: var(--color-text-muted);
  font-size: 14px;
  max-width: 640px;
  margin-bottom: var(--space-5);
}

.overview-grid {
  margin-top: var(--space-2);
}

.overview-card {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.overview-card__stage {
  margin: 0;
  font-size: var(--font-size-block-title);
  font-weight: 700;
  color: var(--color-primary-dark);
}

.overview-card__summary {
  margin: 0;
  font-size: 14px;
  color: var(--color-text-muted);
}

.overview-card__right {
  margin: 4px 0 0;
  font-size: 13.5px;
  color: var(--color-text);
}

.overview-card__status {
  margin: 0;
  font-size: 12.5px;
  color: var(--color-text-muted);
}

.overview-card__links {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-top: var(--space-3);
}
</style>
