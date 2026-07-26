<script setup lang="ts">
import type { RightsGuideEntry } from '../data/rightsGuide'

defineProps<{
  entry: RightsGuideEntry
}>()
</script>

<template>
  <RouterLink :to="`/rights-guide/${entry.id}`" class="rights-card card card--interactive">
    <span class="rights-card__index">{{ entry.order }}</span>
    <h3 class="rights-card__title">{{ entry.title }}</h3>
    <p class="rights-card__summary">{{ entry.summary }}</p>
    <span class="rights-card__link">查看权利要点 →</span>
  </RouterLink>
</template>

<style scoped>
/* hover/focus 边框与阴影反馈统一由全局 .card--interactive 提供，本组件不再重复定义。 */
.rights-card {
  display: flex;
  flex-direction: column;
  text-decoration: none;
  color: inherit;
}

.rights-card__index {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--color-trust);
  color: var(--color-text-inverse);
  font-size: var(--font-size-label);
  font-weight: 700;
  margin-bottom: var(--space-3);
}

.rights-card__title {
  margin: 0 0 var(--space-2);
  font-size: var(--font-size-block-title);
}

.rights-card__summary {
  font-size: var(--font-size-caption);
  color: var(--color-text-muted);
  margin-bottom: var(--space-4);
  flex-grow: 1;
}

.rights-card__link {
  font-size: var(--font-size-caption);
  font-weight: 600;
  color: var(--color-primary);
}
</style>
