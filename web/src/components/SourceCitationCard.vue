<script setup lang="ts">
import StatusBadge, { type StatusKind } from './StatusBadge.vue'

/**
 * 法律来源引用卡片：统一展示"官方来源 → 版本/施行状态 → 最后核验日期 → 核验状态"，
 * 用于满足 LAWGUARD_SOT.md P0.4 / P1 对法律内容页面的记录与呈现要求。
 * 不得在页面里用自由文本段落代替本组件展示法律来源信息。
 */
withDefaults(
  defineProps<{
    /** 官方来源名称，例如"中华人民共和国刑事诉讼法" */
    sourceName: string
    /** 官方来源地址或项目内来源标识；未核验前可留空 */
    sourceRef?: string
    /** 法律版本或施行状态，例如"2018 年修正" */
    version?: string
    /** 最后核验日期，例如"2026-07-26"；尚未核验时留空 */
    verifiedDate?: string
    /** 核验状态徽标 */
    status?: StatusKind
  }>(),
  {
    sourceRef: '',
    version: '',
    verifiedDate: '',
    status: 'pending',
  }
)
</script>

<template>
  <div class="source-card card">
    <div class="source-card__head">
      <h3 class="source-card__name">{{ sourceName }}</h3>
      <StatusBadge :status="status" />
    </div>
    <dl class="source-card__meta">
      <div class="source-card__row">
        <dt>官方来源</dt>
        <dd>{{ sourceRef || '待补充' }}</dd>
      </div>
      <div class="source-card__row">
        <dt>法律版本 / 施行状态</dt>
        <dd>{{ version || '待补充' }}</dd>
      </div>
      <div class="source-card__row">
        <dt>最后核验日期</dt>
        <dd>{{ verifiedDate || '尚未核验' }}</dd>
      </div>
    </dl>
    <div class="source-card__body">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.source-card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
  margin-bottom: var(--space-3);
}

.source-card__name {
  margin: 0;
  font-size: var(--font-size-block-title);
}

.source-card__meta {
  margin: 0 0 var(--space-3);
  display: grid;
  gap: var(--space-1);
}

.source-card__row {
  display: flex;
  justify-content: space-between;
  gap: var(--space-3);
  font-size: var(--font-size-caption);
  border-bottom: 1px dashed var(--color-border);
  padding-bottom: var(--space-1);
}

.source-card__row dt {
  color: var(--color-text-muted);
}

.source-card__row dd {
  margin: 0;
  color: var(--color-text);
  text-align: right;
}

.source-card__body {
  font-size: var(--font-size-caption);
  color: var(--color-text-muted);
}

.source-card__body:empty {
  display: none;
}
</style>
