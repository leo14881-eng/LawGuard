<script setup lang="ts">
import LegalDisclaimer from './LegalDisclaimer.vue'

const updatedAt = '2026-07-26'
const githubUrl = 'https://github.com/leo14881-eng/LawGuard'
</script>

<template>
  <footer class="footer">
    <div class="container footer__inner">
      <div class="footer__col footer__brand">
        <p class="footer__title">法护 LawGuard</p>
        <p class="footer__desc">
          面向刑事案件当事人及其家属的免费公益法律信息平台，帮助了解程序、核对法律依据、查找官方救济渠道。
        </p>
        <p class="footer__desc footer__trust-line">
          纯公益项目 · 永久免费 · 不会主动联系用户 · 不会收集个人信息 · 谨防诈骗
        </p>
      </div>

      <nav class="footer__col footer__links" aria-label="页脚导航">
        <RouterLink to="/about">关于项目</RouterLink>
        <RouterLink to="/legal-sources">法律来源</RouterLink>
        <RouterLink to="/disclaimer">使用边界</RouterLink>
        <RouterLink to="/privacy">隐私说明</RouterLink>
      </nav>

      <div class="footer__col footer__meta">
        <p class="footer__meta-line">内容依据公开正式法律文本整理，标注来源与核验状态，不代表官方立场。</p>
        <p class="footer__meta-line">内容更新时间：{{ updatedAt }}（待法律复核内容以标注为准）</p>
        <p class="footer__meta-line">
          <a :href="githubUrl" target="_blank" rel="noopener noreferrer">GitHub 项目主页</a>
          · 版本 V1
        </p>
        <p class="footer__meta-line">© 2026 法护 LawGuard，保留所有权利</p>
      </div>
    </div>

    <div class="container footer__disclaimer">
      <LegalDisclaimer />
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
  padding: var(--space-8) var(--space-5);
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.footer__col {
  min-width: 0;
}

.footer__title {
  margin: 0;
  font-weight: 700;
  color: var(--color-primary-dark);
}

.footer__desc {
  margin: var(--space-2) 0 0;
  font-size: 13px;
  color: var(--color-text-muted);
  max-width: 320px;
}

.footer__trust-line {
  font-weight: 600;
  color: var(--color-notice-text);
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

.footer__meta-line {
  margin: 0 0 var(--space-2);
  font-size: 12px;
  color: var(--color-text-muted);
}

.footer__meta-line:last-child {
  margin-bottom: 0;
}

.footer__meta-line a {
  color: var(--color-text-muted);
  text-decoration: underline;
}

.footer__meta-line a:hover {
  color: var(--color-primary);
}

.footer__disclaimer {
  padding: 0 var(--space-5) var(--space-6);
}

@media (min-width: 960px) {
  .footer__inner {
    flex-direction: row;
    justify-content: space-between;
    gap: var(--space-8);
  }

  .footer__brand {
    flex: 1 1 280px;
  }

  .footer__links {
    flex-direction: column;
    gap: var(--space-2);
  }

  .footer__meta {
    flex: 0 0 auto;
    text-align: right;
  }
}
</style>
