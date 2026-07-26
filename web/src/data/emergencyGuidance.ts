/**
 * "被羁押后紧急行动指引"功能的内容数据模型与派生逻辑。
 *
 * 设计原则（对应任务要求"不要建设通用规则引擎"）：
 * 所有"根据用户选择生成建议"的逻辑都是几个独立、透明的查表/条件分支函数
 * （按关系是否属于近亲属/监护人范围、按是否已有律师两个维度分别取值后拼接），
 * 不做通用规则引擎、不做 AI 自动判断、不根据用户输入的自由文本生成法律意见。
 *
 * 法律真实性说明（对应 LAWGUARD_SOT.md P0）：
 * 本文件中的说明性文字均为一般性、审慎表述，尚未经过执业律师逐条核验，
 * 一律视为"待法律复核"，不引用具体法律条文编号。具体官方来源见
 * `../data/legal_sources.ts`（新增 `mps-official-rules` 条目）与本文件底部
 * `legalSourceIds` 字段。法律援助/值班律师制度的具体来源类别尚待在
 * LAWGUARD_SOT.md P0.2 中明确批准，本文件对该部分表述更加保守，不归为
 * 已核验内容。
 */

export type CustodyStage =
  | 'just-taken'
  | 'detained'
  | 'arrested'
  | 'in-detention-center'
  | 'prosecution-review'
  | 'trial'
  | 'serving-sentence'
  | 'bail-or-surveillance'
  | 'unknown'

export type RelationshipType =
  | 'spouse'
  | 'parent'
  | 'adult-child'
  | 'sibling'
  | 'guardian'
  | 'partner'
  | 'friend'
  | 'colleague'
  | 'other'
  | 'unsure'

export type LawyerStatus = 'formally-engaged' | 'contacted-not-engaged' | 'not-contacted' | 'unsure'

export interface OptionItem<T extends string> {
  value: T
  label: string
}

export const custodyStageOptions: OptionItem<CustodyStage>[] = [
  { value: 'just-taken', label: '刚被公安机关带走，情况不清楚' },
  { value: 'detained', label: '已被刑事拘留' },
  { value: 'arrested', label: '已被逮捕' },
  { value: 'in-detention-center', label: '在看守所羁押' },
  { value: 'prosecution-review', label: '已移送检察院审查起诉' },
  { value: 'trial', label: '已进入法院审理' },
  { value: 'serving-sentence', label: '已判决，正在监狱服刑' },
  { value: 'bail-or-surveillance', label: '取保候审或监视居住' },
  { value: 'unknown', label: '不清楚' },
]

export const relationshipOptions: OptionItem<RelationshipType>[] = [
  { value: 'spouse', label: '配偶' },
  { value: 'parent', label: '父亲或母亲' },
  { value: 'adult-child', label: '成年子女' },
  { value: 'sibling', label: '同胞兄弟姐妹' },
  { value: 'guardian', label: '监护人' },
  { value: 'partner', label: '未婚恋人' },
  { value: 'friend', label: '普通朋友' },
  { value: 'colleague', label: '同事' },
  { value: 'other', label: '其他关系' },
  { value: 'unsure', label: '不确定' },
]

export const lawyerStatusOptions: OptionItem<LawyerStatus>[] = [
  { value: 'formally-engaged', label: '已经正式委托律师' },
  { value: 'contacted-not-engaged', label: '已联系律师，但尚未完成委托' },
  { value: 'not-contacted', label: '还没有联系律师' },
  { value: 'unsure', label: '不确定是否已有律师' },
]

/** 通常可以代为委托辩护人的关系范围（监护人、近亲属）。 */
export const eligibleRelationships: RelationshipType[] = ['spouse', 'parent', 'adult-child', 'sibling', 'guardian']

export function isEligibleRelationship(relationship: RelationshipType): boolean {
  return eligibleRelationships.includes(relationship)
}

export interface IdentityGuidance {
  summary: string
  canDo: string[]
  mayNotDoDirectly: string[]
}

const eligibleIdentityGuidance: IdentityGuidance = {
  summary:
    '根据现行刑事诉讼相关规定，在押犯罪嫌疑人、被告人的监护人、近亲属可以代为委托辩护人。' +
    '实际办理时，律师事务所或办案机关可能要求核验身份及关系材料，具体要求以现行规定和承办机构为准。',
  canDo: [
    '联系律师事务所确认委托流程',
    '准备本人身份证明',
    '准备能够说明与当事人关系的材料',
    '准备当事人基本信息和可能的羁押信息',
    '向律师确认委托手续是否完整',
    '不要轻信"花钱捞人""保证取保"等承诺',
  ],
  mayNotDoDirectly: ['具体委托材料及关系证明要求，以律师事务所、办案机关和羁押场所的现行要求为准，不属于全国统一清单。'],
}

