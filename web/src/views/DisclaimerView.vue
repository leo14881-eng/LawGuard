<script setup lang="ts">
import PageHeader from '../components/PageHeader.vue'
import LegalDisclaimer from '../components/LegalDisclaimer.vue'
</script>

<template>
  <div class="container section">
    <PageHeader
      title="使用边界说明"
      description="本平台提供的是一般性、通俗化的普法信息，不构成针对任何具体案件的法律意见。"
    />

    <div class="prose">
      <LegalDisclaimer expanded />

      <section>
        <h2>本平台不做的事</h2>
        <ul>
          <li>不提供个案判断，不针对具体案件、具体机关或具体人员发表意见；</li>
          <li>不替代执业律师，不提供辩护策略；</li>
          <li>不收集用户案件材料，不提供上传、提交或在线咨询功能；</li>
          <li>不提供 AI 聊天或自动化法律建议。</li>
        </ul>
      </section>

      <section>
        <h2>遇到紧急或重大事项时</h2>
        <p>请及时联系执业律师，<span class="text-keep">或通过</span> <RouterLink to="/official-channels">官方救济渠道</RouterLink> 寻求帮助。</p>
      </section>
    </div>
  </div>
</template>
