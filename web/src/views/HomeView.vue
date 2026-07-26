<script setup lang="ts">
import HeroSection from '../components/HeroSection.vue'
import QuickNavCard from '../components/QuickNavCard.vue'
import StageCard from '../components/StageCard.vue'
import FeatureCard from '../components/FeatureCard.vue'
import ChannelCard from '../components/ChannelCard.vue'
import AppCard from '../components/AppCard.vue'
import NoticeBanner from '../components/NoticeBanner.vue'
import LegalDisclaimer from '../components/LegalDisclaimer.vue'
import TrustBanner from '../components/TrustBanner.vue'
import { stages } from '../data/stages'

const familySteps = [
  {
    index: '1',
    title: '确认案件当前阶段',
    description: '根据拘留通知书、逮捕通知书、起诉书、判决书或办案机关告知的信息，判断案件所处阶段。',
  },
  {
    index: '2',
    title: '查看并核对官方信息',
    description: '阅读一般性权利说明、程序期限、法律依据和官方救济渠道。',
  },
  {
    index: '3',
    title: '保存、打印或与律师沟通',
    description: '将相关页面保存或打印，作为与律师、法律援助机构或办案机关沟通时的信息参考。',
  },
]

const whyChoose = [
  { title: '官方法律来源', description: '内容对应官方公开法律文本，标注来源与核验状态。' },
  { title: '持续更新', description: '跟踪法律法规变化，及时标记待复核内容。' },
  { title: '免费公益', description: '完全免费使用，不收费、不收集用户材料。' },
  { title: '权利指引', description: '按诉讼阶段梳理权利要点，通俗易懂。' },
]

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
    <div class="container trust-banner-slot">
      <TrustBanner variant="full" />
    </div>

    <HeroSection />

    <section class="section emergency-cta-section">
      <div class="container">
        <div class="card emergency-cta">
          <h2 class="emergency-cta__title">家人或恋人突然被羁押，我该怎么办？</h2>
          <p class="emergency-cta__desc">
            根据关系和案件状态生成下一步行动清单：当前身份通常能做什么、最应该联系谁、联系不到近亲属时还有哪些合法路径。
          </p>
          <RouterLink to="/emergency-guide" class="btn btn-primary emergency-cta__action">
            开始生成行动指引
          </RouterLink>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="container">
        <h2 id="quick-nav-heading">快速导航</h2>
        <p class="section__lead">常用入口一步直达，方便快速查看官方渠道、法律依据与诉讼阶段。</p>
        <QuickNavCard heading-id="quick-nav-heading" />
      </div>
    </section>

    <section class="section section-alt">
      <div class="container">
        <h2>家属如何使用 LawGuard</h2>
        <div class="grid grid-3">
          <AppCard v-for="step in familySteps" :key="step.title" class="family-step">
            <span class="family-step__index" aria-hidden="true">{{ step.index }}</span>
            <h3 class="family-step__title">{{ step.title }}</h3>
            <p class="family-step__desc">{{ step.description }}</p>
          </AppCard>
        </div>
        <NoticeBanner tone="caution" class="family-step__notice">
          <p>
            被羁押人员通常无法自由访问互联网。家属可以保存或打印相关信息，但是否可以寄送、转交或在会见时使用，
            应以具体监管场所和办案机关的现行规定为准。
          </p>
        </NoticeBanner>
      </div>
    </section>

    <section class="section">
      <div class="container">
        <h2>为什么选择 LawGuard</h2>
        <div class="grid grid-4">
          <AppCard v-for="item in whyChoose" :key="item.title" class="why-choose__item">
            <h3 class="why-choose__title">{{ item.title }}</h3>
            <p class="why-choose__desc">{{ item.description }}</p>
          </AppCard>
        </div>
      </div>
    </section>

    <section class="section section-alt">
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

    <section class="section">
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

    <section class="section section-alt">
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

    <section class="section">
      <div class="container">
        <h2>内容边界说明</h2>
        <LegalDisclaimer expanded />
      </div>
    </section>
  </div>
</template>

<style scoped>
.trust-banner-slot {
  padding-top: var(--space-4);
}

.section__lead {
  color: var(--color-text-muted);
  font-size: 14px;
  margin-bottom: 20px;
  max-width: 640px;
}

.section__more {
  margin-top: 20px;
}

.why-choose__title {
  margin: 0 0 6px;
  font-size: 17px;
  color: var(--color-primary-dark);
}

.emergency-cta-section {
  padding-top: var(--space-6);
  padding-bottom: var(--space-6);
}

.emergency-cta {
  border-left: 4px solid var(--color-primary);
  background: var(--color-surface);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.emergency-cta__title {
  margin: 0;
}

.emergency-cta__desc {
  margin: 0;
  color: var(--color-text-muted);
  max-width: 640px;
}

.emergency-cta__action {
  align-self: flex-start;
}

.why-choose__desc {
  margin: 0;
  font-size: 14px;
  color: var(--color-text-muted);
}

.family-step__index {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--color-primary);
  color: var(--color-text-inverse);
  font-size: 13px;
  font-weight: 700;
  margin-bottom: var(--space-3);
}

.family-step__title {
  margin: 0 0 6px;
  font-size: 17px;
  color: var(--color-primary-dark);
}

.family-step__desc {
  margin: 0;
  font-size: 14px;
  color: var(--color-text-muted);
}

.family-step__notice {
  margin-top: var(--space-5);
}
</style>
