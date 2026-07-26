<script setup lang="ts">
/**
 * 首页快速导航区块：提供指向官方渠道、法律依据、诉讼阶段三大入口的快捷链接。
 * 响应式列数复用全局 .grid / .grid-2 / .grid-3（见 style.css，640px/960px 断点），
 * 间距、圆角、聚焦态样式统一复用 style.css 中的设计令牌与 .card--interactive，
 * 不新增独立断点数值。图标为内联 SVG（不引入图标字体/第三方库），
 * 颜色跟随 currentColor，与卡片文字色保持一致。
 */
interface QuickNavItem {
  title: string
  description: string
  to: string
  /** 内联 SVG 图标的 path 数据，均为 24x24 视图下的线性图标 */
  iconPath: string
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
    iconPath: 'M12 3l7 3.2v5.3c0 4.8-3.1 7.9-7 9.5-3.9-1.6-7-4.7-7-9.5V6.2L12 3z',
    ariaLabel: '前往官方渠道页面：公共法律服务热线、检察服务中心等官方救济渠道入口',
  },
  {
    title: '法律依据',
    description: '内容对应的法律依据来源与版本记录，未复核内容明确标注。',
    to: '/legal-sources',
    iconPath:
      'M4 5.8C4 4.8 4.8 4 5.8 4H11v16H5.8A1.8 1.8 0 0 1 4 18.2V5.8zM20 5.8c0-1-.8-1.8-1.8-1.8H13v16h5.2a1.8 1.8 0 0 0 1.8-1.8V5.8z',
    ariaLabel: '前往法律依据页面：内容对应的法律依据来源与版本记录，未复核内容明确标注',
  },
  {
    title: '诉讼阶段',
    description: '按刑事诉讼阶段查看一般性法定权利常识指引。',
    to: '/stages',
    iconPath: 'M4.5 19.5v-5M10.5 19.5v-9M16.5 19.5V5.5M4.5 14.5h6M10.5 10.5h6',
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
        <svg class="quick-nav__icon" viewBox="0 0 24 24" aria-hidden="true">
          <path
            :d="item.iconPath"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
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
  /* 在全局 .card--interactive 的 border/shadow 过渡基础上，
     补充首页专属的轻微上浮动效，仅作用于本组件，不影响其它页面的卡片。 */
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
}

.quick-nav__item:hover,
.quick-nav__item:focus-visible {
  transform: translateY(-4px);
}

@media (prefers-reduced-motion: reduce) {
  .quick-nav__item:hover,
  .quick-nav__item:focus-visible {
    transform: none;
  }
}

.quick-nav__icon {
  width: 28px;
  height: 28px;
  color: var(--color-primary);
  margin-bottom: var(--space-3);
  flex-shrink: 0;
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
