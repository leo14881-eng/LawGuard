<script setup lang="ts">
/**
 * 首页快速导航区块：提供指向官方渠道、法律依据、诉讼阶段三大入口的快捷链接。
 * 响应式列数复用全局 .grid / .grid-2 / .grid-3（见 style.css，640px/960px 断点），
 * 间距、圆角、聚焦态样式统一复用 style.css 中的设计令牌与 .card--interactive，
 * 不新增独立断点数值。
 */
interface QuickNavItem {
  title: string
  description: string
  to: string
  /** 完整无障碍标签：因链接设置了 aria-label，会覆盖卡片内可见文字，
   *  因此需在此包含标题与说明，避免屏幕阅读器用户丢失卡片描述信息。 */
  ariaLabel: string
}

withDefaults(
  defineProps<{
    /** 首页对应区块标题的 id，用于将本组件的 nav 地标与可见标题关联（aria-labelledby） */
    headingId?: string
  }>(),
  { headingId: undefined }
)

const items: QuickNavItem[] = [
  {
    title: '官方渠道',
    description: '公共法律服务热线、检察服务中心等官方救济渠道入口。',
    to: '/official-channels',
    ariaLabel: '前往官方渠道页面：公共法律服务热线、检察服务中心等官方救济渠道入口',
  },
  {
    title: '法律依据',
    description: '内容对应的法律依据来源与版本记录，未复核内容明确标注。',
    to: '/legal-sources',
    ariaLabel: '前往法律依据页面：内容对应的法律依据来源与版本记录，未复核内容明确标注',
  },
  {
    title: '诉讼阶段',
    description: '按刑事诉讼阶段查看一般性法定权利常识指引。',
    to: '/stages',
    ariaLabel: '前往诉讼阶段页面：按刑事诉讼阶段查看一般性法定权利常识指引',
  },
]
</script>

<template>
  <nav
    class="quick-nav"
    :aria-label="headingId ? undefined : '首页快速导航'"
    :aria-labelledby="headingId"
  >
    <div class="grid grid-2 grid-3">
      <RouterLink
        v-for="item in items"
        :key="item.to"
        :to="item.to"
        class="quick-nav__item card card--interactive"
        :aria-label="item.ariaLabel"
      >
        <h3 class="quick-nav__title">{{ item.title }}</h3>
        <p class="quick-nav__desc">{{ item.description }}</p>
        <span class="quick-nav__link" aria-hidden="true">进入 →</span>
      </RouterLink>
    </div>
  </nav>
</template>

<style scoped>
.quick-nav__item {
  display: flex;
  flex-direction: column;
  text-decoration: none;
  color: inherit;
}

.quick-nav__title {
  margin: 0 0 var(--space-2);
  font-size: var(--font-size-block-title);
}

.quick-nav__desc {
  font-size: var(--font-size-caption);
  color: var(--color-text-muted);
  margin-bottom: var(--space-4);
  flex-grow: 1;
}

.quick-nav__link {
  font-size: var(--font-size-caption);
  font-weight: 600;
  color: var(--color-primary);
}
</style>
