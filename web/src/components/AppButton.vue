<script setup lang="ts">
/**
 * 统一按钮组件：在 .btn 基础样式类之上补充 loading/disabled 的行为与无障碍属性，
 * 覆盖 default/hover/focus/disabled/loading 状态（见 P3.4）。
 * 纯展示型链接按钮请直接使用 <RouterLink class="btn btn-primary">，无需引入本组件。
 */
withDefaults(
  defineProps<{
    variant?: 'primary' | 'secondary'
    type?: 'button' | 'submit'
    disabled?: boolean
    loading?: boolean
  }>(),
  {
    variant: 'primary',
    type: 'button',
    disabled: false,
    loading: false,
  }
)

defineEmits<{ click: [MouseEvent] }>()
</script>

<template>
  <button
    class="btn"
    :class="[`btn-${variant}`, { 'btn--loading': loading }]"
    :type="type"
    :disabled="disabled || loading"
    :aria-busy="loading"
    @click="(event) => $emit('click', event)"
  >
    <span v-if="loading" class="btn__spinner" aria-hidden="true" />
    <slot />
  </button>
</template>

<style scoped>
.btn__spinner {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid currentColor;
  border-top-color: transparent;
  opacity: 0.8;
  animation: btn-spin 0.7s linear infinite;
}

@keyframes btn-spin {
  to {
    transform: rotate(360deg);
  }
}

@media (prefers-reduced-motion: reduce) {
  .btn__spinner {
    animation: none;
  }
}
</style>
