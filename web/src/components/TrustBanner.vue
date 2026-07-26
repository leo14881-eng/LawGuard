<script setup lang="ts">
/**
 * 全站统一的"公益与安全声明"组件。
 *
 * 文案统一在本组件内维护，禁止各页面自行修改措辞——如需调整，只能修改本文件。
 * 三种呈现形态：
 * - full：首页 Header 与 Hero 之间的完整版本，首屏固定显示，不可关闭/折叠/轮播。
 * - compact：其它核心页面顶部的精简版本。
 * - print：打印页面第一页顶部的强制显示版本（复用全局 .print-only 工具类，
 *   屏幕上不可见，仅在打印/另存为 PDF 时显示，且不可被隐藏或移到页面底部）。
 *
 * 颜色复用既有 --color-notice-*（浅黄色系）与 --color-info-*（蓝灰色系）
 * Design Token，不引入红色，不新增颜色变量。
 */
withDefaults(
  defineProps<{
    variant?: 'full' | 'compact' | 'print'
  }>(),
  { variant: 'full' }
)
</script>

<template>
  <div v-if="variant === 'full'" class="trust-banner trust-banner--full" role="note" aria-label="公益与安全声明">
    <p class="trust-banner__title">【纯公益 · 永久免费 · 注意防骗】</p>
    <ul class="trust-banner__list">
      <li>LawGuard 是纯公益法律信息平台，永久免费，不收取任何费用。</li>
      <li>不会主动通过电话、短信、微信、QQ、邮件或任何社交软件联系用户，不会要求注册账号。</li>
      <li>不会收集身份证、手机号、银行卡、验证码、案件材料等个人信息。</li>
      <li>不会推荐律师，不会接受案件委托，不会要求任何形式的付款或转账。</li>
    </ul>
    <p class="trust-banner__caution">
      任何冒充 LawGuard 主动联系、收费、推荐律师、承诺取保、撤案、无罪、减刑、要求转账或索要个人信息的行为，
      都可能涉嫌诈骗，请务必提高警惕。
    </p>
  </div>

  <div
    v-else-if="variant === 'compact'"
    class="trust-banner trust-banner--compact"
    role="note"
    aria-label="公益与安全声明"
  >
    <p class="trust-banner__title">【纯公益 · 永久免费】</p>
    <p class="trust-banner__compact-text">
      LawGuard 不收费、不主动联系用户、不收集个人信息。任何冒充 LawGuard 收费、推荐律师、要求付款或索要个人
      信息的行为，都可能涉嫌诈骗。
    </p>
  </div>

  <div v-else class="trust-banner trust-banner--print print-only">
    <p class="trust-banner__title">【纯公益安全提示】</p>
    <p>
      LawGuard 是纯公益法律信息平台。永久免费。不会主动联系任何用户。不会收集任何个人信息。不会要求注册。
      不会推荐律师。不会接受案件委托。不会要求付款或转账。
    </p>
    <p>
      任何冒充 LawGuard 联系用户、收费、索要身份证、银行卡、验证码、案件材料或承诺案件结果的行为，都可能
      涉嫌诈骗。
    </p>
  </div>
</template>

<style scoped>
.trust-banner {
  border-radius: var(--radius);
  border: 1px solid var(--color-notice-border);
  background: var(--color-notice-bg);
  color: var(--color-notice-text);
}

.trust-banner__title {
  margin: 0 0 var(--space-2);
  font-weight: 700;
}

.trust-banner__list {
  margin: 0 0 var(--space-2);
  padding-left: var(--space-5);
  font-size: var(--font-size-caption);
}

.trust-banner__list li {
  margin-bottom: var(--space-1);
}

.trust-banner__caution {
  margin: 0;
  font-size: var(--font-size-caption);
  font-weight: 600;
}

.trust-banner--full {
  padding: var(--space-4) var(--space-5);
}

.trust-banner--compact {
  padding: var(--space-3) var(--space-4);
  margin-bottom: var(--space-5);
}

.trust-banner--compact .trust-banner__compact-text {
  margin: 0;
  font-size: var(--font-size-caption);
}

.trust-banner--print {
  padding: var(--space-3) 0;
  margin-bottom: var(--space-5);
  border: none;
  border-top: 3px double #000;
  border-bottom: 3px double #000;
  border-radius: 0;
  background: none;
  color: #000;
}

.trust-banner--print p {
  margin: 0 0 var(--space-2);
  font-size: 12px;
}

.trust-banner--print p:last-child {
  margin-bottom: 0;
  font-weight: 700;
}
</style>
