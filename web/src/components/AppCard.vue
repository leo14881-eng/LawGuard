<script setup lang="ts">
/**
 * 统一卡片容器：在 .card 基础样式类之上补充 interactive（可交互/hover 反馈）语义。
 * 已有 StageCard / FeatureCard / ChannelCard / SourceCitationCard 等专用卡片
 * 组件的场景请继续使用专用组件，本组件用于页面中临时、通用的卡片容器场景，
 * 避免继续用裸 <div class="card"> 各自拼样式。
 */
withDefaults(
  defineProps<{
    interactive?: boolean
  }>(),
  { interactive: false }
)
</script>

<template>
  <div class="card" :class="{ 'card--interactive': interactive }">
    <slot />
  </div>
</template>
