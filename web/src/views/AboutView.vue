<script setup lang="ts">
import NoticeBanner from '../components/NoticeBanner.vue'
import PageHeader from '../components/PageHeader.vue'
import TrustBanner from '../components/TrustBanner.vue'
import LegalDisclaimer from '../components/LegalDisclaimer.vue'

const privacyPoints = [
  '纯公益',
  '永久免费',
  '不需要注册',
  '不收集个人信息',
  '不建立用户画像',
  '不收集案件材料',
  '不上传身份证',
  '不上传银行卡',
  '不上传结婚证',
  '不上传户口簿',
  '不收集手机号',
  '不收集邮箱',
  '不推荐律师',
  '不接受案件委托',
  '不提供收费咨询',
  '不会主动联系任何用户',
  '不会索要任何费用',
]

const fraudBehaviors = [
  '自称 LawGuard 工作人员',
  '主动给你打电话、加微信、发 QQ、发短信或发邮件',
  '推荐律师或推荐"内部关系"',
  '承诺取保、撤案、无罪或减刑',
  '要求付款或转账',
  '要求发送身份证、银行卡或验证码',
  '要求发送案件材料',
]
</script>

<template>
  <div class="container section">
    <PageHeader title="关于法护 LawGuard" />

    <TrustBanner variant="compact" />

    <section class="section">
      <h2>项目定位</h2>
      <p>
        法护（LawGuard）是免费、公益、独立、非商业的刑事诉讼权利普法平台，
        面向刑事案件当事人及其家属，帮助了解一般性法定权利、基本程序、文书核对方法和官方救济渠道。
      </p>
      <p>
        法护希望解决的是信息难找、程序难懂、官方渠道分散的问题：把分散在不同机构、不同文件里的一般性权利
        说明与官方渠道信息，整理成通俗易懂、可核实来源的内容。
      </p>
    </section>

    <section class="section">
      <h2>谁在使用 LawGuard</h2>
      <p class="lead">
        考虑到被拘留、逮捕或羁押的当事人通常无法自由使用手机或访问互联网，法护的直接访问者主要是：
      </p>
      <ul>
        <li>刑事案件当事人的家属；</li>
        <li>已经取保候审、监视居住或未被采取强制措施、能够正常访问互联网的当事人；</li>
        <li>被害人及其家属；</li>
        <li>协助传递法律信息的律师或其他人员；</li>
        <li>希望了解刑事诉讼程序的普通公众。</li>
      </ul>
      <p>
        对于无法使用互联网的被羁押人员，法护提供适合保存和打印的一般性信息，供家属或律师依法合规地参考和传递。
        被羁押人员能否接收、持有或阅读相关材料，应以具体监管场所和办案机关的现行规定为准，
        是否能够传递给被羁押人员，不由法护决定。
      </p>
    </section>

    <section class="section">
      <LegalDisclaimer expanded />
    </section>

    <section class="section">
      <NoticeBanner tone="info" title="其它非官方与公益说明">
        <p>本平台不接受个案委托，不代理案件，不预测案件结果。</p>
        <p>本平台不收集案件信息，不允许用户上传材料，不提供在线咨询或 AI 聊天。</p>
        <p>本平台完全免费，当前版本不接受捐款。</p>
      </NoticeBanner>
    </section>

    <section class="section">
      <h2>公益与隐私声明</h2>
      <ul class="grid grid-2 privacy-list">
        <li v-for="point in privacyPoints" :key="point" class="privacy-list__item">
          <span aria-hidden="true">✓</span> {{ point }}
        </li>
      </ul>
    </section>

    <section class="section">
      <h2>谨防诈骗</h2>
      <NoticeBanner tone="caution">
        <p>如果有人出现以下行为，都不是 LawGuard 的官方行为，请不要付款，不要提供个人信息：</p>
        <ul class="fraud-list">
          <li v-for="behavior in fraudBehaviors" :key="behavior">{{ behavior }}</li>
        </ul>
      </NoticeBanner>
    </section>
  </div>
</template>

<style scoped>
.privacy-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.privacy-list__item {
  font-size: var(--font-size-body);
  color: var(--color-text);
}

.fraud-list {
  margin: var(--space-2) 0 0;
  padding-left: var(--space-5);
}

.fraud-list li {
  margin-bottom: var(--space-1);
}
</style>
