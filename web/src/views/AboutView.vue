<script setup lang="ts">
import NoticeBanner from '../components/NoticeBanner.vue'
</script>

<template>
  <div class="container section">
    <h1>关于法护 LawGuard</h1>

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
      <NoticeBanner tone="caution" title="非官方与公益性质">
        <p>本平台不属于政府机关，不属于公安机关、检察院、法院，不属于律师事务所或法律援助机构。</p>
        <p>本平台不接受个案委托，不代理案件，不提供具体案件分析或辩护策略，不预测案件结果，不替代执业律师。</p>
        <p>本平台不判断具体机关或人员是否违法，不推荐诉讼策略、辩护方案、举报方案或规避法律责任的方法。</p>
        <p>本平台不收集案件信息，不允许用户上传材料，不提供在线咨询或 AI 聊天。</p>
        <p>本平台完全免费，当前版本不接受捐款。</p>
      </NoticeBanner>
    </section>
  </div>
</template>

<style scoped>
.lead {
  color: var(--color-text-muted);
  max-width: 640px;
}
</style>
