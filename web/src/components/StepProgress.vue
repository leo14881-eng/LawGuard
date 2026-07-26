<script setup lang="ts">
/**
 * 通用步骤进度指示器："第 X 步，共 N 步"，用于多步引导流程。
 * 纯展示组件，不持有步骤状态，样式复用 Design Tokens。
 */
defineProps<{
  current: number
  total: number
  /** 当前步骤标题，用于屏幕阅读器与可见文案 */
  label: string
}>()
</script>

<template>
  <div class="step-progress" role="status">
    <p class="step-progress__meta">第 {{ current }} 步，共 {{ total }} 步</p>
    <h2 class="step-progress__label">{{ label }}</h2>
    <div class="step-progress__bar" aria-hidden="true">
      <span
        v-for="index in total"
        :key="index"
        class="step-progress__segment"
        :class="{ 'step-progress__segment--done': index <= current }"
      />
    </div>
  </div>
</template>

<style scoped>
.step-progress__meta {
  margin: 0 0 var(--space-1);
  font-size: var(--font-size-label);
  font-weight: 600;
  color: var(--color-primary);
}

.step-progress__label {
  margin-bottom: var(--space-3);
}

.step-progress__bar {
  display: flex;
  gap: var(--space-2);
  margin-bottom: var(--space-5);
}

.step-progress__segment {
  flex: 1;
  height: 4px;
  border-radius: var(--radius-pill);
  background: var(--color-border);
}

.step-progress__segment--done {
  background: var(--color-primary);
}
</style>
