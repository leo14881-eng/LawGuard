<script setup lang="ts">
import HeroSection from '../components/HeroSection.vue'
import QuickNavCard from '../components/QuickNavCard.vue'
import StageCard from '../components/StageCard.vue'
import ChannelCard from '../components/ChannelCard.vue'
import AppCard from '../components/AppCard.vue'
import NoticeBanner from '../components/NoticeBanner.vue'
import LegalDisclaimer from '../components/LegalDisclaimer.vue'
import TrustBanner from '../components/TrustBanner.vue'
import SharePanel from '../components/SharePanel.vue'
import { stages } from '../data/stages'
import { useJsonLd } from '../composables/useJsonLd'
import { getSiteUrl } from '../utils/seo'

const siteUrl = getSiteUrl()
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

/** "为什么可以放心使用"：小图标 + 标题 + 一句说明，替代原先大面积绿色胶囊标签。 */
const trustPoints = [
  {
    title: '官方法律来源',
    description: '内容对应官方公开法律文本，标注来源与核验状态。',
    iconPath: 'M12 3l7 3.2v5.3c0 4.8-3.1 7.9-7 9.5-3.9-1.6-7-4.7-7-9.5V6.2L12 3z',
  },
  {
    title: '内容标注核验日期',
    description: '每条内容记录最后核验日期，未核验内容明确标注。',
    iconPath: 'M4 6h16M4 6v13a1 1 0 001 1h14a1 1 0 001-1V6M8 3v4M16 3v4',
  },
  {
    title: '不收集个人信息',
    description: '不要求注册，不收集身份证、手机号等个人信息。',
    iconPath: 'M12 3l7 3.2v5.3c0 4.8-3.1 7.9-7 9.5-3.9-1.6-7-4.7-7-9.5V6.2L12 3z M9 12l2 2 4-4',
  },
  {
    title: '不提供个案法律意见',
    description: '仅提供一般性程序信息，具体案件请咨询执业律师。',
    iconPath: 'M12 3.5L2.5 19.5h19L12 3.5z M12 9.5v4 M12 16.3h.01',
  },
]
</script>

<template>
  <div>
    <div class="container trust-banner-slot">
      <TrustBanner variant="full" />
    </div>

    <HeroSection />

    <section class="section share-section">
      <div class="container">
        <SharePanel variant="primary" />
      </div>
    </section>

    <section class="section">
      <div class="container">
        <h2 id="quick-nav-heading">你现在需要什么？</h2>
        <QuickNavCard heading-id="quick-nav-heading" />
      </div>
    </section>

    <section class="section section-alt">
      <div class="container">
        <h2>为什么可以放心使用</h2>
        <div class="grid grid-2 grid-4 trust-points">
          <AppCard v-for="point in trustPoints" :key="point.title" class="trust-point">
            <svg class="trust-point__icon" viewBox="0 0 24 24" aria-hidden="true">
              <path
                :d="point.iconPath"
                fill="none"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
            <h3 class="trust-point__title">{{ point.title }}</h3>
            <p class="trust-point__desc">{{ point.description }}</p>
          </AppCard>
        </div>
      </div>
    </section>

    <section class="section">
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
          <p class="boundary__lead">帮助您正确理解本平台能提供什么、不能提供什么。</p>
        </div>
        <div class="boundary__content">
          <LegalDisclaimer expanded />
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.trust-banner-slot {
  padding-top: var(--space-4);
}

.share-section {
  padding-top: 0;
  padding-bottom: var(--space-6);
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

.trust-points {
  margin-top: var(--space-2);
}

.trust-point__icon {
  width: 26px;
  height: 26px;
  color: var(--color-primary);
  margin-bottom: var(--space-2);
}

.trust-point__title {
  margin: 0 0 6px;
  font-size: 16px;
  color: var(--color-primary-dark);
}

.trust-point__desc {
  margin: 0;
  font-size: 13px;
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
  max-width: 320px;
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
