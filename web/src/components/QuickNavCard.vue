<script setup lang="ts">
/**
 * 首页快速导航区块：提供指向官方渠道、法律依据、诉讼阶段三大入口的快捷链接。
 * 响应式列数复用全局 .grid / .grid-2 / .grid-3（见 style.css），
 * 不新增断点，不引入新样式变量。
 */
interface QuickNavItem {
  title: string
  description: string
  to: string
  ariaLabel: string
}

const items: QuickNavItem[] = [
  {
    title: '官方渠道',
    description: '公共法律服务热线、检察服务中心等官方救济渠道入口。',
    to: '/official-channels',
    ariaLabel: '前往官方渠道页面',
  },
  {
    title: '法律依据',
    description: '内容对应的法律依据来源与版本记录，未复核内容明确标注。',
    to: '/legal-sources',
    ariaLabel: '前往法律依据页面',
  },
  {
    title: '诉讼阶段',
    description: '按刑事诉讼阶段查看一般性法定权利常识指引。',
    to: '/stages',
    ariaLabel: '前往诉讼阶段页面',
  },
]
</script>

<template>
  <nav class="quick-nav" aria-label="首页快速导航">
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

.quick-nav__item:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.quick-nav__title {
  margin: 0 0 8px;
  font-size: 17px;
}

.quick-nav__desc {
  font-size: 14px;
  color: var(--color-text-muted);
  margin-bottom: 16px;
  flex-grow: 1;
}

.quick-nav__link {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-primary);
}
</style>
