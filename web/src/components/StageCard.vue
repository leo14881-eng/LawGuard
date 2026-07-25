<script setup lang="ts">
import type { Stage } from '../data/stages'

defineProps<{
  stage: Stage
}>()
</script>

<template>
  <RouterLink to="/coming-soon" class="stage-card card">
    <span class="stage-card__index">{{ stage.order }}</span>
    <h3 class="stage-card__name">{{ stage.name }}</h3>
    <p class="stage-card__summary">{{ stage.summary }}</p>
    <span class="stage-card__link">查看本阶段指引 →</span>
  </RouterLink>
</template>

<style scoped>
.stage-card {
  display: flex;
  flex-direction: column;
  text-decoration: none;
  color: inherit;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.stage-card:hover {
  border-color: var(--color-primary-light);
  box-shadow: var(--shadow-sm);
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
  font-size: 13px;
  font-weight: 700;
  margin-bottom: 12px;
}

.stage-card__name {
  margin: 0 0 8px;
  font-size: 17px;
}

.stage-card__summary {
  font-size: 14px;
  color: var(--color-text-muted);
  margin-bottom: 16px;
  flex-grow: 1;
}

.stage-card__link {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-primary);
}
</style>
