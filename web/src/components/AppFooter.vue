<script setup lang="ts">
const githubUrl = 'https://github.com/leo14881-eng/LawGuard'
</script>

<template>
  <footer class="footer">
    <div class="container footer__layer footer__layer--top">
      <div class="footer__brand">
        <p class="footer__title">LawGuard</p>
        <p class="footer__desc">面向刑事案件当事人及家属的公益应急导航平台</p>
      </div>

      <nav class="footer__links" aria-label="页脚导航">
        <RouterLink to="/about">关于项目</RouterLink>
        <RouterLink to="/legal-sources">法律来源</RouterLink>
        <RouterLink to="/disclaimer">使用边界</RouterLink>
        <RouterLink to="/privacy">隐私说明</RouterLink>
        <a :href="githubUrl" target="_blank" rel="noopener noreferrer">GitHub</a>
      </nav>
    </div>

    <div class="container footer__layer footer__layer--bottom">
      <p class="footer__trust-line">纯公益 · 永久免费 · 不主动联系 · 不收集个人信息</p>
      <p class="footer__copyright">© 2026 LawGuard</p>
    </div>
  </footer>
</template>

<style scoped>
.footer {
  border-top: 1px solid var(--color-border);
  background: var(--color-surface-alt);
  margin-top: auto;
}

.footer__layer {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-5);
}

.footer__layer--top {
  padding-bottom: var(--space-4);
}

.footer__layer--bottom {
  padding-top: var(--space-4);
  border-top: 1px solid var(--color-border);
  flex-direction: column;
  gap: var(--space-1);
}

.footer__title {
  margin: 0;
  font-weight: 700;
  color: var(--color-primary-dark);
}

.footer__desc {
  margin: var(--space-1) 0 0;
  font-size: 13px;
  color: var(--color-text-muted);
}

.footer__links {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-4);
}

.footer__links a {
  font-size: 14px;
  color: var(--color-text-muted);
  text-decoration: none;
}

.footer__links a:hover {
  color: var(--color-primary);
}

.footer__trust-line {
  margin: 0;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-notice-text);
}

.footer__copyright {
  margin: 0;
  font-size: 12px;
  color: var(--color-text-muted);
}

@media (min-width: 640px) {
  .footer__layer--top {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }

  .footer__layer--bottom {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }
}
</style>
