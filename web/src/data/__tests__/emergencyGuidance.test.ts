import { describe, expect, it } from 'vitest'
import {
  getIdentityGuidance,
  isEligibleRelationship,
  buildTodayPriorities,
  getMeetingGuidance,
  getLawyerNextSteps,
  fallbackPaths,
  suggestedContactOrder,
  engagedLawyerSteps,
} from '../emergencyGuidance'

describe('emergencyGuidance：身份与优先事项', () => {
  it('场景1：未婚恋人 + 看守所羁押 + 没有律师', () => {
    expect(isEligibleRelationship('partner')).toBe(false)
    const guidance = getIdentityGuidance('partner')
    expect(guidance.summary).toContain('通常不能直接')
    expect(guidance.summary).toContain('先联系律师事务所')

    const meeting = getMeetingGuidance('in-detention-center')
    expect(meeting.title).toBe('看守所羁押阶段')
    expect(meeting.points.join('')).toContain('普通探视')

    const priorities = buildTodayPriorities('partner', 'not-contacted')
    expect(priorities).toHaveLength(3)
    expect(priorities[0]).toContain('配偶、父母、成年子女、同胞兄弟姐妹或监护人')
    expect(priorities[1]).toContain('不要只通过私人中介')
  })

  it('场景2：普通朋友 + 刚被带走情况不清楚 + 未知律师状态', () => {
    const guidance = getIdentityGuidance('friend')
    expect(guidance.mayNotDoDirectly[0]).toContain('不等于已经完成正式委托')
    const meeting = getMeetingGuidance('just-taken')
    // "刚被带走" 属于羁押前/看守所前置阶段，按看守所口径处理，不等同于"不清楚阶段"分支
    expect(meeting.title).toBe('看守所羁押阶段')
  })

  it('场景3：父母 + 已刑事拘留 + 尚无律师', () => {
    expect(isEligibleRelationship('parent')).toBe(true)
    const guidance = getIdentityGuidance('parent')
    expect(guidance.summary).toContain('监护人、近亲属可以代为委托辩护人')
    const steps = getLawyerNextSteps('not-contacted')
    expect(steps.title).toContain('还没有正式委托律师')
  })

  it('场景4：配偶 + 已逮捕 + 已联系律师但未完成委托', () => {
    const steps = getLawyerNextSteps('contacted-not-engaged')
    expect(steps.steps[0]).toContain('推进正式委托')
  })

  it('场景5：同胞兄弟姐妹 + 审查起诉 + 已正式委托律师', () => {
    expect(isEligibleRelationship('sibling')).toBe(true)
    const steps = getLawyerNextSteps('formally-engaged')
    expect(steps.steps).toEqual(engagedLawyerSteps)
    expect(steps.steps.join('')).not.toContain('立即会见')
  })

  it('场景6：未婚恋人 + 监狱服刑', () => {
    const meeting = getMeetingGuidance('serving-sentence')
    expect(meeting.title).toBe('监狱服刑阶段')
    // 不得写成"未婚恋人绝对不能/一定可以申请会见"的绝对结论，应为审慎表述
    expect(meeting.points.join('')).not.toMatch(/未婚恋人(绝对不能|一定可以|一定不能)/)
    expect(meeting.points.join('')).toContain('未婚恋人并非全国范围内绝对不能申请')
  })

  it('场景7：用户选择"不清楚"阶段', () => {
    const meeting = getMeetingGuidance('unknown')
    expect(meeting.title).toBe('案件阶段尚不清楚')
    expect(meeting.points.length).toBeGreaterThan(0)
  })

  it('场景8：联系不到近亲属时显示三条替代路径', () => {
    expect(fallbackPaths).toHaveLength(3)
    expect(fallbackPaths.map((p) => p.id)).toEqual(['self-request', 'duty-lawyer', 'legal-aid'])
    fallbackPaths.forEach((path) => {
      expect(path.caveat.length).toBeGreaterThan(0)
    })
  })

  it('建议联系人顺序不包含未婚恋人自身，且不描述为强制顺序', () => {
    expect(suggestedContactOrder).toEqual(['当事人的配偶', '父母', '成年子女', '同胞兄弟姐妹', '监护人'])
  })

  it('取保候审阶段提示与羁押阶段不同', () => {
    const meeting = getMeetingGuidance('bail-or-surveillance')
    expect(meeting.title).toContain('取保候审或监视居住')
    expect(meeting.points.join('')).toContain('不处于羁押状态')
  })
})
