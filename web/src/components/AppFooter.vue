<script setup lang="ts">
const updatedAt = '2026-07-26'
</script>

<template>
  <footer class="footer">
    <div class="container footer__inner">
      <div class="footer__brand">
        <p class="footer__title">法护 LawGuard</p>
        <p class="footer__desc">公益普法项目 · 非官方机构</p>
      </div>

      <nav class="footer__links">
        <RouterLink to="/privacy">隐私说明</RouterLink>
        <RouterLink to="/disclaimer">使用边界</RouterLink>
        <RouterLink to="/legal-sources">法律来源</RouterLink>
      </nav>

      <p class="footer__meta">内容更新时间：{{ updatedAt }}（待法律复核内容以标注为准）</p>
    </div>
  </footer>
</template>

<style scoped>
.footer {
  border-top: 1px solid var(--color-border);
  background: var(--color-surface-alt);
  margin-top: auto;
}

.footer__inner {
  padding: 32px 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.footer__title {
  margin: 0;
  font-weight: 700;
  color: var(--color-primary-dark);
}

.footer__desc {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--color-text-muted);
}

.footer__links {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.footer__links a {
  font-size: 14px;
  color: var(--color-text-muted);
  text-decoration: none;
}

.footer__links a:hover {
  color: var(--color-primary);
}

.footer__meta {
  margin: 0;
  font-size: 12px;
  color: var(--color-text-muted);
}

@media (min-width: 800px) {
  .footer__inner {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }
}
</style>
