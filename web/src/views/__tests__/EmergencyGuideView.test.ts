import { beforeEach, describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import EmergencyGuideView from '../EmergencyGuideView.vue'

describe('EmergencyGuideView：三步引导 + 结果页', () => {
  beforeEach(() => {
    window.localStorage.clear()
  })

  it('场景15/16：所有选项均为原生 button（浏览器默认支持 Tab + Enter/Space 键盘操作）', () => {
    const wrapper = mount(EmergencyGuideView)
    const options = wrapper.findAll('.option-card')
    expect(options.length).toBeGreaterThan(0)
    options.forEach((opt) => expect(opt.element.tagName).toBe('BUTTON'))
  })

  it('一次只展示当前步骤，顶部显示"第 X 步，共 3 步"', async () => {
    const wrapper = mount(EmergencyGuideView)
    expect(wrapper.text()).toContain('第 1 步，共 3 步')
    expect(wrapper.findAll('.option-card')).toHaveLength(9) // custodyStageOptions

    await wrapper.findAll('.option-card')[3]!.trigger('click') // 在看守所羁押
    expect(wrapper.text()).toContain('第 2 步，共 3 步')
    expect(wrapper.findAll('.option-card')).toHaveLength(10) // relationshipOptions
  })

  it('走完三步后生成结果页，包含未婚恋人 + 看守所 + 未联系律师的完整清单', async () => {
    const wrapper = mount(EmergencyGuideView)

    await wrapper.findAll('.option-card')[3]!.trigger('click') // 在看守所羁押
    await wrapper.findAll('.option-card')[5]!.trigger('click') // 未婚恋人
    await wrapper.findAll('.option-card')[2]!.trigger('click') // 还没有联系律师

    const text = wrapper.text()
    expect(text).toContain('你的紧急行动清单')
    expect(text).toContain('今天优先完成的三件事')
    expect(text).toContain('建议寻找的适格联系人')
    expect(text).toContain('联系不到近亲属怎么办')
    expect(text).toContain('看守所羁押阶段')
    expect(text).toContain('防诈骗提醒')
    expect(text).toContain('官方法律依据')
    expect(text).toContain('最后核验日期：待核验')
  })

  it('配偶等适格关系不展示"建议寻找的适格联系人"区域', async () => {
    const wrapper = mount(EmergencyGuideView)
    await wrapper.findAll('.option-card')[0]!.trigger('click') // 刚被公安机关带走
    await wrapper.findAll('.option-card')[0]!.trigger('click') // 配偶
    await wrapper.findAll('.option-card')[0]!.trigger('click') // 已经正式委托律师

    expect(wrapper.text()).not.toContain('建议寻找的适格联系人')
    expect(wrapper.text()).toContain('已委托律师后，接下来可以做什么')
  })

  it('可以返回上一步修改选择', async () => {
    const wrapper = mount(EmergencyGuideView)
    await wrapper.findAll('.option-card')[0]!.trigger('click')
    expect(wrapper.text()).toContain('第 2 步，共 3 步')
    await wrapper.find('.wizard-step__back').trigger('click')
    expect(wrapper.text()).toContain('第 1 步，共 3 步')
  })

  it('打印相关元素带有 no-print，联系人操作区不会出现在打印输出中', async () => {
    const wrapper = mount(EmergencyGuideView)
    await wrapper.findAll('.option-card')[0]!.trigger('click')
    await wrapper.findAll('.option-card')[0]!.trigger('click')
    await wrapper.findAll('.option-card')[0]!.trigger('click')

    expect(wrapper.find('.contact-actions').classes()).toContain('no-print')
    expect(wrapper.find('.result-actions').classes()).toContain('no-print')
  })

  it('结果页保留法律来源、最后核验日期与免责声明（打印内容要求）', async () => {
    const wrapper = mount(EmergencyGuideView)
    await wrapper.findAll('.option-card')[0]!.trigger('click')
    await wrapper.findAll('.option-card')[0]!.trigger('click')
    await wrapper.findAll('.option-card')[0]!.trigger('click')

    expect(wrapper.text()).toContain('LawGuard 不提供个案法律意见')
    expect(wrapper.text()).toContain('本指引根据用户选择的关系和案件阶段提供一般性程序信息')
  })
})
