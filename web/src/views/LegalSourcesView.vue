<script setup lang="ts">
import NoticeBanner from '../components/NoticeBanner.vue'
</script>

<template>
  <div class="container section">
    <h1>法律来源与版本记录</h1>

    <NoticeBanner tone="caution" title="内容状态说明">
      <p>本平台内容对应的具体法律条文引用正在整理，需经可核验的正式公开文本来源确认并完成法律复核后发布，当前暂未收录具体条文。</p>
    </NoticeBanner>

    <section class="section">
      <h2>内容依据原则</h2>
      <ul>
        <li>所有正式法律内容必须来自可核验的公开正式文本；</li>
        <li>不得仅凭模型记忆作为发布依据；</li>
        <li>未经执业律师审核前，统一标注为"待法律复核"。</li>
      </ul>
    </section>

    <section class="section">
      <h2>版本记录</h2>
      <p>当前为 V1 初始版本，尚未收录正式法律条文引用。后续版本将在完成法律复核后逐步补充并记录更新时间。</p>
    </section>
  </div>
</template>
