<script setup lang="ts">
import { computed, ref } from 'vue'
import ChannelCard from '../components/ChannelCard.vue'
import NoticeBanner from '../components/NoticeBanner.vue'
import PageHeader from '../components/PageHeader.vue'
import PrintPageButton from '../components/PrintPageButton.vue'
import SourceCitationCard from '../components/SourceCitationCard.vue'
import TrustBanner from '../components/TrustBanner.vue'
import SharePanel from '../components/SharePanel.vue'
import type { StatusKind } from '../components/StatusBadge.vue'
import { officialChannelsByProvince } from '../data/official_channels'

/** 省份筛选控件的选中值，'all' 表示全国 / 未筛选 */
const selectedProvince = ref<string>('all')

/** 筛选控件选项：固定的"全国（未筛选）"项 + 各省级行政区 */
const provinceOptions = computed(() => [
  { code: 'all', province: '全国（未筛选）' },
  ...officialChannelsByProvince.map(({ code, province }) => ({ code, province })),
])

/**
 * 按 province 字段分组的省级渠道列表。骨架阶段每省仅一条占位记录，
 * 保留分组结构是为了未来同一省份存在多条已核验记录时无需改动模板。
 */
const provinceGroups = computed(() => {
  const source =
    selectedProvince.value === 'all'
      ? officialChannelsByProvince
      : officialChannelsByProvince.filter((entry) => entry.code === selectedProvince.value)

  const groups = new Map<string, typeof officialChannelsByProvince>()
  for (const entry of source) {
    const list = groups.get(entry.province) ?? []
    list.push(entry)
    groups.set(entry.province, list)
  }
  return Array.from(groups.entries()).map(([province, entries]) => ({ province, entries }))
})

/**
 * 官方渠道来源记录条目。
 * 根据 LAWGUARD_SOT.md P0 / P0.3 / P0.7，具体官方链接、版本与最后核验日期
 * 在完成人工核验前不得凭记忆编造或推断，一律固定填写"待核验"占位文案。
 */
interface ChannelSourceRecord {
  /** 记录唯一标识 */
  id: string
  /** 官方渠道名称，需与上方渠道卡片一致 */
  title: string
  /** 官方来源地址；完成链接核验前固定为"待核验" */
  url: string
  /** 版本或公布状态；完成核验前固定为"待核验" */
  version: string
  /** 最后核验日期；完成核验前固定为"待核验" */
  lastVerifiedDate: string
  /** 核验状态徽标 */
  status: StatusKind
}

const channelSources: ChannelSourceRecord[] = [
  {
    id: '12348-hotline',
    title: '12348 公共法律服务热线',
    url: '待核验',
    version: '待核验',
    lastVerifiedDate: '待核验',
    status: 'pending',
  },
  {
    id: '12309-hotline',
    title: '12309 检察服务中心',
    url: '待核验',
    version: '待核验',
    lastVerifiedDate: '待核验',
    status: 'pending',
  },
]
</script>

