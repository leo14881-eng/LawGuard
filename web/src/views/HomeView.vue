<script setup lang="ts">
import HeroSection from '../components/HeroSection.vue'
import StageCard from '../components/StageCard.vue'
import FeatureCard from '../components/FeatureCard.vue'
import ChannelCard from '../components/ChannelCard.vue'
import LegalDisclaimer from '../components/LegalDisclaimer.vue'
import { stages } from '../data/stages'

const features = [
  {
    title: '权利知识',
    description: '以通俗语言梳理刑事诉讼各阶段的一般性法定权利常识。',
    to: '/stages',
  },
  {
    title: '文书核对',
    description: '核对笔录与法律文书时可以留意的一般性方法与要点。',
    to: '/documents',
  },
  {
    title: '法律依据',
    description: '内容对应的法律依据来源与版本记录，未复核内容明确标注。',
    to: '/legal-sources',
  },
  {
    title: '官方救济',
    description: '公共法律服务热线、检察服务中心等官方渠道信息。',
    to: '/official-channels',
  },
]
</script>

<template>
  <div>
    <HeroSection />

    <section class="section">
      <div class="container">
        <h2>按刑事诉讼阶段查看指引</h2>
        <p class="section__lead">
          以下阶段划分仅用于组织普法内容，不代表对具体案件程序状态作出判断。
        </p>
        <div class="grid grid-3">
          <StageCard v-for="stage in stages" :key="stage.id" :stage="stage" />
        </div>
      </div>
    </section>

    <section class="section section-alt">
      <div class="container">
        <h2>核心功能</h2>
        <div class="grid grid-4">
          <FeatureCard
            v-for="feature in features"
            :key="feature.title"
            :title="feature.title"
            :description="feature.description"
            :to="feature.to"
          />
        </div>
      </div>
    </section>

    <section class="section">
      <div class="container">
        <h2>官方救济渠道</h2>
        <p class="section__lead">
          遇到紧急或重大事项，建议及时通过官方渠道或执业律师寻求帮助。
        </p>
        <div class="grid grid-2">
          <ChannelCard
            name="12348 公共法律服务热线"
            description="全国公共法律服务热线，可用于一般性法律咨询与服务引导。"
          />
          <ChannelCard
            name="12309 检察服务中心"
            description="检察机关服务热线与控告申诉渠道，可用于反映检察环节相关事项。"
          />
        </div>
        <RouterLink to="/official-channels" class="btn btn-secondary section__more">
          查看全部官方渠道
        </RouterLink>
      </div>
    </section>

    <section class="section section-alt">
      <div class="container">
        <h2>内容边界说明</h2>
        <LegalDisclaimer expanded />
      </div>
    </section>
  </div>
</template>

<style scoped>
.section__lead {
  color: var(--color-text-muted);
  font-size: 14px;
  margin-bottom: 20px;
  max-width: 640px;
}

.section__more {
  margin-top: 20px;
}
</style>
