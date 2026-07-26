// 权利指引数据
//
// 与「诉讼阶段」模块的区别（对应本次任务"拆分两个模块"要求）：
// - 诉讼阶段（stages.ts）说明"案件现在走到哪个程序环节、一般会发生什么"；
// - 权利指引（本文件）说明"这个阶段当事人一般享有哪些合法权利"，不重复
//   描述程序流程本身。
//
// 为方便家属对照查看，权利指引沿用与诉讼阶段相同的 6 个阶段划分作为
// 条目 id，但页面、路由、内容完全独立维护，不共用同一个视图组件。
//
// 内容均为一般性、审慎表述，尚未经过执业律师逐条核验，一律视为"待法律
// 复核"，不引用具体法律条文编号、法定期限或具体办案流程（见
// LAWGUARD_SOT.md P0）。

import type { ReviewStatus } from './stages'

/** 单项权利说明 */
export interface RightItem {
  /** 权利名称 */
  title: string
  /** 一般性说明 */
  description: string
}

/** 权利指引条目 */
export interface RightsGuideEntry {
  /** 条目唯一标识，与 stages.ts 中同名阶段 id 对应，便于家属对照查看 */
  id: string
  /** 展示顺序 */
  order: number
  /** 标题 */
  title: string
  /** 一句话摘要 */
  summary: string
  /** 内容审核状态 */
  status: ReviewStatus
  /** 关键结论：这一阶段最需要知道的几条权利（简要列表） */
  keyRights: string[]
  /** 正文：逐条展开的权利说明 */
  rightsDetail: RightItem[]
  /** 下一步：如何关注或行使这些权利 */
  howToExercise: string[]
  /** 关联的官方法律来源候选 id，对应 `legal_sources.ts` 中的条目 */
  legalSourceIds: string[]
}

