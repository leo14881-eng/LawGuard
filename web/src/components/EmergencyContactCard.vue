<script setup lang="ts">
/**
 * 单条紧急联系人记录：姓名/关系/手机号/状态/备注均可编辑，改动即时通过
 * emit('update', ...) 交给父组件写入 localStorage（见 useEmergencyContacts）。
 * 不采集身份证号码、住址或证件信息。
 */
import { contactStatusOptions, type EmergencyContact, type ContactStatus } from '../composables/useEmergencyContacts'
import { maskPhone } from '../utils/phoneMask'

const props = defineProps<{
  contact: EmergencyContact
  /** 打印/展示时是否显示完整手机号，默认脱敏 */
  showFullPhone?: boolean
}>()

const emit = defineEmits<{
  update: [patch: Partial<Omit<EmergencyContact, 'id'>>]
  delete: []
}>()

function onField<K extends 'name' | 'relationship' | 'phone' | 'note'>(field: K, event: Event) {
  const value = (event.target as HTMLInputElement | HTMLTextAreaElement).value
  emit('update', { [field]: value } as Partial<Omit<EmergencyContact, 'id'>>)
}

function onStatusChange(event: Event) {
  emit('update', { status: (event.target as HTMLSelectElement).value as ContactStatus })
}

function markReached() {
  emit('update', { status: 'reached' })
}

const displayPhone = (contact: EmergencyContact) => (props.showFullPhone ? contact.phone : maskPhone(contact.phone))
</script>

<template>
  <div class="contact-card card">
    <div class="contact-card__row contact-card__row--2col no-print">
      <label class="contact-card__field">
        <span class="contact-card__label">姓名</span>
        <input
          class="contact-card__input"
          type="text"
          :value="contact.name"
          placeholder="例如：张三"
          @change="onField('name', $event)"
        />
      </label>
      <label class="contact-card__field">
        <span class="contact-card__label">与当事人的关系</span>
        <input
          class="contact-card__input"
          type="text"
          :value="contact.relationship"
          placeholder="例如：配偶"
          @change="onField('relationship', $event)"
        />
      </label>
    </div>

    <div class="contact-card__row contact-card__row--2col no-print">
      <label class="contact-card__field">
        <span class="contact-card__label">手机号</span>
        <input
          class="contact-card__input"
          type="tel"
          :value="contact.phone"
          placeholder="例如：13800000000"
          @change="onField('phone', $event)"
        />
      </label>
      <label class="contact-card__field">
        <span class="contact-card__label">联系状态</span>
        <select class="contact-card__input" :value="contact.status" @change="onStatusChange">
          <option v-for="opt in contactStatusOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
        </select>
      </label>
    </div>

    <label class="contact-card__field no-print">
      <span class="contact-card__label">备注</span>
      <textarea
        class="contact-card__input"
        rows="2"
        :value="contact.note"
        placeholder="选填，例如沟通情况、下次跟进时间"
        @change="onField('note', $event)"
      />
    </label>

    <!-- 打印/只读展示：屏幕上默认隐藏可编辑控件时使用同一份数据的静态呈现 -->
    <dl class="contact-card__print-view print-only">
      <div><dt>姓名</dt><dd>{{ contact.name || '（未填写）' }}</dd></div>
      <div><dt>关系</dt><dd>{{ contact.relationship || '（未填写）' }}</dd></div>
      <div><dt>手机号</dt><dd>{{ displayPhone(contact) }}</dd></div>
      <div>
        <dt>联系状态</dt>
        <dd>{{ contactStatusOptions.find((o) => o.value === contact.status)?.label }}</dd>
      </div>
      <div v-if="contact.note"><dt>备注</dt><dd>{{ contact.note }}</dd></div>
    </dl>

    <div class="contact-card__actions no-print">
      <button type="button" class="btn btn-secondary contact-card__action" @click="markReached">标记已联系</button>
      <button type="button" class="btn btn-secondary contact-card__action" @click="emit('delete')">删除</button>
    </div>
  </div>
</template>

<style scoped>
.contact-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.contact-card__row {
  display: grid;
  gap: var(--space-3);
}

.contact-card__row--2col {
  grid-template-columns: 1fr;
}

@media (min-width: 640px) {
  .contact-card__row--2col {
    grid-template-columns: 1fr 1fr;
  }
}

.contact-card__field {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.contact-card__label {
  font-size: var(--font-size-label);
  font-weight: 600;
  color: var(--color-text-muted);
}

.contact-card__input {
  width: 100%;
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-body);
  font-family: inherit;
  color: var(--color-text);
  background: var(--color-bg);
}

.contact-card__input:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 1px;
  border-color: var(--color-primary-light);
}

.contact-card__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.contact-card__action {
  font-size: var(--font-size-caption);
  padding: var(--space-2) var(--space-4);
}

.contact-card__print-view {
  margin: 0;
  display: grid;
  gap: var(--space-1);
}

.contact-card__print-view div {
  display: flex;
  gap: var(--space-2);
}

.contact-card__print-view dt {
  font-weight: 700;
  min-width: 5em;
}

.contact-card__print-view dd {
  margin: 0;
}
</style>
