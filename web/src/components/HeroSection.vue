<script setup lang="ts">
/**
 * 首页 Hero 区域：标题需在 3 秒内说明网站用途，Trust Signals 建立信任在前，
 * 非法律意见声明保留但降低视觉权重（不使用色块，仅小号灰字），
 * 背景复用 --color-surface → --color-bg 的既有浅色渐变，不新增颜色。
 */
const trustSignals = [
  '官方法律来源',
  '免费公益平台',
  '内容标注最后核验日期',
  '不提供个案法律意见',
]
</script>

<template>
  <section class="hero">
    <div class="container hero__inner">
      <h1>家人卷入刑事案件，先了解程序和合法权利</h1>
      <p class="hero__subtitle">
        为刑事案件当事人及其家属提供一般性权利说明、程序指引、文书核对方法和官方救济渠道。
      </p>

      <div class="hero__actions">
        <RouterLink to="/stages" class="btn btn-primary">按案件阶段查看指引</RouterLink>
        <RouterLink to="/official-channels" class="btn btn-secondary">查找官方救济渠道</RouterLink>
      </div>

      <ul class="hero__trust" aria-label="平台信任标识">
        <li v-for="item in trustSignals" :key="item" class="hero__trust-item">
          <svg class="hero__trust-icon" viewBox="0 0 20 20" aria-hidden="true">
            <path
              d="M4 10.5l3.5 3.5 8-8"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
          {{ item }}
        </li>
      </ul>

      <p class="hero__disclaimer">
        本平台不是政府机关、律师事务所或法律援助机构，不提供具体案件法律意见。
      </p>
    </div>
  </section>
</template>

<style scoped>
.hero {
  background: linear-gradient(180deg, var(--color-surface) 0%, var(--color-bg) 100%);
  padding: var(--space-10) 0 var(--space-6);
}

.hero__inner {
  max-width: 760px;
}

.hero__subtitle {
  font-size: 16px;
  color: var(--color-text-muted);
  margin-bottom: var(--space-6);
  max-width: 620px;
}

.hero__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  margin-bottom: var(--space-5);
}

.hero__trust {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2) var(--space-3);
  list-style: none;
  padding: 0;
  margin: 0 0 var(--space-4);
}

.hero__trust-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: var(--radius-pill);
  background: var(--color-success-bg);
  border: 1px solid var(--color-success-border);
  color: var(--color-success-text);
  font-size: var(--font-size-label);
  font-weight: 600;
  white-space: nowrap;
}

.hero__trust-icon {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}

.hero__disclaimer {
  font-size: var(--font-size-caption);
  color: var(--color-text-muted);
  margin: 0;
}
</style>
