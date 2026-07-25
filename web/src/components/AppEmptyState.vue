<script setup lang="ts">
/**
 * 统一空状态展示，用于列表/搜索结果为空等场景（例如未来的本地全文搜索功能）。
 * 禁止在没有数据时直接留白或不做任何提示。
 */
withDefaults(
  defineProps<{
    title?: string
    description?: string
  }>(),
  {
    title: '暂无内容',
    description: '',
  }
)
</script>

<template>
  <div class="empty-state">
    <p class="empty-state__title">{{ title }}</p>
    <p v-if="description" class="empty-state__desc">{{ description }}</p>
    <div v-if="$slots.default" class="empty-state__extra">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.empty-state {
  text-align: center;
  padding: var(--space-10) var(--space-4);
  color: var(--color-text-muted);
}

.empty-state__title {
  font-size: var(--font-size-block-title);
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: var(--space-2);
}

.empty-state__desc {
  font-size: var(--font-size-caption);
  margin: 0 auto;
  max-width: 420px;
}

.empty-state__extra {
  margin-top: var(--space-4);
}
</style>
