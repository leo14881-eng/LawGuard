import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import TrustBanner from '../TrustBanner.vue'

describe('TrustBanner', () => {
  it('full 版本包含关键公益与防骗声明', () => {
    const wrapper = mount(TrustBanner, { props: { variant: 'full' } })
    expect(wrapper.text()).toContain('纯公益')
    expect(wrapper.text()).toContain('永久免费')
    expect(wrapper.text()).toContain('不会推荐律师')
    expect(wrapper.text()).toContain('可能涉嫌诈骗')
  })

  it('compact 版本文案更短但仍包含核心声明', () => {
    const wrapper = mount(TrustBanner, { props: { variant: 'compact' } })
    expect(wrapper.text()).toContain('纯公益')
    expect(wrapper.text()).toContain('不主动联系用户')
  })

  it('print 版本标记为 print-only，且包含强制免责内容', () => {
    const wrapper = mount(TrustBanner, { props: { variant: 'print' } })
    expect(wrapper.classes()).toContain('print-only')
    expect(wrapper.text()).toContain('纯公益安全提示')
    expect(wrapper.text()).toContain('不会要求注册')
  })

  it('默认 variant 为 full', () => {
    const wrapper = mount(TrustBanner)
    expect(wrapper.text()).toContain('注意防骗')
  })
})
