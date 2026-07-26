import type { StatusKind } from '../components/StatusBadge.vue'

/**
 * 法律来源记录条目。
 *
 * 仅收录 LAWGUARD_SOT.md P0.2 明确允许的官方机构类别作为候选来源标识。
 * 根据 P0 / P0.3 / P0.7：具体官方链接、法律版本、最后核验日期在完成人工
 * 核验前不得凭记忆编造或推断，一律固定填写"待核验"占位文案，待执业律师
 * 或人工核验流程确认后再补充为正式内容。
 */
export interface LegalSource {
  /** 来源记录唯一标识 */
  id: string
  /** 官方来源名称（正式公布或发布该类法律内容的机构） */
  title: string
  /** 官方来源地址；完成链接核验前固定为"待核验" */
  url: string
  /** 法律版本或施行状态；完成核验前固定为"待核验" */
  version: string
  /** 最后核验日期；完成核验前固定为"待核验" */
  lastVerifiedDate: string
  /** LawGuard 对该来源用途与当前核验现状的解释，不构成具体法律条文引用 */
  explanation: string
  /** 辅助说明：与官方文本存在差异时的处理方式等一般性提示 */
  note: string
  /** 核验状态徽标 */
  status: StatusKind
}

export const legalSources: LegalSource[] = [
  {
    id: 'npc-official-law',
    title: '全国人民代表大会（法律正式公布机关）',
    url: '待核验',
    version: '待核验',
    lastVerifiedDate: '待核验',
    explanation:
      '法护后续涉及刑事诉讼相关权利与程序的说明，计划逐条对照全国人民代表大会正式公布的法律文本进行核验。' +
      '该机构属于 LAWGUARD_SOT.md P0.2 允许的官方来源类别，但目前尚未完成具体条文与官方链接的逐条核验，' +
      '本记录仅用于标记候选来源，不作为已核验的法律条文引用。',
    note: '如后续页面内容与全国人民代表大会正式公布文本存在差异，以官方文本为准；官方链接完成核验前不提供可跳转地址。',
    status: 'pending',
  },
  {
    id: 'supreme-court-official',
    title: '最高人民法院（司法解释发布机关）',
    url: '待核验',
    version: '待核验',
    lastVerifiedDate: '待核验',
    explanation:
      '最高人民法院发布的司法解释属于 P0.2 允许的官方来源类别之一。法护尚未针对具体司法解释条文完成核验，' +
      '本记录仅用于标记候选来源，暂不构成对具体法律程序或适用条件的引用。',
    note: '如后续页面内容涉及相关司法解释，将在完成人工核验后再补充具体版本、施行日期与官方链接。',
    status: 'pending',
  },
  {
    id: 'mps-official-rules',
    title: '公安部（部门规章发布机关）',
    url: '待核验',
    version: '待核验',
    lastVerifiedDate: '待核验',
    explanation:
      '"被羁押后紧急行动指引"功能中涉及侦查阶段委托辩护人、转达委托要求等程序性说明，计划对照公安部发布的' +
      '部门规章进行核验。该机构属于 LAWGUARD_SOT.md P0.2 允许的官方来源类别，但目前尚未完成具体条文核验，' +
      '本记录仅用于标记候选来源，不作为已核验的法律程序引用。',
    note: '如后续内容与公安部正式发布文本存在差异，以官方文本为准；官方链接完成核验前不提供可跳转地址。',
    status: 'pending',
  },
]
