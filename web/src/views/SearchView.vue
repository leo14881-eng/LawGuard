<script setup lang="ts">
/**
 * 本地全文搜索页面（BL-003-1）。
 *
 * 仅在浏览器本地对 `data/searchItems.ts` 中的静态索引做字符串匹配，不请求
 * 任何后端接口；匹配范围为标题、摘要/内容与补充关键词，命中片段以 <mark>
 * 高亮展示，点击结果通过具名路由跳转到对应已发布页面。
 */
import { computed, ref } from 'vue'
import PageHeader from '../components/PageHeader.vue'
import TrustBanner from '../components/TrustBanner.vue'
import AppEmptyState from '../components/AppEmptyState.vue'
import StatusBadge from '../components/StatusBadge.vue'
import { searchItems, type SearchItem } from '../data/searchItems'

const keyword = ref('')

/** 归一化匹配用字符串：统一转小写，兼容英文关键词大小写混用 */
function normalize(value: string): string {
  return value.trim().toLowerCase()
}

/** 单条索引是否命中当前关键词：匹配标题、摘要/内容或补充关键词任意一项 */
function isMatch(item: SearchItem, query: string): boolean {
  if (normalize(item.title).includes(query)) return true
  if (normalize(item.summary).includes(query)) return true
  return (item.keywords ?? []).some((word) => normalize(word).includes(query))
}

const trimmedKeyword = computed(() => keyword.value.trim())

const results = computed<SearchItem[]>(() => {
  const query = normalize(trimmedKeyword.value)
  if (!query) return []
  return searchItems.filter((item) => isMatch(item, query))
})

/** 高亮片段：命中片段单独返回，交由模板渲染 <mark>，避免使用 v-html 拼接 HTML */
interface HighlightPart {
  text: string
  matched: boolean
}

function highlightParts(text: string, query: string): HighlightPart[] {
  if (!query) return [{ text, matched: false }]
  const lowerText = text.toLowerCase()
  const parts: HighlightPart[] = []
  let cursor = 0
  let matchIndex = lowerText.indexOf(query, cursor)
  while (matchIndex !== -1) {
    if (matchIndex > cursor) {
      parts.push({ text: text.slice(cursor, matchIndex), matched: false })
    }
    parts.push({ text: text.slice(matchIndex, matchIndex + query.length), matched: true })
    cursor = matchIndex + query.length
    matchIndex = lowerText.indexOf(query, cursor)
  }
  if (cursor < text.length) {
    parts.push({ text: text.slice(cursor), matched: false })
  }
  return parts
}

function titleParts(item: SearchItem): HighlightPart[] {
  return highlightParts(item.title, normalize(trimmedKeyword.value))
}

function summaryParts(item: SearchItem): HighlightPart[] {
  return highlightParts(item.summary, normalize(trimmedKeyword.value))
}

/** 结果卡片跳转目标：仅需要 :id 动态参数的路由才传入 params */
function resultTarget(item: SearchItem) {
  return item.routeId ? { name: item.routeName, params: { id: item.routeId } } : { name: item.routeName }
}
</script>

<template>
  <div class="container section">
    <PageHeader
      title="站内搜索"
      description="在法护已发布的诉讼阶段、权利指引和其它页面中搜索关键词，索引仅使用本地静态数据，不依赖后端服务。"
    />

    <TrustBanner variant="compact" />

    <div class="search-box">
      <label class="search-box__label" for="search-keyword-input">输入关键词进行搜索</label>
      <input
        id="search-keyword-input"
        v-model="keyword"
        type="search"
        class="search-box__input"
        placeholder="例如：讯问、辩护人、看守所"
        autocomplete="off"
        aria-describedby="search-result-summary"
      />
    </div>

    <p id="search-result-summary" class="search-result-summary">
      <template v-if="!trimmedKeyword">请输入关键词开始搜索。</template>
      <template v-else>共找到 {{ results.length }} 条与"{{ trimmedKeyword }}"相关的结果。</template>
    </p>

    <AppEmptyState
      v-if="trimmedKeyword && results.length === 0"
      title="未找到相关结果"
      description="请尝试更换关键词，或前往首页浏览全部内容分类。"
    />

    <AppEmptyState
      v-else-if="!trimmedKeyword"
      title="尚未输入关键词"
      description="搜索范围覆盖诉讼阶段、权利指引、法律来源记录和其它已发布页面。"
    />

    <div v-else class="result-list" role="list" aria-label="搜索结果列表">
      <RouterLink
        v-for="item in results"
        :key="item.id"
        :to="resultTarget(item)"
        class="result-card card card--interactive"
        role="listitem"
      >
        <div class="result-card__head">
          <span class="result-card__category">{{ item.category }}</span>
          <StatusBadge v-if="item.status" :status="item.status === '已复核' ? 'verified' : 'pending'" />
        </div>
        <h3 class="result-card__title">
          <template v-for="(part, index) in titleParts(item)" :key="index">
            <mark v-if="part.matched" class="result-card__mark">{{ part.text }}</mark>
            <template v-else>{{ part.text }}</template>
          </template>
        </h3>
        <p class="result-card__summary">
          <template v-for="(part, index) in summaryParts(item)" :key="index">
            <mark v-if="part.matched" class="result-card__mark">{{ part.text }}</mark>
            <template v-else>{{ part.text }}</template>
          </template>
        </p>
      </RouterLink>
    </div>
  </div>
</template>

<style scoped>
.search-box {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  max-width: 480px;
  margin-bottom: var(--space-4);
}

.search-box__label {
  font-size: var(--font-size-caption);
  font-weight: 600;
  color: var(--color-text);
}

.search-box__input {
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg);
  color: var(--color-text);
  font-size: var(--font-size-body);
  font-family: inherit;
}

.search-box__input:focus-visible {
  outline: 2px solid var(--color-action);
  outline-offset: 2px;
}

.search-result-summary {
  color: var(--color-text-muted);
  font-size: var(--font-size-caption);
  margin-bottom: var(--space-5);
}

.result-list {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-4);
}

@media (min-width: 640px) {
  .result-list {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 960px) {
  .result-list {
    grid-template-columns: repeat(3, 1fr);
  }
}

.result-card {
  display: block;
  text-decoration: none;
  color: inherit;
}

.result-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
  margin-bottom: var(--space-2);
}

.result-card__category {
  font-size: var(--font-size-label);
  font-weight: 600;
  color: var(--color-primary);
}

.result-card__title {
  margin: 0 0 var(--space-2);
  font-size: var(--font-size-block-title);
  color: var(--color-primary-dark);
}

.result-card__summary {
  margin: 0;
  font-size: var(--font-size-caption);
  color: var(--color-text-muted);
}

.result-card__mark {
  background: var(--color-notice-bg);
  color: var(--color-notice-text);
  border-radius: 3px;
  padding: 0 2px;
}
</style>
