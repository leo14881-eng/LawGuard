<script setup lang="ts">
import { computed, useId } from 'vue'
import StatusBadge, { type StatusKind } from './StatusBadge.vue'

/**
 * 法律来源引用卡片：统一展示顺序固定为
 * "官方来源名称/链接 → 法律版本与最后核验日期 → LawGuard 解释 → 辅助说明"，
 * 用于满足 LAWGUARD_SOT.md P0.4 / P1 对法律内容页面的记录与呈现要求。
 * 不得在页面里用自由文本段落代替本组件展示法律来源信息。
 *
 * 组件根元素为 <article>，通过 aria-labelledby 关联标题，便于屏幕阅读器
 * 将卡片识别为独立的信息单元；父组件可通过透传的 role="listitem" 等属性
 * 将多张卡片组织为无障碍列表。
 */
const props = withDefaults(
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

const headingId = `source-card-heading-${useId()}`

/** 仅当官方来源确实是可跳转链接时才渲染为 <a>，避免"待核验"占位文案被误当作可点击链接 */
const isVerifiedLink = computed(() => /^https?:\/\//i.test(props.sourceRef))
</script>

<template>
  <article class="source-card card" :aria-labelledby="headingId">
    <div class="source-card__head">
      <h3 :id="headingId" class="source-card__name">{{ sourceName }}</h3>
      <StatusBadge :status="status" />
    </div>
    <dl class="source-card__meta">
      <div class="source-card__row">
        <dt>官方来源</dt>
        <dd>
          <a
            v-if="isVerifiedLink"
            class="source-card__link"
            :href="sourceRef"
            target="_blank"
            rel="noopener noreferrer"
          >
            {{ sourceRef }}
            <span class="sr-only">（在新窗口打开官方来源链接）</span>
          </a>
          <span v-else>{{ sourceRef || '待补充' }}</span>
        </dd>
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
  </article>
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
  gap: var(--space-2);
}

.source-card__row {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  font-size: var(--font-size-caption);
  border-bottom: 1px dashed var(--color-border);
  padding-bottom: var(--space-2);
}

.source-card__row dt {
  color: var(--color-text);
  font-weight: 600;
}

.source-card__row dd {
  margin: 0;
  color: var(--color-text-muted);
  word-break: break-word;
}

.source-card__link {
  color: var(--color-primary);
  text-decoration: underline;
}

.source-card__link:hover {
  color: var(--color-primary-dark);
}

.source-card__link:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
  border-radius: var(--radius-sm);
}

.source-card__body {
  font-size: var(--font-size-caption);
  color: var(--color-text-muted);
}

.source-card__body:empty {
  display: none;
}

/* 仅供屏幕阅读器识别的辅助文本，视觉上不可见 */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* 平板及以上（>= 640px）：来源元数据由纵向堆叠改为左右对齐的行布局 */
@media (min-width: 640px) {
  .source-card__row {
    flex-direction: row;
    align-items: baseline;
    justify-content: space-between;
    gap: var(--space-3);
    padding-bottom: var(--space-1);
  }

  .source-card__row dd {
    text-align: right;
  }
}

/* 桌面端（>= 960px）：增加卡片内边距与元数据间距，提升可读性 */
@media (min-width: 960px) {
  .source-card {
    padding: var(--space-6);
  }

  .source-card__meta {
    gap: var(--space-3);
  }
}
</style>
