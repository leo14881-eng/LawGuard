<script setup lang="ts">
defineProps<{
  name: string
  description: string
  /** 是否已核验为正式官方入口，V1 默认未核验 */
  verified?: boolean
}>()
</script>

<template>
  <div class="channel-card card">
    <div class="channel-card__head">
      <h3 class="channel-card__name">{{ name }}</h3>
      <span class="badge">{{ verified ? '已核验' : '待官方链接核验' }}</span>
    </div>
    <p class="channel-card__desc">{{ description }}</p>
  </div>
</template>

<style scoped>
.channel-card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.channel-card__name {
  margin: 0;
  font-size: 17px;
}

.channel-card__desc {
  margin: 0;
  font-size: 14px;
  color: var(--color-text-muted);
}
</style>
