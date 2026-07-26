<script setup lang="ts">
import HeroSection from '../components/HeroSection.vue'
import QuickNavCard from '../components/QuickNavCard.vue'
import StageCard from '../components/StageCard.vue'
import ChannelCard from '../components/ChannelCard.vue'
import NoticeBanner from '../components/NoticeBanner.vue'
import LegalDisclaimer from '../components/LegalDisclaimer.vue'
import TrustBanner from '../components/TrustBanner.vue'
import SharePanel from '../components/SharePanel.vue'
import PrintPageButton from '../components/PrintPageButton.vue'
import AppCard from '../components/AppCard.vue'
import AppButton from '../components/AppButton.vue'
import InteractiveNavigator from '../components/InteractiveNavigator.vue'
import { stages } from '../data/stages'
import { useJsonLd } from '../composables/useJsonLd'
import { getSiteUrl } from '../utils/seo'
import { ref } from 'vue'

const siteUrl = getSiteUrl()
/** 是否展开首页互动导航工具（问答式入口，见 InteractiveNavigator） */
const showNavigator = ref(false)
useJsonLd({
  '@context': 'https://schema.org',
  '@type': 'WebSite',
  name: 'LawGuard',
  alternateName: '法护',
  ...(siteUrl ? { url: siteUrl } : {}),
  description:
    '面向刑事案件当事人及家属的纯公益应急导航平台，提供基于官方法律依据的程序导航、权利指引、文书核对和官方救济渠道。',
  inLanguage: 'zh-CN',
  isAccessibleForFree: true,
})

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

/** "为什么可以放心使用"：短标签 + 一句说明，替代原先图标卡片网格。 */
const trustPoints = [
  {
    title: '官方法律来源',
    description: '内容对应官方公开法律文本，标注来源与核验状态。',
  },
  {
    title: '内容标注核验日期',
    description: '每条内容记录最后核验日期，未核验内容明确标注。',
  },
  {
    title: '不收集个人信息',
    description: '不要求注册，不收集身份证、手机号等个人信息。',
  },
  {
    title: '不提供个案法律意见',
    description: '仅提供一般性程序信息，具体案件请咨询执业律师。',
  },
]
</script>

<template>
  <div>
    <div class="container home-print-slot no-print">
      <PrintPageButton page-title="法护 LawGuard - 刑事案件公益应急导航" />
    </div>

    <div class="container trust-banner-slot">
      <TrustBanner variant="full" />
    </div>

    <HeroSection />

    <section class="section" aria-labelledby="quick-nav-heading">
      <div class="container">
        <h2 id="quick-nav-heading">现在，你可能需要做这些事</h2>
        <QuickNavCard heading-id="quick-nav-heading" />
      </div>
    </section>

    <section class="section" aria-labelledby="navigator-heading">
      <div class="container">
        <h2 id="navigator-heading">不确定现在处于哪个阶段？</h2>
        <p class="section__lead">
          回答一个简单问题，快速定位到对应阶段的说明和权利指引入口，仅作为入口参考，不构成对具体案件的判断。
        </p>

        <AppCard v-if="!showNavigator" interactive class="navigator-entry">
          <div class="navigator-entry__body">
            <div class="navigator-entry__text">
              <h3 class="navigator-entry__title">互动导航工具</h3>
              <p class="navigator-entry__desc">选择当前最符合的情况，快速跳转到对应内容。</p>
            </div>
            <AppButton aria-label="开始互动导航，选择当前所处情况" @click="showNavigator = true">
              开始互动导航
            </AppButton>
          </div>
        </AppCard>

        <InteractiveNavigator v-else @close="showNavigator = false" />

        <AppCard class="navigator-entry navigator-entry--page">
          <div class="navigator-entry__body">
            <div class="navigator-entry__text">
              <h3 class="navigator-entry__title">交互式个人处境导航工具入口</h3>
              <p class="navigator-entry__desc">
                打开独立的分步引导页面，结合诉讼阶段与权利指引静态数据查看更完整的对照速览。
              </p>
            </div>
            <RouterLink
              to="/interactive-navigator"
              class="btn btn-secondary"
              aria-label="进入交互式个人处境导航工具独立页面"
            >
              进入导航工具页面
            </RouterLink>
          </div>
        </AppCard>
      </div>
    </section>

    <section class="section section-alt">
      <div class="container">
        <h2>怎么用</h2>
        <div class="steprow">
          <div v-for="step in familySteps" :key="step.title" class="stepitem">
            <span class="stepitem__num" aria-hidden="true">{{ step.index }}</span>
            <div>
              <p class="stepitem__title">{{ step.title }}</p>
              <p class="stepitem__desc">{{ step.description }}</p>
            </div>
          </div>
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
        <h2>为什么可以放心使用</h2>
        <div class="trustrow">
          <div v-for="point in trustPoints" :key="point.title" class="trustchip">
            <span class="trustchip__title">{{ point.title }}</span>
            <span class="trustchip__desc">{{ point.description }}</span>
          </div>
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

    <section class="section section-alt boundary-section">
      <div class="container boundary">
        <div class="boundary__intro">
          <h2>使用边界</h2>
          <p class="boundary__lead">帮助您正确理解本平台能提供什么、<span class="text-keep">不能提供什么</span>。</p>
        </div>
        <div class="boundary__content">
          <LegalDisclaimer expanded />
        </div>
      </div>
    </section>

    <section class="section share-section">
      <div class="container">
        <SharePanel variant="compact" />
      </div>
    </section>
  </div>
