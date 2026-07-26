<script setup lang="ts">
/**
 * 首页"你现在需要什么？"任务入口区块：4 个明确的用户场景任务卡（家人刚被带走/
 * 已收到法律文书/想了解当前权利/需要寻找官方渠道），替代原先的通用"快速导航"，
 * 与首页"核心功能"区块合并去重，避免同一批目的地在首页出现两套导航。
 * 响应式列数复用全局 .grid / .grid-2 / .grid-4（见 style.css，640px/960px 断点），
 * 间距、圆角、聚焦态样式统一复用 style.css 中的设计令牌与 .card--interactive，
 * 不新增独立断点数值。图标为内联 SVG（不引入图标字体/第三方库），
 * 颜色跟随 currentColor，与卡片文字色保持一致。
 */
interface QuickNavItem {
  title: string
  description: string
  /** 每张卡片只保留一个明确动作的行动文案，替代原先通用的"进入 →" */
  actionLabel: string
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
    title: '家人刚被带走',
    description: '快速了解最先需要确认的事情。',
    actionLabel: '查看紧急指引',
    to: '/emergency-guide',
    iconPath: 'M12 3.5L2.5 19.5h19L12 3.5z M12 9.5v4 M12 16.3h.01',
    ariaLabel: '前往被羁押后紧急行动指引：快速了解最先需要确认的事情',
  },
  {
    title: '已收到法律文书',
    description: '核对文书名称、机关和关键时间。',
    actionLabel: '开始文书核对',
    to: '/documents',
    iconPath: 'M6 3h8l5 5v13H6z M14 3v5h5',
    ariaLabel: '前往文书核对页面：核对文书名称、机关和关键时间',
  },
  {
    title: '想了解当前权利',
    description: '按案件阶段查看一般性权利和程序。',
    actionLabel: '查看权利指引',
    to: '/stages',
    iconPath: 'M4.5 19.5v-5M10.5 19.5v-9M16.5 19.5V5.5M4.5 14.5h6M10.5 10.5h6',
    ariaLabel: '前往权利指引页面：按案件阶段查看一般性权利和程序',
  },
  {
    title: '需要寻找官方渠道',
    description: '查询法律援助、司法机关和官方公开入口。',
    actionLabel: '查看官方渠道',
    to: '/official-channels',
    iconPath: 'M12 3l7 3.2v5.3c0 4.8-3.1 7.9-7 9.5-3.9-1.6-7-4.7-7-9.5V6.2L12 3z',
    ariaLabel: '前往官方渠道页面：查询法律援助、司法机关和官方公开入口',
  },
]
</script>

<template>
  <nav
    class="quick-nav"
    :aria-label="headingId ? undefined : '首页任务导航'"
    :aria-labelledby="headingId"
  >
    <div class="grid grid-2 grid-4">
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
        <span class="quick-nav__link" aria-hidden="true">{{ item.actionLabel }} →</span>
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
