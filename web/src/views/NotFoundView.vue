<script setup lang="ts">
/**
 * 真正未匹配到任何路由时展示的 404 页面，与 ComingSoonView（内容正在整理中，
 * 用于已规划但尚未开放的具体内容）含义不同，不应合并：ComingSoonView 用于站内
 * 已知链接指向的"待开放"内容，NotFoundView 用于访问了不存在的路径。
 */
</script>

<template>
  <div class="container section not-found">
    <h1>页面不存在</h1>
    <p>你访问的页面不存在，可能是链接有误或页面已经调整。</p>
    <div class="not-found__actions">
      <RouterLink to="/" class="btn btn-primary">返回首页</RouterLink>
      <RouterLink to="/emergency-guide" class="btn btn-secondary">开始应急导航</RouterLink>
    </div>
  </div>
</template>

<style scoped>
.not-found {
  text-align: center;
  padding: var(--space-16) var(--space-5);
}

.not-found p {
  color: var(--color-text-muted);
  max-width: 480px;
  margin: 0 auto var(--space-6);
}

.not-found__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--space-3);
}
</style>