</template>

<style scoped>
.home-print-slot {
  display: flex;
  justify-content: flex-end;
  padding-top: var(--space-4);
}

.trust-banner-slot {
  padding-top: var(--space-4);
}

.share-section {
  padding-top: var(--space-6);
  padding-bottom: var(--space-8);
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

/* 互动导航入口卡片：折叠态展示，点击后替换为 InteractiveNavigator */
.navigator-entry__body {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--space-4);
}

.navigator-entry__title {
  margin: 0 0 var(--space-1);
  font-size: var(--font-size-block-title);
  color: var(--color-primary-dark);
}

.navigator-entry__desc {
  margin: 0;
  font-size: var(--font-size-caption);
  color: var(--color-text-muted);
}

@media (min-width: 640px) {
  .navigator-entry__body {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }
}

.navigator-entry--page {
  margin-top: var(--space-4);
}

/* 使用步骤：横向带状条，顶部色条 + 编号，替代原先三张等权卡片 */
.steprow {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  margin-bottom: var(--space-5);
}

.stepitem {
  display: flex;
  gap: var(--space-3);
  padding-top: var(--space-4);
  border-top: 3px solid var(--color-action);
}

.stepitem__num {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: var(--color-action);
  color: var(--color-text-inverse);
  font-size: 13px;
  font-weight: 700;
}

.stepitem__title {
  margin: 0 0 4px;
  font-size: 16px;
  font-weight: 700;
  color: var(--color-primary-dark);
}

.stepitem__desc {
  margin: 0;
  font-size: 14px;
  color: var(--color-text-muted);
}

.family-step__notice {
  margin-top: var(--space-5);
}

/* 信任点：标签 + 说明文字，替代原先图标卡片网格，减少"处处是卡片"的观感；
   用 grid 而非 flex-wrap，避免不同长度的说明文字撑出参差不齐的行高。 */
.trustrow {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-3);
}

@media (min-width: 640px) {
  .trustrow {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 960px) {
  .trustrow {
    grid-template-columns: repeat(4, 1fr);
  }
}

.trustchip {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius);
  background: var(--color-surface-alt);
  border: 1px solid var(--color-border);
}

.trustchip__title {
  font-size: 14.5px;
  font-weight: 700;
  color: var(--color-primary-dark);
}

.trustchip__desc {
  font-size: 13px;
  color: var(--color-text-muted);
}

@media (min-width: 960px) {
  .steprow {
    flex-direction: row;
  }

  .stepitem {
    flex: 1;
  }
}

.boundary-section {
  padding-top: var(--space-8);
  padding-bottom: var(--space-8);
}

.boundary {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.boundary__intro h2 {
  margin-bottom: var(--space-2);
}

.boundary__lead {
  margin: 0;
  color: var(--color-text-muted);
  font-size: 14px;
}

.boundary__content {
  flex: 1 1 auto;
}

@media (min-width: 960px) {
  .boundary {
    flex-direction: row;
    gap: var(--space-8);
  }

  .boundary__intro {
    flex: 0 0 280px;
  }

  .boundary__content {
    flex: 1 1 auto;
  }
}
</style>
