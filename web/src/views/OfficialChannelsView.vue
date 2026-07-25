<script setup lang="ts">
import ChannelCard from '../components/ChannelCard.vue'
import NoticeBanner from '../components/NoticeBanner.vue'
</script>

<template>
  <div class="container section">
    <h1>官方救济渠道</h1>
    <p class="lead">
      以下为一般性官方渠道说明与入口占位，具体链接与联系方式在核验前不作为正式官方地址展示。
    </p>

    <NoticeBanner tone="caution" title="链接核验说明">
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
  </div>
</template>

<style scoped>
.lead {
  color: var(--color-text-muted);
  max-width: 640px;
  margin-bottom: 20px;
}

.channels-grid {
  margin-top: 24px;
}
</style>
