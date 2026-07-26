import { beforeEach, describe, expect, it } from 'vitest'
import { useEmergencyContacts, __testing } from '../useEmergencyContacts'

describe('useEmergencyContacts：联系人本地存储', () => {
  beforeEach(() => {
    window.localStorage.clear()
  })

  it('场景9：新增、编辑、删除联系人，并在重新读取时恢复', () => {
    const store = useEmergencyContacts()
    expect(store.contacts.value).toHaveLength(0)

    const created = store.addContact({
      name: '张三',
      relationship: '未婚恋人',
      phone: '13800000000',
      status: 'not-contacted',
      note: '',
    })
    expect(store.contacts.value).toHaveLength(1)

    store.updateContact(created.id, { status: 'reached', note: '已通话' })
    expect(store.contacts.value[0].status).toBe('reached')
    expect(store.contacts.value[0].note).toBe('已通话')

    // 模拟"页面刷新后可以恢复本地记录"：重新调用组合式函数，读取同一份 localStorage
    const reloaded = useEmergencyContacts()
    expect(reloaded.contacts.value).toHaveLength(1)
    expect(reloaded.contacts.value[0].name).toBe('张三')
    expect(reloaded.contacts.value[0].status).toBe('reached')

    store.deleteContact(created.id)
    expect(store.contacts.value).toHaveLength(0)
    const reloadedAfterDelete = useEmergencyContacts()
    expect(reloadedAfterDelete.contacts.value).toHaveLength(0)
  })

  it('场景10：一键清除全部本地数据', () => {
    const store = useEmergencyContacts()
    store.addContact({ name: 'A', relationship: '父母', phone: '', status: 'not-contacted', note: '' })
    store.addContact({ name: 'B', relationship: '配偶', phone: '', status: 'not-contacted', note: '' })
    expect(store.contacts.value).toHaveLength(2)

    store.clearAll()
    expect(store.contacts.value).toHaveLength(0)
    expect(window.localStorage.getItem(__testing.STORAGE_KEY)).toBe('[]')
  })

  it('数据损坏时静默恢复为空列表，不抛出异常', () => {
    window.localStorage.setItem(__testing.STORAGE_KEY, '{not valid json')
    expect(() => useEmergencyContacts()).not.toThrow()
    expect(useEmergencyContacts().contacts.value).toEqual([])
  })

  it('不采集身份证号码等字段：EmergencyContactInput 仅包含允许字段', () => {
    const store = useEmergencyContacts()
    const contact = store.addContact({
      name: '李四',
      relationship: '朋友',
      phone: '13900000000',
      status: 'willing',
      note: '备注',
    })
    expect(Object.keys(contact).sort()).toEqual(['id', 'name', 'note', 'phone', 'relationship', 'status'])
  })
})
