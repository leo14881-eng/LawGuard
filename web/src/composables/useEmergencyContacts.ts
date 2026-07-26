import { ref } from 'vue'
import type { OptionItem } from '../data/emergencyGuidance'

/**
 * "被羁押后紧急行动指引"联系人本地存储。
 *
 * 设计要求（对应任务"十一、联系人数据与隐私"）：
 * - 仅使用 localStorage，不上传服务器、不要求登录；
 * - 不采集身份证号码、证件、法律文书或具体案情，字段仅限姓名/关系/手机号/
 *   联系状态/备注；
 * - localStorage key 使用项目专属命名空间 `lawguard.emergencyContacts.v1`，
 *   避免与其它模块冲突，并便于未来升级数据结构时更换版本号。
 */
const STORAGE_KEY = 'lawguard.emergencyContacts.v1'

export type ContactStatus =
  | 'not-contacted'
  | 'unreachable'
  | 'reached'
  | 'unwilling'
  | 'willing'
  | 'identity-unconfirmed'

export const contactStatusOptions: OptionItem<ContactStatus>[] = [
  { value: 'not-contacted', label: '尚未联系' },
  { value: 'unreachable', label: '无法接通' },
  { value: 'reached', label: '已取得联系' },
  { value: 'unwilling', label: '不愿协助' },
  { value: 'willing', label: '愿意协助' },
  { value: 'identity-unconfirmed', label: '身份或关系待确认' },
]

const contactStatusValues: ContactStatus[] = contactStatusOptions.map((o) => o.value)

export interface EmergencyContact {
  id: string
  name: string
  relationship: string
  phone: string
  status: ContactStatus
  note: string
}

export type EmergencyContactInput = Omit<EmergencyContact, 'id'>

function generateId(): string {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`
}

function isValidContact(value: unknown): value is EmergencyContact {
  if (typeof value !== 'object' || value === null) return false
  const v = value as Record<string, unknown>
  return (
    typeof v.id === 'string' &&
    typeof v.name === 'string' &&
    typeof v.relationship === 'string' &&
    typeof v.phone === 'string' &&
    typeof v.note === 'string' &&
    typeof v.status === 'string' &&
    contactStatusValues.includes(v.status as ContactStatus)
  )
}

function readStorage(): EmergencyContact[] {
  if (typeof window === 'undefined') return []
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed: unknown = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    return parsed.filter(isValidContact)
  } catch {
    // 本地存储不可用或内容损坏时视为空列表，不阻断页面使用
    return []
  }
}

function writeStorage(contacts: EmergencyContact[]): void {
  if (typeof window === 'undefined') return
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(contacts))
  } catch {
    // 隐私模式、存储容量已满等场景下静默失败
  }
}

/** 供组件使用的联系人本地存储组合式函数；每次调用读取当前 localStorage 状态。 */
export function useEmergencyContacts() {
  const contacts = ref<EmergencyContact[]>(readStorage())

  function addContact(input: EmergencyContactInput): EmergencyContact {
    const contact: EmergencyContact = { ...input, id: generateId() }
    contacts.value = [...contacts.value, contact]
    writeStorage(contacts.value)
    return contact
  }

  function updateContact(id: string, patch: Partial<EmergencyContactInput>): void {
    contacts.value = contacts.value.map((c) => (c.id === id ? { ...c, ...patch } : c))
    writeStorage(contacts.value)
  }

  function deleteContact(id: string): void {
    contacts.value = contacts.value.filter((c) => c.id !== id)
    writeStorage(contacts.value)
  }

  function clearAll(): void {
    contacts.value = []
    writeStorage(contacts.value)
  }

  return { contacts, addContact, updateContact, deleteContact, clearAll }
}

/** 供测试直接校验持久化行为，不经过组合式函数的响应式包装。 */
export const __testing = { STORAGE_KEY, readStorage, writeStorage }
