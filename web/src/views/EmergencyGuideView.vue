<script setup lang="ts">
/**
 * "被羁押后紧急行动指引"：3 步引导（案件阶段 → 关系 → 是否已有律师）+ 结果页。
 * 所有生成逻辑复用 data/emergencyGuidance.ts 中的纯函数/静态数据，本组件只负责
 * 交互状态与渲染，不在组件内硬编码法律判断（见该文件头部说明）。
 */
import { computed, ref } from 'vue'
import StepProgress from '../components/StepProgress.vue'
import AppAccordion from '../components/AppAccordion.vue'
import NoticeBanner from '../components/NoticeBanner.vue'
import PageHeader from '../components/PageHeader.vue'
import LegalDisclaimer from '../components/LegalDisclaimer.vue'
import TrustBanner from '../components/TrustBanner.vue'
import PrintPageButton from '../components/PrintPageButton.vue'
import PrintFooter from '../components/PrintFooter.vue'
import SharePanel from '../components/SharePanel.vue'
import EmergencyContactCard from '../components/EmergencyContactCard.vue'
import SourceCitationCard from '../components/SourceCitationCard.vue'
import {
  custodyStageOptions,
  relationshipOptions,
  lawyerStatusOptions,
  isEligibleRelationship,
  getIdentityGuidance,
  suggestedContactOrder,
  buildTodayPriorities,
  fallbackPaths,
  getMeetingGuidance,
  fraudWarnings,
  getLawyerNextSteps,
  legalSourceIds,
  unifiedDisclaimer,
  contactRecordDisclaimer,
  type CustodyStage,
  type RelationshipType,
  type LawyerStatus,
} from '../data/emergencyGuidance'
import { legalSources } from '../data/legal_sources'
import { useEmergencyContacts } from '../composables/useEmergencyContacts'

const step = ref<1 | 2 | 3 | 4>(1)
const stage = ref<CustodyStage | null>(null)
const relationship = ref<RelationshipType | null>(null)
const lawyerStatus = ref<LawyerStatus | null>(null)

function chooseStage(value: CustodyStage) {
  stage.value = value
  step.value = 2
}
function chooseRelationship(value: RelationshipType) {
  relationship.value = value
  step.value = 3
}
function chooseLawyerStatus(value: LawyerStatus) {
  lawyerStatus.value = value
  step.value = 4
}
function goBack() {
  if (step.value > 1) step.value = (step.value - 1) as 1 | 2 | 3
}
function restart() {
  stage.value = null
  relationship.value = null
  lawyerStatus.value = null
  step.value = 1
}

const identityGuidance = computed(() => (relationship.value ? getIdentityGuidance(relationship.value) : null))
const showContactOrder = computed(() => (relationship.value ? !isEligibleRelationship(relationship.value) : false))
const todayPriorities = computed(() =>
  relationship.value && lawyerStatus.value ? buildTodayPriorities(relationship.value, lawyerStatus.value) : []
)
const meetingGuidance = computed(() => (stage.value ? getMeetingGuidance(stage.value) : null))
const lawyerNextSteps = computed(() => (lawyerStatus.value ? getLawyerNextSteps(lawyerStatus.value) : null))

const relationshipLabel = computed(
  () => relationshipOptions.find((o) => o.value === relationship.value)?.label ?? ''
)
const stageLabel = computed(() => custodyStageOptions.find((o) => o.value === stage.value)?.label ?? '')

// 联系人本地存储（仅浏览器本地，见 useEmergencyContacts 顶部说明）
const { contacts, addContact, updateContact, deleteContact, clearAll } = useEmergencyContacts()
const showFullPhone = ref(false)
const hasShownStorageNotice = ref(false)
const newContact = ref({ name: '', relationship: '', phone: '', note: '' })
const confirmClearOpen = ref(false)

function submitNewContact() {
  if (!newContact.value.name.trim()) return
  addContact({
    name: newContact.value.name.trim(),
    relationship: newContact.value.relationship.trim(),
    phone: newContact.value.phone.trim(),
    status: 'not-contacted',
    note: newContact.value.note.trim(),
  })
  newContact.value = { name: '', relationship: '', phone: '', note: '' }
  hasShownStorageNotice.value = true
}