const nonEligibleIdentityGuidance: IdentityGuidance = {
  summary:
    '仅凭未婚恋人、朋友或同事关系，通常不能直接按照在押人员监护人或近亲属的身份代为办理辩护律师委托。' +
    '你仍然可以先联系律师事务所了解所需手续，并应尽快联系当事人的配偶、父母、成年子女、同胞兄弟姐妹或监护人。',
  canDo: [
    '尽快寻找并联系适格的监护人或近亲属',
    '先联系律师事务所，了解律师姓名、律所名称和委托材料',
    '整理当事人的姓名、可能的办案机关、羁押地点和收到的法律文书',
    '询问办案机关是否可以依法向在押人员转达其委托律师的要求',
    '了解值班律师和法律援助渠道',
  ],
  mayNotDoDirectly: ['恋人、朋友或同事帮助联系律师、传递信息，不等于已经完成正式委托。'],
}

export function getIdentityGuidance(relationship: RelationshipType): IdentityGuidance {
  return isEligibleRelationship(relationship) ? eligibleIdentityGuidance : nonEligibleIdentityGuidance
}

/** 建议优先联系的适格人员顺序：不代表法律上的强制优先顺序，仅供参考。 */
export const suggestedContactOrder: string[] = ['当事人的配偶', '父母', '成年子女', '同胞兄弟姐妹', '监护人']

function relationshipPriority(relationship: RelationshipType): string {
  if (isEligibleRelationship(relationship)) {
    return '准备好本人身份证明和能够说明与当事人关系的材料，委托律师时可能需要核验。'
  }
  return '尽快联系当事人的配偶、父母、成年子女、同胞兄弟姐妹或监护人，明确谁来牵头处理委托事宜。'
}

function lawyerPriority(lawyerStatus: LawyerStatus): string {
  switch (lawyerStatus) {
    case 'formally-engaged':
      return '尽快联系已委托的律师，确认当事人所处阶段、羁押地点，并了解委托手续是否已提交办案机关。'
    case 'contacted-not-engaged':
      return '尽快与已联系的律师确认委托手续、费用与所需材料，推进正式委托。'
    case 'not-contacted':
      return '先联系正规律师事务所了解委托手续，不要只通过私人中介打听。'
    case 'unsure':
      return '先确认当事人是否已经委托律师；不确定时，可同时联系正规律师事务所了解一般性委托流程。'
  }
}

const recordPriority =
  '记录已知的办案机关、羁押地点和收到的法律文书信息，并了解本人提出委托、值班律师和法律援助等渠道。'

/** "今天优先完成的三件事"：按关系维度与律师状态维度独立取值后拼接，见文件头说明。 */
export function buildTodayPriorities(relationship: RelationshipType, lawyerStatus: LawyerStatus): string[] {
  return [relationshipPriority(relationship), lawyerPriority(lawyerStatus), recordPriority]
}

export interface FallbackPath {
  id: string
  title: string
  description: string
  template?: string
  caveat: string
}

export const fallbackPaths: FallbackPath[] = [
  {
    id: 'self-request',
    title: '由在押人员本人提出委托要求',
    description:
      '在押犯罪嫌疑人、被告人可以自行提出委托辩护人的要求，相关办案机关应依法及时转达其委托要求。',
    template:
      '我已联系到某律师事务所。请问当事人是否可以依法提出委托律师的要求，以及相关律师或律师事务所信息应通过什么方式转达？',
    caveat: '由恋人或朋友提交律师信息，不等于已经完成正式委托，仍需由有权主体依法办理或由在押人员本人确认。',
  },
  {
    id: 'duty-lawyer',
    title: '值班律师',
    description:
      '没有辩护人的犯罪嫌疑人、被告人，可以依法获得值班律师提供的法律帮助。值班律师可以提供法律咨询、' +
      '程序选择建议、帮助申请变更强制措施以及协助申请法律援助等服务。',
    template: '请问当事人目前是否已经委托辩护律师？如果没有，是否可以告知其申请约见值班律师或申请法律援助？',
    caveat: '值班律师提供法律帮助，不应被描述为已经正式接受案件委托的辩护律师。',
  },
  {
    id: 'legal-aid',
    title: '法律援助',
    description:
      '符合条件的犯罪嫌疑人、被告人，可以依法申请法律援助；部分法定情形下，办案机关应通知法律援助机构指派律师。',
    caveat: '不得承诺法律援助一定受理，是否受理以法律援助机构的正式决定为准。',
  },
]

export interface MeetingGuidance {
  title: string
  points: string[]
}

