<script setup lang="ts">
/**
 * 首页"你现在需要什么？"任务入口区块（方案 A · 可信公益型）：
 * 4 个等权重的任务卡片，不做优先级高亮，保持平和、克制的基调。
 * 响应式列数复用全局 .grid / .grid-2 / .grid-4（见 style.css）。
 */
interface QuickNavItem {
  title: string
  description: string
  actionLabel: string
  to: string
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
    description: '快速了解最先需要确认的事情，按案件阶段获取一份行动清单。',
    actionLabel: '查看紧急指引',
    to: '/emergency-guide',
  },
  {
    title: '已收到法律文书',
    description: '核对文书名称、机关和关键时间。',
    actionLabel: '开始文书核对',
    to: '/documents',
  },
  {
    title: '想了解当前权利',
    description: '按案件阶段查看一般性权利和程序。',
    actionLabel: '查看权利指引',
    to: '/rights-guide',
  },
  {
    title: '需要寻找官方渠道',
    description: '查询法律援助、司法机关和官方公开入口。',
    actionLabel: '查看官方渠道',
    to: '/official-channels',
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
        :aria-label="item.title"
      >
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

.quick-nav__title {
  margin: 0 0 var(--space-2);
  font-size: var(--font-size-block-title);
  color: var(--color-primary-dark);
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
  color: var(--color-action);
}
</style>
