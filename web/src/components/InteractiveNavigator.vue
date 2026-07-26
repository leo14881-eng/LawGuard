<script setup lang="ts">
/**
 * 首页互动导航工具：让用户从"当前处于哪个阶段"这一问题出发，
 * 快速定位到对应的诉讼阶段说明与权利指引入口。
 * 仅做入口跳转与内容映射，不对具体案件作出任何判断，
 * 展示文案直接复用 stages.ts 中已核对的阶段名称与摘要，不新增法律事实。
 */
import { computed, ref } from 'vue'
import AppCard from './AppCard.vue'
import AppButton from './AppButton.vue'
import NoticeBanner from './NoticeBanner.vue'
import { stages } from '../data/stages'

const emit = defineEmits<{ close: [] }>()

/** 当前步骤：question 为选择情况，result 为展示映射结果 */
const step = ref<'question' | 'result'>('question')
/** 用户选中的阶段 id，对应 stages.ts / rightsGuide.ts 共用的阶段划分 */
const selected = ref<string | null>(null)

const selectedStage = computed(() => stages.find((stage) => stage.id === selected.value))

function handleConfirm() {
  if (selected.value) {
    step.value = 'result'
  }
}

function handleRestart() {
  step.value = 'question'
}

function handleClose() {
  emit('close')
}
</script>

<template>
  <AppCard class="navigator" aria-label="互动导航工具">
    <div class="navigator__header">
      <h3 class="navigator__title">互动导航</h3>
      <button
        type="button"
        class="navigator__close"
        aria-label="收起互动导航，返回首页入口"
        @click="handleClose"
      >
        返回
      </button>
    </div>

    <div class="navigator__body" aria-live="polite">
      <template v-if="step === 'question'">
        <p class="navigator__prompt">请选择当前最符合你情况的一项：</p>
        <fieldset class="navigator__fieldset">
          <legend class="sr-only">选择当前所处的情况</legend>
          <div class="navigator__options">
            <label
              v-for="stage in stages"
              :key="stage.id"
              class="navigator__option"
              :class="{ 'navigator__option--active': selected === stage.id }"
            >
              <input
                v-model="selected"
                type="radio"
                name="navigator-situation"
                class="navigator__radio-input"
                :value="stage.id"
              />
              <span class="navigator__option-text">
                <span class="navigator__option-title">{{ stage.name }}</span>
                <span class="navigator__option-desc">{{ stage.summary }}</span>
              </span>
            </label>
          </div>
        </fieldset>
        <div class="navigator__confirm-row">
          <AppButton
            :disabled="!selected"
            aria-label="根据选择的情况查看对应入口"
            @click="handleConfirm"
          >
            查看对应入口
          </AppButton>
        </div>
      </template>

      <template v-else-if="step === 'result' && selectedStage">
        <NoticeBanner tone="info">
          <p>
            此结果仅根据你选择的情况提供入口参考，不构成对具体案件的判断。具体案件请以官方文书内容和执业律师意见为准。
          </p>
        </NoticeBanner>
        <h4 class="navigator__result-title">{{ selectedStage.name }}</h4>
        <p class="navigator__result-summary">{{ selectedStage.summary }}</p>
        <div class="navigator__links">
          <RouterLink :to="`/stages/${selectedStage.id}`" class="btn btn-primary">
            查看该阶段说明
          </RouterLink>
          <RouterLink :to="`/rights-guide/${selectedStage.id}`" class="btn btn-secondary">
            查看对应权利指引
          </RouterLink>
        </div>
        <button type="button" class="navigator__restart" @click="handleRestart">
          重新选择
        </button>
      </template>
    </div>
  </AppCard>
</template>

<style scoped>
.navigator__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  margin-bottom: var(--space-3);
}

.navigator__title {
  margin: 0;
  font-size: var(--font-size-block-title);
  color: var(--color-primary-dark);
}

.navigator__close {
  flex-shrink: 0;
  background: none;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: var(--space-1) var(--space-3);
  font-size: var(--font-size-caption);
  color: var(--color-text-muted);
  cursor: pointer;
}

.navigator__close:hover {
  border-color: var(--color-action);
  color: var(--color-action);
}

.navigator__close:focus-visible {
  outline: 2px solid var(--color-action);
  outline-offset: 2px;
}

.navigator__prompt {
  margin: 0 0 var(--space-3);
  font-size: var(--font-size-caption);
  color: var(--color-text-muted);
}

.navigator__fieldset {
  border: none;
  padding: 0;
  margin: 0;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.navigator__options {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-3);
}

@media (min-width: 640px) {
  .navigator__options {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 960px) {
  .navigator__options {
    grid-template-columns: repeat(3, 1fr);
  }
}

.navigator__option {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  padding: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-bg);
  cursor: pointer;
  transition: border-color 0.2s ease, background-color 0.2s ease;
}

.navigator__option:hover {
  border-color: var(--color-action);
}

.navigator__option--active {
  border-color: var(--color-action);
  background: var(--color-surface-alt);
}

.navigator__option:focus-within {
  outline: 2px solid var(--color-action);
  outline-offset: 2px;
}

.navigator__radio-input {
  flex-shrink: 0;
  margin-top: 3px;
  width: 16px;
  height: 16px;
  accent-color: var(--color-action);
}

.navigator__option-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.navigator__option-title {
  font-size: var(--font-size-body);
  font-weight: 700;
  color: var(--color-primary-dark);
}

.navigator__option-desc {
  font-size: var(--font-size-caption);
  color: var(--color-text-muted);
}

.navigator__confirm-row {
  margin-top: var(--space-4);
}

.navigator__result-title {
  margin: var(--space-4) 0 var(--space-1);
  font-size: var(--font-size-block-title);
  color: var(--color-primary-dark);
}

.navigator__result-summary {
  margin: 0 0 var(--space-4);
  font-size: var(--font-size-caption);
  color: var(--color-text-muted);
}

.navigator__links {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  margin-bottom: var(--space-3);
}

.navigator__restart {
  background: none;
  border: none;
  padding: 0;
  font-size: var(--font-size-caption);
  color: var(--color-action);
  cursor: pointer;
  text-decoration: underline;
}

.navigator__restart:focus-visible {
  outline: 2px solid var(--color-action);
  outline-offset: 2px;
}
</style>