const detentionCenterMeetingGuidance: MeetingGuidance = {
  title: '看守所羁押阶段',
  points: [
    '普通家属、未婚恋人或朋友不能把普通探视理解为辩护律师会见。',
    '辩护律师依法享有会见在押犯罪嫌疑人、被告人的权利，但具体手续和特殊案件规则应以现行法律规定为准。',
    '当前的首要任务通常是确认羁押信息和合法委托律师，而不是持续等待普通探视。',
    '不能保证家属或恋人一定能够进入看守所会见。',
    '在看守所羁押阶段，律师会见和普通家属探视不是同一制度，请优先确认律师委托、值班律师或法律援助路径。',
  ],
}

const prisonMeetingGuidance: MeetingGuidance = {
  title: '监狱服刑阶段',
  points: [
    '监狱服刑后的会见规则不同于看守所羁押期间。',
    '亲属、监护人以及其他关系人员能否申请会见，需要依据现行法律和具体监狱公开规定判断。',
    '未婚恋人并非全国范围内绝对不能申请，也不能保证一定能够批准。',
    '建议查询具体监狱的官方会见对象、预约方式、材料要求和审批规则。',
    '未婚恋人是否可以申请会见，可能取决于具体监狱的现行规定和审批结果，请以该监狱公开规则及正式答复为准。',
  ],
}

const bailMeetingGuidance: MeetingGuidance = {
  title: '取保候审或监视居住期间',
  points: [
    '取保候审或监视居住期间，当事人通常不处于羁押状态，本页面的看守所/监狱会见说明不适用。',
    '仍建议尽快联系律师，了解案件所处阶段及需要遵守的具体要求。',
  ],
}

/** 看守所与监狱的会见/探视规则不得混为一谈，按羁押阶段返回不同说明；取保/不清楚阶段单独处理。 */
export function getMeetingGuidance(stage: CustodyStage): MeetingGuidance {
  if (stage === 'serving-sentence') {
    return prisonMeetingGuidance
  }
  if (stage === 'bail-or-surveillance') {
    return bailMeetingGuidance
  }
  if (stage === 'unknown') {
    return {
      title: '案件阶段尚不清楚',
      points: [
        '看守所羁押期间与监狱服刑期间的会见规则完全不同，建议先确认当事人目前处于哪个阶段。',
        '可以通过办案机关的书面通知、家属询问或委托律师了解确切阶段后，再参考对应的会见说明。',
      ],
    }
  }
  return detentionCenterMeetingGuidance
}

export const fraudWarnings: string[] = [
  '声称认识内部人员，可以直接"捞人"',
  '保证取保、撤案、无罪或减刑',
  '要求向私人账户支付大额"关系费"',
  '拒绝提供律师姓名、律所名称或正式合同',
  '冒充办案人员、看守所或律师索要转账',
  '要求销毁、隐藏、伪造证据或统一口径',
]

/** 已有律师时的处理步骤（不评价具体律师办案能力，不生成催促律师的绝对指令）。 */
export const engagedLawyerSteps: string[] = [
  '确认律师事务所和承办律师信息',
  '保留委托手续和缴费凭证',
  '向律师核实当事人所处阶段和羁押地点',
  '询问律师是否已向办案机关提交手续',
  '不要求律师透露依法不能透露的案件信息',
  '对律师身份有疑问时，通过官方律师查询渠道核验',
]

export interface LawyerNextSteps {
  title: string
  steps: string[]
}

/** 结果页"已有律师或联系律师步骤"小节：仅在已正式委托时区分处理，其余状态统一引导先了解委托流程。 */
export function getLawyerNextSteps(lawyerStatus: LawyerStatus): LawyerNextSteps {
  if (lawyerStatus === 'formally-engaged') {
    return { title: '已委托律师后，接下来可以做什么', steps: engagedLawyerSteps }
  }
  return {
    title: '还没有正式委托律师，接下来可以做什么',
    steps: [
      lawyerPriority(lawyerStatus),
      '了解值班律师和法律援助等替代路径（见下方"联系不到近亲属时的替代路径"）。',
      '不要轻信"花钱捞人""保证取保"等承诺。',
    ],
  }
}

/** 本功能引用的候选官方来源 id，对应 legal_sources.ts 中的条目；具体条文尚待逐项核验。 */
export const legalSourceIds = ['npc-official-law', 'mps-official-rules'] as const

export const unifiedDisclaimer =
  '本指引根据用户选择的关系和案件阶段提供一般性程序信息，不构成对具体身份资格、案件情况或办理结果的认定，' +
  '也不能替代律师、法律援助机构或办案机关的正式意见。是否可以代为委托律师、需要提交哪些关系证明、能否会见或' +
  '探视，应以现行法律、具体案件阶段及有关机关的正式要求为准。'

export const contactRecordDisclaimer =
  '被记录为紧急联系人，不代表该人员自动取得监护人、近亲属、辩护委托人或会见申请人的法律资格。'
