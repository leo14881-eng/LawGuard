<script setup lang="ts">
import type { Stage } from '../data/stages'

defineProps<{
  stage: Stage
}>()
</script>

<template>
  <RouterLink to="/coming-soon" class="stage-card card card--interactive">
    <span class="stage-card__index">{{ stage.order }}</span>
    <h3 class="stage-card__name">{{ stage.name }}</h3>
    <p class="stage-card__summary">{{ stage.summary }}</p>
    <span class="stage-card__link">查看本阶段指引 →</span>
  </RouterLink>
</template>

<style scoped>
/* hover/focus 边框与阴影反馈统一由全局 .card--interactive 提供（见 style.css），
   本组件不再自行重复定义 transition/hover 规则。 */
.stage-card {
  display: flex;
  flex-direction: column;
  text-decoration: none;
  color: inherit;
}

.stage-card__index {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--color-primary);
  color: var(--color-text-inverse);
  font-size: var(--font-size-label);
  font-weight: 700;
  margin-bottom: var(--space-3);
}

.stage-card__name {
  margin: 0 0 var(--space-2);
  font-size: var(--font-size-block-title);
}

.stage-card__summary {
  font-size: var(--font-size-caption);
  color: var(--color-text-muted);
  margin-bottom: var(--space-4);
  flex-grow: 1;
}

.stage-card__link {
  font-size: var(--font-size-caption);
  font-weight: 600;
  color: var(--color-primary);
}
</style>
