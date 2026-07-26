<script setup lang="ts">
import ChannelCard from '../components/ChannelCard.vue'
import NoticeBanner from '../components/NoticeBanner.vue'
import PageHeader from '../components/PageHeader.vue'
import SourceCitationCard from '../components/SourceCitationCard.vue'
import TrustBanner from '../components/TrustBanner.vue'
import type { StatusKind } from '../components/StatusBadge.vue'

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
    />

    <TrustBanner variant="compact" />

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

    <section class="section">
      <h2>使用说明</h2>
      <p>官方渠道适用于反映诉求、寻求法律咨询或程序性帮助，不能替代执业律师提供的个案法律意见。</p>
    </section>

    <section class="section" aria-labelledby="channel-source-heading">
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
</template>

<style scoped>
.channels-grid {
  margin-top: var(--space-6);
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
