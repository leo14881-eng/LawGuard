<script setup lang="ts">
import NoticeBanner from '../components/NoticeBanner.vue'
</script>

<template>
  <div class="container section">
    <h1>关于法护 LawGuard</h1>

    <section class="section">
      <h2>项目定位</h2>
      <p>
        法护（LawGuard）是免费、公益、独立、非商业的刑事诉讼权利普法平台，致力于帮助被讯问、被追诉人员及其家属，
        在法律框架内了解法定权利、基本程序、文书核对方法和官方救济渠道。
      </p>
    </section>

    <section class="section">
      <NoticeBanner tone="caution" title="非官方与公益性质">
        <p>本平台不属于政府机关，不属于公安机关、检察院、法院，不属于律师事务所或法律援助机构。</p>
        <p>本平台不提供具体案件分析、不提供辩护策略，不判断具体机关或人员是否违法，不替代执业律师。</p>
        <p>本平台不收集案件信息，不允许用户上传材料，不提供在线咨询或 AI 聊天。</p>
        <p>本平台完全免费，当前版本不接受捐款。</p>
      </NoticeBanner>
    </section>

    <section class="section">
      <h2>目标用户</h2>
      <ul>
        <li>被讯问、被采取强制措施或被追诉的当事人；</li>
        <li>当事人的家属；</li>
        <li>需要了解刑事诉讼一般性程序与权利常识的公众。</li>
      </ul>
    </section>
  </div>
</template>
