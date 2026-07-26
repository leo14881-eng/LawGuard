<script setup lang="ts">
/**
 * 通用折叠面板：用于"法律依据默认折叠，用户可展开"等场景，
 * 不引入新的 UI 框架，键盘可通过 Tab + Enter/Space 操作原生 <button>。
 */
import { ref, useId } from 'vue'

withDefaults(
  defineProps<{
    title: string
    /** 默认是否展开 */
    defaultOpen?: boolean
  }>(),
  { defaultOpen: false }
)

const open = ref(false)
const panelId = `accordion-panel-${useId()}`
</script>

<template>
  <div class="accordion" :class="{ 'accordion--open': open || defaultOpen }">
    <button
      type="button"
      class="accordion__trigger"
      :aria-expanded="open || defaultOpen"
      :aria-controls="panelId"
      @click="open = !open"
    >
      <span>{{ title }}</span>
      <span class="accordion__icon" aria-hidden="true">{{ open || defaultOpen ? '收起 ▲' : '展开 ▼' }}</span>
    </button>
    <div v-show="open || defaultOpen" :id="panelId" class="accordion__panel">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.accordion {
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-bg);
}

.accordion__trigger {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-5);
  background: none;
  border: none;
  cursor: pointer;
  font-size: var(--font-size-block-title);
  font-weight: 700;
  color: var(--color-primary-dark);
  text-align: left;
}

.accordion__trigger:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.accordion__icon {
  font-size: var(--font-size-caption);
  font-weight: 600;
  color: var(--color-primary);
  white-space: nowrap;
}

.accordion__panel {
  padding: 0 var(--space-5) var(--space-5);
}
</style>
