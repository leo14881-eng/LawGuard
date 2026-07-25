<script setup lang="ts">
// 通用提示说明组件，用于展示"非官方机构""待法律复核"等边界与状态说明
withDefaults(
  defineProps<{
    /** 提示标题，可留空 */
    title?: string
    /** 视觉强调级别：info 为中性提示，caution 为需要注意的边界说明 */
    tone?: 'info' | 'caution'
  }>(),
  {
    title: '',
    tone: 'info',
  }
)
</script>

<template>
  <div class="notice" :class="`notice--${tone}`">
    <p v-if="title" class="notice__title">{{ title }}</p>
    <div class="notice__body">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.notice {
  border-radius: var(--radius);
  padding: 16px 18px;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
}

.notice--caution {
  background: var(--color-notice-bg);
  border-color: var(--color-notice-border);
}

.notice__title {
  margin: 0 0 6px;
  font-weight: 700;
  color: var(--color-primary-dark);
}

.notice--caution .notice__title {
  color: var(--color-notice-text);
}

.notice__body :deep(p) {
  margin: 0 0 6px;
  font-size: 14px;
  color: var(--color-text-muted);
}

.notice__body :deep(p:last-child) {
  margin-bottom: 0;
}
</style>