export const rightsGuide: RightsGuideEntry[] = [
  {
    id: 'taken-or-summoned',
    order: 1,
    title: '被带走或被传唤阶段的一般性权利',
    summary: '了解在被带走、传唤或采取强制措施后，当事人及家属一般可以关注的权利要点。',
    status: '待法律复核',
    keyRights: [
      '当事人通常有权知晓办案机关身份及采取措施的依据。',
      '符合法定情形时，家属通常应被告知相关强制措施信息。',
      '当事人及其近亲属通常可以依法委托辩护人。',
    ],
    rightsDetail: [
      {
        title: '知情权',
        description:
          '当事人及家属通常有权了解办案机关身份、采取的措施类型及依据，具体告知方式以现行法律规定为准。',
      },
      {
        title: '委托辩护人的权利',
        description:
          '当事人及其近亲属、监护人通常可以依法委托辩护人，具体委托流程及材料要求以律师事务所及办案机关的现行要求为准。',
      },
      {
        title: '人身权利保障',
        description: '当事人在被采取强制措施期间的人身权利依法受到保障，具体保障方式以现行法律规定为准。',
      },
    ],
    howToExercise: [
      '尽快确认办案机关信息并核对相关法律文书。',
      '了解并推进委托辩护人的流程，可参考「被羁押后紧急行动指引」。',
      '如认为权利未得到保障，可通过官方渠道依法反映。',
    ],
    legalSourceIds: ['npc-official-law', 'mps-official-rules'],
  },
  {
    id: 'interrogation',
    order: 2,
    title: '讯问阶段的一般性权利',
    summary: '了解讯问过程中当事人一般可以关注的权利要点。',
    status: '待法律复核',
    keyRights: [
      '当事人对与本案无关的问题通常有权拒绝回答。',
      '当事人通常有权要求核对讯问笔录内容是否准确。',
      '符合条件时，当事人通常可以获得辩护人或值班律师提供的法律帮助。',
    ],
    rightsDetail: [
      {
        title: '程序性权利',
        description: '当事人在讯问过程中依法享有相关程序性权利，具体范围以现行法律规定为准。',
      },
      {
        title: '核对笔录的权利',
        description:
          '当事人对讯问形成的笔录，通常可以要求核对内容是否准确，如有异议可以要求更正或说明，具体方式以现行法律规定为准。',
      },
      {
        title: '获得法律帮助的权利',
        description: '符合条件的当事人依法可以获得辩护人或值班律师提供的法律帮助，具体范围以现行法律规定为准。',
      },
    ],
    howToExercise: [
      '讯问结束后，尽量了解笔录核对与签署的基本情况。',
      '关注是否已委托辩护人或联系值班律师。',
      '如认为讯问过程存在问题，可通过官方渠道依法反映。',
    ],
    legalSourceIds: ['npc-official-law', 'mps-official-rules'],
  },
  {
    id: 'document-signing',
    order: 3,
    title: '核对与签署文书阶段的一般性权利',
    summary: '了解核对和签署法律文书时，当事人一般可以关注的权利要点。',
    status: '待法律复核',
    keyRights: [
      '当事人通常有权在签署前核对文书记载内容是否准确。',
      '对文书内容有异议时，当事人通常可以要求说明或更正。',
      '当事人通常有权持有依法应当交付的文书副本。',
    ],
    rightsDetail: [
      {
        title: '核对权',
        description: '当事人在签署法律文书前，通常可以逐项核对姓名、案号、时间、地点等基本信息是否准确。',
      },
      {
        title: '异议表达权',
        description: '对文书记载内容有异议的，当事人通常可以要求说明或更正，具体方式以现行法律规定和办案机关实际操作为准。',
      },
      {
        title: '获取文书副本',
        description: '依法应当交付当事人的文书副本，当事人通常有权持有并妥善保管。',
      },
    ],
    howToExercise: [
      '签署文书前，参考「文书核对清单」页面进行基础核对。',
      '如有疑问，建议先咨询律师后再签署。',
      '妥善保管已签署文书的副本。',
    ],
    legalSourceIds: ['npc-official-law'],
  },
  {
    id: 'prosecution-review',
    order: 4,
    title: '审查起诉阶段的一般性权利',
    summary: '了解案件进入检察机关审查起诉阶段后，当事人一般可以关注的权利要点。',
    status: '待法律复核',
    keyRights: [
      '当事人及其辩护人通常可以依法了解案件相关情况。',
      '当事人通常有权向检察机关反映意见。',
      '符合条件的，当事人可以依法提出相关申请。',
    ],
    rightsDetail: [
      {
        title: '了解案件情况的权利',
        description: '当事人及其辩护人在审查起诉阶段通常可以依法了解案件相关情况，具体范围以现行法律规定为准。',
      },
      {
        title: '陈述与申辩权利',
        description: '当事人通常可以向检察机关就案件情况进行陈述或提出意见，具体方式以现行法律规定为准。',
      },
      {
        title: '申请权利',
        description: '符合法定情形的，当事人可以依法提出相关申请，具体条件和程序以现行法律规定为准。',
      },
    ],
    howToExercise: [
      '与辩护律师保持沟通，了解可以行使的具体权利。',
      '如需反映意见，可通过检察机关官方渠道（见「官方渠道」页面）。',
      '如尚未委托律师，建议尽快了解委托流程。',
    ],
    legalSourceIds: ['npc-official-law'],
  },
  {
    id: 'trial',
    order: 5,
    title: '法院审判阶段的一般性权利',
    summary: '了解案件进入法院审理阶段后，当事人一般可以关注的权利要点。',
    status: '待法律复核',
    keyRights: [
      '当事人通常享有获得辩护的权利。',
      '当事人在法庭审理中通常享有陈述、质证等权利。',
      '当事人通常有权知晓判决结果及理由。',
    ],
    rightsDetail: [
      {
        title: '获得辩护的权利',
        description: '当事人在审判阶段依法享有获得辩护人辩护的权利，具体范围以现行法律规定为准。',
      },
      {
        title: '参与庭审的权利',
        description:
          '当事人在法庭审理中通常享有陈述意见、对证据进行质证等程序性权利，具体范围以现行法律规定为准。',
      },
      {
        title: '知悉判决的权利',
        description: '当事人依法有权知晓判决结果及送达的判决文书内容。',
      },
    ],
    howToExercise: [
      '与辩护律师保持沟通，了解庭审安排与需要准备的事项。',
      '关注判决文书的送达情况。',
      '如对判决有异议，建议尽快咨询执业律师了解救济途径。',
    ],
    legalSourceIds: ['npc-official-law', 'supreme-court-official'],
  },
  {
    id: 'post-verdict',
    order: 6,
    title: '判决后及社区矫正阶段的一般性权利',
    summary: '了解判决生效后及社区矫正阶段，当事人一般可以关注的权利要点。',
    status: '待法律复核',
    keyRights: [
      '对判决不服的，当事人通常依法享有申诉等救济权利。',
      '符合条件适用社区矫正的，当事人依法享有相应权利保障。',
      '当事人通常有权了解执行的具体安排。',
    ],
    rightsDetail: [
      {
        title: '申诉等救济权利',
        description: '当事人对已生效判决不服的，依法可以通过法定途径提出申诉，具体条件与程序以现行法律规定为准。',
      },
      {
        title: '社区矫正期间的权利保障',
        description:
          '依法适用社区矫正的当事人，其合法权利依法受到保障，具体内容以现行法律规定及社区矫正机构的正式告知为准。',
      },
      {
        title: '知悉执行安排的权利',
        description: '当事人通常有权了解判决的具体执行安排，具体告知方式以现行规定为准。',
      },
    ],
    howToExercise: [
      '确认判决生效情况及执行安排。',
      '如需申诉，建议尽快咨询执业律师了解程序和期限。',
      '涉及社区矫正的，主动了解并配合社区矫正机构的正式要求。',
    ],
    legalSourceIds: ['npc-official-law', 'supreme-court-official'],
  },
]

export function getRightsGuideById(id: string): RightsGuideEntry | undefined {
  return rightsGuide.find((entry) => entry.id === id)
}