function requestClearAll() {
  confirmClearOpen.value = true
}
function confirmClearAll() {
  clearAll()
  confirmClearOpen.value = false
}

const referencedLegalSources = computed(() =>
  legalSources.filter((s) => legalSourceIds.includes(s.id as (typeof legalSourceIds)[number]))
)
</script>

<template>
  <div class="container section">
    <TrustBanner variant="print" />

    <PageHeader
      title="被羁押后紧急行动指引"
      description="家人、恋人或朋友突然被羁押，不知道谁可以委托律师？根据关系和案件状态生成下一步行动清单。"
    />

    <TrustBanner variant="compact" />

    <NoticeBanner tone="info" title="使用前请了解">
      <p>本页面仅提供一般性程序信息，不判断具体身份资格或案件情况，不能替代律师、法律援助机构或办案机关的正式意见。</p>
    </NoticeBanner>

    <!-- 第一步：案件阶段 -->
    <section v-if="step === 1" class="wizard-step no-print">
      <StepProgress :current="1" :total="3" label="当事人目前处于什么状态？" />
      <p class="wizard-step__hint">"看守所羁押"与"监狱服刑"的会见规则不同，请分别选择，<span class="text-keep">不要混用</span>。</p>
      <div class="option-grid">
        <button
          v-for="opt in custodyStageOptions"
          :key="opt.value"
          type="button"
          class="option-card card card--interactive"
          @click="chooseStage(opt.value)"
        >
          {{ opt.label }}
        </button>
      </div>
    </section>

    <!-- 第二步：关系 -->
    <section v-else-if="step === 2" class="wizard-step no-print">
      <StepProgress :current="2" :total="3" label="你与当事人是什么关系？" />
      <p class="wizard-step__hint">请选择具体关系，不要只用"家属"这种模糊选项。</p>
      <div class="option-grid">
        <button
          v-for="opt in relationshipOptions"
          :key="opt.value"
          type="button"
          class="option-card card card--interactive"
          @click="chooseRelationship(opt.value)"
        >
          {{ opt.label }}
        </button>
      </div>
      <button type="button" class="btn btn-secondary wizard-step__back" @click="goBack">上一步</button>
    </section>

    <!-- 第三步：是否已有律师 -->
    <section v-else-if="step === 3" class="wizard-step no-print">
      <StepProgress :current="3" :total="3" label="现在是否已经有辩护律师？" />
      <div class="option-grid">
        <button
          v-for="opt in lawyerStatusOptions"
          :key="opt.value"
          type="button"
          class="option-card card card--interactive"
          @click="chooseLawyerStatus(opt.value)"
        >
          {{ opt.label }}
        </button>
      </div>
      <button type="button" class="btn btn-secondary wizard-step__back" @click="goBack">上一步</button>
    </section>

    <!-- 第四步：结果页 -->
    <section v-else class="result">
      <h2>你的紧急行动清单</h2>

      <!-- 身份结果卡 -->
      <div class="card identity-card">
        <p class="identity-card__meta">
          关系：{{ relationshipLabel }}　案件阶段：{{ stageLabel }}
        </p>
        <p>{{ identityGuidance?.summary }}</p>
        <h3 class="identity-card__subtitle">你现在可以做的事情</h3>
        <ul>
          <li v-for="item in identityGuidance?.canDo" :key="item">{{ item }}</li>
        </ul>
        <NoticeBanner tone="caution">
          <p v-for="item in identityGuidance?.mayNotDoDirectly" :key="item">{{ item }}</p>
        </NoticeBanner>
        <button type="button" class="btn btn-primary identity-card__action no-print" @click="step = 3">
          查看下一步行动
        </button>
      </div>

      <!-- 今天优先完成的三件事 -->
      <section class="section result-section">
        <h3>今天优先完成的三件事</h3>
        <ol class="priority-list">
          <li v-for="item in todayPriorities" :key="item">{{ item }}</li>
        </ol>
      </section>

      <!-- 建议寻找的适格联系人 -->
      <section v-if="showContactOrder" class="section result-section">
        <h3>建议寻找的适格联系人</h3>
        <p class="result-section__hint">
          以下人员通常属于需要优先核实的监护人或近亲属范围。是否能够代为办理具体手续，仍需结合身份、关系证明和办理机构要求确认，不是法律上的强制优先顺序。
        </p>
        <ol class="priority-list">
          <li v-for="item in suggestedContactOrder" :key="item">{{ item }}</li>
        </ol>
      </section>

      <!-- 联系人记录 -->
      <section class="section result-section">
        <h3>联系人记录</h3>
        <p class="result-section__hint no-print">
          联系人和行动记录仅保存在当前浏览器。请勿在公共电脑或他人设备上保存敏感信息。
        </p>
        <p v-if="hasShownStorageNotice" class="result-section__hint no-print">
          已保存到本地浏览器：刷新页面后仍可看到，清除浏览器数据或更换设备后将无法恢复。
        </p>

        <div v-if="contacts.length" class="contact-list">
          <EmergencyContactCard
            v-for="contact in contacts"
            :key="contact.id"
            :contact="contact"
            :show-full-phone="showFullPhone"
            @update="(patch) => updateContact(contact.id, patch)"
            @delete="deleteContact(contact.id)"
          />
        </div>
        <p v-else class="result-section__hint">暂无联系人记录，可在下方添加。</p>

        <form class="contact-form card no-print" @submit.prevent="submitNewContact">
          <h4 class="contact-form__title">添加联系人</h4>
          <div class="contact-form__row">
            <input v-model="newContact.name" class="contact-form__input" type="text" placeholder="姓名" required />
            <input v-model="newContact.relationship" class="contact-form__input" type="text" placeholder="与当事人的关系" />
          </div>
          <div class="contact-form__row">
            <input v-model="newContact.phone" class="contact-form__input" type="tel" placeholder="手机号" />
            <input v-model="newContact.note" class="contact-form__input" type="text" placeholder="备注（选填）" />
          </div>
          <button type="submit" class="btn btn-primary">添加联系人</button>
        </form>

        <div class="contact-actions no-print">
          <label class="contact-actions__toggle">
            <input v-model="showFullPhone" type="checkbox" />
            打印/展示时显示完整联系方式（默认关闭，手机号默认脱敏为 138****5678）
          </label>
          <button type="button" class="btn btn-secondary" @click="requestClearAll">一键清除所有记录</button>
        </div>
        <div v-if="confirmClearOpen" class="card confirm-clear no-print">
          <p>清除后将无法恢复，确认要清除全部本地联系人记录吗？</p>
          <div class="confirm-clear__actions">
            <button type="button" class="btn btn-secondary" @click="confirmClearAll">确认清除</button>
            <button type="button" class="btn btn-secondary" @click="confirmClearOpen = false">取消</button>
          </div>
        </div>
        <p class="result-section__caveat">{{ contactRecordDisclaimer }}</p>
      </section>

      <!-- 已有律师或联系律师步骤 -->
      <section class="section result-section">
        <h3>{{ lawyerNextSteps?.title }}</h3>
        <ul>
          <li v-for="item in lawyerNextSteps?.steps" :key="item">{{ item }}</li>
        </ul>
      </section>

      <!-- 联系不到近亲属时的替代路径 -->
      <section class="section result-section">
        <h3>联系不到近亲属怎么办？</h3>
        <div class="fallback-list">
          <div v-for="path in fallbackPaths" :key="path.id" class="card fallback-card">
            <h4 class="fallback-card__title">{{ path.title }}</h4>
            <p>{{ path.description }}</p>
            <p v-if="path.template" class="fallback-card__template">可参考的询问模板：{{ path.template }}</p>
            <p class="fallback-card__caveat">{{ path.caveat }}</p>
          </div>
        </div>
      </section>

      <!-- 看守所或监狱相关说明 -->
      <section class="section result-section">
        <h3>{{ meetingGuidance?.title }}</h3>
        <ul>
          <li v-for="point in meetingGuidance?.points" :key="point">{{ point }}</li>
        </ul>
      </section>

      <!-- 防诈骗提醒 -->
      <section class="section result-section">
        <h3>防诈骗提醒</h3>
        <NoticeBanner tone="caution" title="遇到以下情况应保持警惕">
          <ul>
            <li v-for="item in fraudWarnings" :key="item">{{ item }}</li>
          </ul>
        </NoticeBanner>
      </section>

      <!-- 官方法律依据（默认折叠） -->
      <section class="section result-section no-print">
        <AppAccordion title="官方法律依据（待法律复核）">
          <p class="result-section__hint">
            以下为候选官方来源，具体条文尚未完成执业律师逐条核验，暂不作为已核验的法律条文引用。
          </p>
          <div class="grid grid-2 legal-source-list">
            <SourceCitationCard
              v-for="source in referencedLegalSources"
              :key="source.id"
              :source-name="source.title"
              :source-ref="source.url"
              :version="source.version"
              :verified-date="source.lastVerifiedDate"
              :status="source.status"
            />
          </div>
        </AppAccordion>
      </section>

      <p class="result-section__last-verified">最后核验日期：待核验</p>

      <LegalDisclaimer />
      <p class="result-section__unified-disclaimer">{{ unifiedDisclaimer }}</p>

      <div class="result-actions no-print">
        <PrintPageButton page-title="被羁押后紧急行动清单 - 法护 LawGuard" />
        <button type="button" class="btn btn-secondary" @click="restart">重新开始</button>
      </div>

      <div class="result-share no-print">
        <SharePanel variant="primary" />
      </div>
    </section>

    <PrintFooter />
  </div>
