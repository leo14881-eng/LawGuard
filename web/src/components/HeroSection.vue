<script setup lang="ts"></script>

<template>
  <section class="hero">
    <div class="container hero__inner">
      <h1>在法律框架内，了解并维护自己的合法权益</h1>
      <p class="hero__subtitle">
        面向刑事诉讼参与人及家属的免费公益普法平台，提供一般性权利说明、程序指引、文书核对方法和官方救济渠道。
      </p>

      <div class="hero__actions">
        <RouterLink to="/stages" class="btn btn-primary">按当前阶段查看</RouterLink>
        <RouterLink to="/official-channels" class="btn btn-secondary">查看官方救济渠道</RouterLink>
      </div>

      <p class="hero__caution">
        本平台不是政府机关、律师事务所或法律援助机构，不提供具体案件法律意见。
      </p>
    </div>
  </section>
</template>

<style scoped>
.hero {
  background: linear-gradient(180deg, var(--color-surface) 0%, var(--color-bg) 100%);
  padding: 48px 0 40px;
}

.hero__inner {
  max-width: 760px;
}

.hero__subtitle {
  font-size: 16px;
  color: var(--color-text-muted);
  margin-bottom: 24px;
}

.hero__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 20px;
}

.hero__caution {
  font-size: 13px;
  color: var(--color-notice-text);
  background: var(--color-notice-bg);
  border: 1px solid var(--color-notice-border);
  border-radius: var(--radius);
  padding: 10px 14px;
  display: inline-block;
  margin-bottom: 0;
}
</style>
