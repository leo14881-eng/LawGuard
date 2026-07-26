<script setup lang="ts">
/**
 * 未匹配到任何已知路由时展示的 404 页面。
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
