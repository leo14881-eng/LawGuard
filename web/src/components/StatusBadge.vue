<script setup lang="ts">
/**
 * 统一状态徽标：用于展示内容核验/审核状态。
 * 覆盖法护全站涉及法律内容审核流程的全部语义状态，
 * 页面不得再各自用 <span class="badge"> 拼写不同文案与颜色。
 */
export type StatusKind =
  | 'verified' // 已核验
  | 'pending' // 待核验 / 待法律复核
  | 'expired' // 已过期
  | 'pending-review' // 待人工审核
  | 'blocked' // BLOCKED
  | 'missing-source' // 来源缺失

const STATUS_LABELS: Record<StatusKind, string> = {
  verified: '已核验',
  pending: '待核验',
  expired: '已过期',
  'pending-review': '待人工审核',
  blocked: 'BLOCKED',
  'missing-source': '来源缺失',
}

// 语义状态到颜色 tone 的映射，颜色本身来自 style.css 中的 Design Tokens。
const STATUS_TONE: Record<StatusKind, 'success' | 'warning' | 'error' | 'info'> = {
  verified: 'success',
  pending: 'warning',
  expired: 'error',
  'pending-review': 'warning',
  blocked: 'error',
  'missing-source': 'error',
}

const props = withDefaults(
  defineProps<{
    status: StatusKind
    /** 自定义展示文案，留空时使用内置中文文案 */
    label?: string
  }>(),
  { label: '' }
)

const displayLabel = props.label || STATUS_LABELS[props.status]
const tone = STATUS_TONE[props.status]
</script>

<template>
  <span class="status-badge" :class="`status-badge--${tone}`">{{ displayLabel }}</span>
</template>

<style scoped>
.status-badge {
  display: inline-block;
  font-size: var(--font-size-label);
  font-weight: 600;
  padding: 3px 10px;
  border-radius: var(--radius-pill);
  white-space: nowrap;
  border: 1px solid transparent;
}

.status-badge--success {
  background: var(--color-success-bg);
  border-color: var(--color-success-border);
  color: var(--color-success-text);
}

.status-badge--warning {
  background: var(--color-warning-bg);
  border-color: var(--color-warning-border);
  color: var(--color-warning-text);
}

.status-badge--error {
  background: var(--color-error-bg);
  border-color: var(--color-error-border);
  color: var(--color-error-text);
}

.status-badge--info {
  background: var(--color-info-bg);
  border-color: var(--color-info-border);
  color: var(--color-info-text);
}
</style>
