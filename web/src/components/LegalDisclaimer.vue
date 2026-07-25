<script setup lang="ts">
/**
 * 全站统一的"非法律意见"声明组件（对应 LAWGUARD_SOT.md P-1 最高优先级原则）。
 * 页面不得再各自编写措辞相近但不完全一致的免责文案，必须复用本组件，
 * 保证个案风险提示的文案在全站保持完全一致、清晰醒目，不得用小字隐藏在角落。
 */
withDefaults(
  defineProps<{
    /** 是否展示扩展说明（不属于哪些机构、不做哪些事），默认展示 */
    expanded?: boolean
  }>(),
  { expanded: false }
)
</script>

<template>
  <div class="legal-disclaimer" role="note" aria-label="非法律意见声明">
    <p class="legal-disclaimer__main">
      <strong>LawGuard 不提供个案法律意见。</strong>
      如需法律帮助，请咨询执业律师或当地法律援助机构。
    </p>
    <ul v-if="expanded" class="legal-disclaimer__list">
      <li>不属于政府机关、公安机关、检察院、法院，也不属于律师事务所或法律援助机构；</li>
      <li>不判断具体案件是否合法、是否构成犯罪、是否有罪、可能判处何种刑罚；</li>
      <li>不评价警方、检察院、法院或律师的具体行为、意见是否正确；</li>
      <li>不推荐诉讼策略、辩护方案、举报方案，或任何规避法律责任的方法。</li>
    </ul>
  </div>
</template>

<style scoped>
/* 使用 warning（而非 error）色调：既要清晰醒目，也要符合 P3.3 "克制、不制造恐慌"
   的产品气质，避免大面积红色造成视觉恐慌（见 LAWGUARD_SOT.md UI 设计规范）。 */
.legal-disclaimer {
  border-radius: var(--radius);
  padding: var(--space-4);
  background: var(--color-warning-bg);
  border: 1px solid var(--color-warning-border);
}

.legal-disclaimer__main {
  margin: 0;
  color: var(--color-warning-text);
  font-size: var(--font-size-body);
}

.legal-disclaimer__list {
  margin: var(--space-2) 0 0;
  padding-left: var(--space-5);
  color: var(--color-warning-text);
  font-size: var(--font-size-caption);
}

.legal-disclaimer__list li {
  margin-bottom: var(--space-1);
}
</style>