</template>

<style scoped>
.wizard-step__hint {
  color: var(--color-text-muted);
  font-size: var(--font-size-caption);
  margin-bottom: var(--space-5);
}

.wizard-step__back {
  margin-top: var(--space-5);
}

.option-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-3);
}

@media (min-width: 640px) {
  .option-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.option-card {
  text-align: left;
  font: inherit;
  font-weight: 600;
  color: var(--color-text);
  cursor: pointer;
  min-height: 56px;
}

.result {
  margin-top: var(--space-2);
}

.identity-card {
  margin-bottom: var(--space-6);
}

.identity-card__meta {
  font-size: var(--font-size-caption);
  font-weight: 600;
  color: var(--color-primary);
  margin-bottom: var(--space-2);
}

.identity-card__subtitle {
  margin-top: var(--space-4);
}

.identity-card__action {
  margin-top: var(--space-4);
}

.result-section {
  padding-top: var(--space-6);
  border-top: 1px solid var(--color-border);
}

.result-section__hint {
  color: var(--color-text-muted);
  font-size: var(--font-size-caption);
}

.result-section__caveat {
  font-size: var(--font-size-caption);
  color: var(--color-text-muted);
  font-style: italic;
  margin-top: var(--space-3);
}

.result-section__last-verified {
  font-size: var(--font-size-caption);
  color: var(--color-text-muted);
  margin-top: var(--space-6);
}

.result-section__unified-disclaimer {
  font-size: var(--font-size-caption);
  color: var(--color-text-muted);
  margin-top: var(--space-3);
}

.priority-list li {
  margin-bottom: var(--space-2);
}

.contact-list {
  display: grid;
  gap: var(--space-4);
  margin-bottom: var(--space-4);
}

.contact-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
}

