<script setup lang="ts">
/**
 * 统一加载状态：轻量旋转指示器 + 文案，不使用炫技动画（见 P3.3 / P3.8）。
 * 尊重用户的"减少动态效果"系统偏好（prefers-reduced-motion）。
 */
withDefaults(
  defineProps<{
    label?: string
  }>(),
  { label: '加载中…' }
)
</script>

<template>
  <div class="app-loading" role="status" aria-live="polite">
    <span class="app-loading__spinner" aria-hidden="true" />
    <span class="app-loading__label">{{ label }}</span>
  </div>
</template>

<style scoped>
.app-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-8) 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-caption);
}

.app-loading__spinner {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 2px solid var(--color-border);
  border-top-color: var(--color-primary);
  animation: app-loading-spin 0.8s linear infinite;
}

@keyframes app-loading-spin {
  to {
    transform: rotate(360deg);
  }
}

@media (prefers-reduced-motion: reduce) {
  .app-loading__spinner {
    animation: none;
  }
}
</style>
