<script setup lang="ts">
import NoticeBanner from '../components/NoticeBanner.vue'
import PrintPageButton from '../components/PrintPageButton.vue'
import PrintFooter from '../components/PrintFooter.vue'

const methods = [
  '核对文书上的姓名、身份信息与案件编号等基础信息是否准确。',
  '核对文书类型与所处诉讼阶段是否一致。',
  '核对文书上记录的时间、地点等信息是否与实际情况相符。',
  '在签署前确认自己已经阅读并理解文书内容，对不理解之处可以要求说明。',
  '妥善保管本人持有的文书副本。',
]
</script>

<template>
  <div class="container section">
    <h1>文书核对清单</h1>
    <p class="lead">
      核对和签署法律文书是刑事诉讼中的重要环节。以下为一般性核对方法框架，具体条目正在整理并等待法律复核。
    </p>

    <PrintPageButton class="documents-print" page-title="文书核对清单 - 法护 LawGuard" />

    <NoticeBanner tone="caution" title="内容状态说明">
      <p>本页面内容为一般性方法框架，不针对任何具体文书或具体案件给出结论，具体条目待法律复核后正式发布。</p>
    </NoticeBanner>

    <section class="section">
      <h2>一般性核对方法（待法律复核）</h2>
      <ul class="list">
        <li v-for="item in methods" :key="item">{{ item }}</li>
      </ul>
    </section>

    <section class="section">
      <h2>需要专业帮助时</h2>
      <p>
        如对具体文书内容存在疑问，建议及时联系执业律师，或通过
        <RouterLink to="/official-channels">官方救济渠道</RouterLink>
        寻求帮助。
      </p>
    </section>

    <PrintFooter />
  </div>
</template>

<style scoped>
.lead {
  color: var(--color-text-muted);
  max-width: 640px;
  margin-bottom: 20px;
}

.documents-print {
  margin-bottom: var(--space-5);
}

.list li {
  margin-bottom: 10px;
  color: var(--color-text);
}
</style>