.contact-form__title {
  margin: 0;
}

.contact-form__row {
  display: grid;
  gap: var(--space-3);
  grid-template-columns: 1fr;
}

@media (min-width: 640px) {
  .contact-form__row {
    grid-template-columns: 1fr 1fr;
  }
}

.contact-form__input {
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-body);
  font-family: inherit;
}

.contact-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-4);
  margin-bottom: var(--space-3);
}

.contact-actions__toggle {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--font-size-caption);
  color: var(--color-text-muted);
}

.confirm-clear {
  border-color: var(--color-error-border);
  background: var(--color-error-bg);
}

.confirm-clear__actions {
  display: flex;
  gap: var(--space-3);
  margin-top: var(--space-3);
}

.fallback-list {
  display: grid;
  gap: var(--space-4);
}

.fallback-card__title {
  margin-top: 0;
}

.fallback-card__template {
  font-size: var(--font-size-caption);
  background: var(--color-surface);
  border-radius: var(--radius-sm);
  padding: var(--space-3);
}

.fallback-card__caveat {
  font-size: var(--font-size-caption);
  color: var(--color-text-muted);
  font-style: italic;
  margin-bottom: 0;
}

.legal-source-list {
  margin-top: var(--space-4);
}

.result-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  margin-top: var(--space-6);
}

.result-share {
  margin-top: var(--space-6);
  padding-top: var(--space-6);
  border-top: 1px solid var(--color-border);
}
</style>
