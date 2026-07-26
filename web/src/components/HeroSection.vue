<script setup lang="ts">
/**
 * 首页 Hero 区域（方案 A · 可信公益型）：左侧文案 + 右侧静态使用流程卡片，
 * 浅色背景、低饱和度，突出"平和、可信、家属友好"的基调，不使用深色通栏
 * 或高对比强调色。
 */
const navigationSteps = ['选择案件阶段', '查看当前权利', '获取行动清单', '核对官方渠道']
</script>

<template>
  <section class="hero">
    <div class="container hero__inner">
      <div class="hero__main">
        <span class="hero__tag">刑事案件公益应急导航</span>
        <h1 class="hero__title">关键时刻，先弄清楚下一步该怎么办</h1>
        <p class="hero__subtitle">
          为刑事案件当事人及家属提供基于官方法律依据的程序导航、权利指引、文书核对和救济渠道。
        </p>

        <div class="hero__actions">
          <RouterLink to="/emergency-guide" class="btn btn-primary">开始应急导航</RouterLink>
          <RouterLink to="/stages" class="btn btn-secondary">按案件阶段查看</RouterLink>
        </div>

        <p class="hero__helper">无需注册 · 不收集信息 · 永久免费</p>
      </div>

      <div class="hero__aside">
        <div class="card hero__steps" aria-label="使用流程">
          <p class="hero__steps-title">使用流程</p>
          <ol class="hero__steps-list">
            <li v-for="(step, index) in navigationSteps" :key="step" class="hero__steps-item">
              <span class="hero__steps-index" aria-hidden="true">{{ index + 1 }}</span>
              {{ step }}
            </li>
          </ol>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.hero {
  background: linear-gradient(180deg, var(--color-surface) 0%, var(--color-bg) 100%);
  padding: var(--space-8) 0;
}

.hero__inner {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.hero__main {
  flex: 1 1 auto;
}

.hero__tag {
  display: inline-block;
  font-size: var(--font-size-label);
  font-weight: 600;
  color: var(--color-primary);
  background: var(--color-info-bg);
  border: 1px solid var(--color-info-border);
  border-radius: var(--radius-pill);
  padding: 3px 12px;
  margin-bottom: var(--space-3);
}

.hero__title {
  margin: 0 0 var(--space-3);
  max-width: 14em;
  text-wrap: balance;
}

.hero__subtitle {
  font-size: 16px;
  color: var(--color-text-muted);
  margin-bottom: var(--space-5);
  max-width: 520px;
}

.hero__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  margin-bottom: var(--space-3);
}

.hero__helper {
  font-size: var(--font-size-caption);
  color: var(--color-text-muted);
  margin: 0;
}

.hero__steps {
  display: flex;
  flex-direction: column;
}

.hero__steps-title {
  font-size: 13px;
  color: var(--color-text-muted);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin: 0 0 var(--space-4);
}

.hero__steps-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.hero__steps-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  font-weight: 600;
  color: var(--color-text);
}

.hero__steps-index {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--color-primary);
  color: var(--color-text-inverse);
  font-size: 13px;
  font-weight: 700;
}

@media (min-width: 960px) {
  .hero {
    padding: var(--space-8) 0;
  }

  .hero__inner {
    flex-direction: row;
    align-items: center;
    gap: var(--space-10);
  }

  .hero__main {
    flex: 0 0 58%;
  }

  .hero__aside {
    flex: 0 0 38%;
  }
}
</style>
