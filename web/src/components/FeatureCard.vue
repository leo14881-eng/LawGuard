<script setup lang="ts">
defineProps<{
  title: string
  description: string
  to: string
}>()
</script>

<template>
  <RouterLink :to="to" class="feature-card card">
    <h3 class="feature-card__title">{{ title }}</h3>
    <p class="feature-card__desc">{{ description }}</p>
  </RouterLink>
</template>

<style scoped>
.feature-card {
  display: block;
  text-decoration: none;
  color: inherit;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.feature-card:hover {
  border-color: var(--color-primary-light);
  box-shadow: 0 4px 14px rgba(20, 51, 92, 0.08);
}

.feature-card__title {
  margin: 0 0 6px;
  font-size: 17px;
  color: var(--color-primary-dark);
}

.feature-card__desc {
  margin: 0;
  font-size: 14px;
  color: var(--color-text-muted);
}
</style>
