<script setup lang="ts">
/**
 * 统一页面头部：标题 + 一句话说明 + 可选主操作按钮，
 * 用于替代各页面自行拼写 <h1> + <p> 且样式不一致的写法（见 P3.4）。
 */
withDefaults(
  defineProps<{
    title: string
    /** 一句话说明页面用途，使用通俗语言，不展示开发者术语 */
    description?: string
  }>(),
  { description: '' }
)
</script>

<template>
  <header class="page-header">
    <h1 class="page-header__title">{{ title }}</h1>
    <p v-if="description" class="page-header__desc">{{ description }}</p>
    <div v-if="$slots.actions" class="page-header__actions">
      <slot name="actions" />
    </div>
  </header>
</template>

<style scoped>
.page-header {
  margin-bottom: var(--space-6);
}

.page-header__title {
  margin-bottom: var(--space-2);
}

.page-header__desc {
  color: var(--color-text-muted);
  font-size: var(--font-size-body);
  max-width: 640px;
  margin-bottom: 0;
}

.page-header__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  margin-top: var(--space-4);
}
</style>