<template>
  <div class="container section">
    <PageHeader
      title="官方救济渠道"
      description="以下为一般性官方渠道说明与入口占位，具体链接与联系方式在核验前不作为正式官方地址展示。"
    >
      <template #actions>
        <PrintPageButton page-title="官方救济渠道 - 法护 LawGuard" />
      </template>
    </PageHeader>

    <SharePanel variant="compact" />

    <TrustBanner variant="compact" />

    <div class="prose">
      <NoticeBanner tone="info" title="链接核验说明">
        <p>本页面暂不提供未经核验的具体网址或电话跳转链接，避免误导。核验完成后将更新为正式入口。</p>
      </NoticeBanner>

      <div class="grid grid-2 channels-grid">
        <ChannelCard
          name="12348 公共法律服务热线"
          description="全国公共法律服务热线，用于一般性法律咨询与服务引导。"
        />
        <ChannelCard
          name="12309 检察服务中心"
          description="检察机关服务热线与控告申诉渠道，用于反映检察环节相关事项。"
        />
      </div>

      <section>
        <h2>使用说明</h2>
        <p>官方渠道适用于反映诉求、寻求法律咨询或程序性帮助，不能替代执业律师提供的个案法律意见。</p>
      </section>

      <section aria-labelledby="province-query-heading">
        <h2 id="province-query-heading">按省份查询（骨架，待官方数据接入）</h2>
        <p class="lead" id="province-query-desc">
          各省具体机构名称与联系方式尚未取得可核验的官方来源，以下仅提供省份筛选入口与
          统一占位条目，紧急情况请优先拨打上方 12348 或 12309 全国性热线。
        </p>

        <NoticeBanner tone="info" title="省级数据核验说明">
          <p>省级条目均标注"待官方链接核验"，具体机构名称与电话完成人工核验后才会更新为正式内容。</p>
        </NoticeBanner>

        <div class="province-filter">
          <label class="province-filter__label" for="province-filter-select">
            按省份筛选官方求助渠道
          </label>
          <select
            id="province-filter-select"
            v-model="selectedProvince"
            class="province-filter__select"
            aria-describedby="province-query-desc"
          >
            <option v-for="option in provinceOptions" :key="option.code" :value="option.code">
              {{ option.province }}
            </option>
          </select>
        </div>

        <div
          class="province-groups"
          role="list"
          :aria-label="
            selectedProvince === 'all'
              ? '全部省级行政区官方求助渠道占位列表'
              : `${provinceGroups[0]?.province ?? ''}官方求助渠道占位列表`
          "
        >
          <div
            v-for="group in provinceGroups"
            :key="group.province"
            class="province-group"
            role="listitem"
          >
            <h3 class="province-group__title">{{ group.province }}</h3>
            <div class="grid grid-2 channels-grid">
              <ChannelCard
                v-for="entry in group.entries"
                :key="entry.code"
                :name="`${entry.province} · ${entry.name}`"
                :description="entry.contact"
                :verified="entry.verificationStatus === 'verified'"
              />
            </div>
          </div>
        </div>
      </section>

      <section aria-labelledby="channel-source-heading">
        <h2 id="channel-source-heading">来源与版本记录</h2>
        <p class="lead" id="channel-source-desc">
          以下记录本页面官方渠道对应的来源标识、版本与最后核验日期。完成人工核验前，链接、
          版本与核验日期统一标注为"待核验"，不作为已核验的官方地址或联系方式发布。
        </p>
        <div
          class="grid grid-2 channel-source-list"
          role="list"
          aria-describedby="channel-source-desc"
        >
          <SourceCitationCard
            v-for="source in channelSources"
            :key="source.id"
            role="listitem"
            tabindex="0"
            :source-name="source.title"
            :source-ref="source.url"
            :version="source.version"
            :verified-date="source.lastVerifiedDate"
            :status="source.status"
          />
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.province-filter {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  margin: var(--space-4) 0 var(--space-5);
  max-width: 320px;
}

.province-filter__label {
  font-size: var(--font-size-caption);
  font-weight: 600;
  color: var(--color-text);
}

.province-filter__select {
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg);
  color: var(--color-text);
  font-size: var(--font-size-caption);
  cursor: pointer;
}

.province-filter__select:focus-visible {
  outline: 2px solid var(--color-action);
  outline-offset: 2px;
}

.province-groups {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.province-group__title {
  margin: 0 0 var(--space-3);
  font-size: var(--font-size-body);
  color: var(--color-primary-dark);
}

.channel-source-list {
  margin-top: var(--space-4);
}

/* 平板（>= 640px）：来源记录卡片列表间距略微放宽 */
@media (min-width: 640px) {
  .channel-source-list {
    gap: var(--space-5);
  }
}

/* 桌面端（>= 960px）：来源记录卡片列表间距进一步放宽，呼应卡片内边距的增加 */
@media (min-width: 960px) {
  .channel-source-list {
    gap: var(--space-6);
  }
}
</style>
