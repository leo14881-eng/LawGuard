// 刑事诉讼阶段数据
// 说明：以下阶段仅为页面信息分类，用于组织通俗普法内容，
// 不代表对任何具体案件的程序状态作出判断。

/** 内容审核状态：内容未经执业律师审核前必须标注"待法律复核" */
export type ReviewStatus = '待法律复核' | '已复核'

/** 刑事诉讼阶段条目 */
export interface Stage {
  /** 阶段唯一标识，用于路由与跳转 */
  id: string
  /** 展示顺序 */
  order: number
  /** 阶段名称 */
  name: string
  /** 一句话通俗说明 */
  summary: string
  /** 内容审核状态 */
  status: ReviewStatus
}

export const stages: Stage[] = [
  {
    id: 'taken-or-summoned',
    order: 1,
    name: '被带走或被传唤后',
    summary: '了解被带走、传唤或采取强制措施后，一般应知晓的基本权利与注意事项。',
    status: '待法律复核',
  },
  {
    id: 'interrogation',
    order: 2,
    name: '讯问过程中',
    summary: '了解讯问环节的一般程序常识，以及可以关注的权利要点。',
    status: '待法律复核',
  },
  {
    id: 'document-signing',
    order: 3,
    name: '核对和签署文书时',
    summary: '了解核对笔录、签署法律文书前，可以留意的一般性事项。',
    status: '待法律复核',
  },
  {
    id: 'prosecution-review',
    order: 4,
    name: '审查起诉阶段',
    summary: '了解案件进入检察机关审查起诉阶段的一般程序常识。',
    status: '待法律复核',
  },
  {
    id: 'trial',
    order: 5,
    name: '法院审判阶段',
    summary: '了解法院审判阶段的一般程序常识与当事人可关注的权利要点。',
    status: '待法律复核',
  },
  {
    id: 'post-verdict',
    order: 6,
    name: '判决后及社区矫正阶段',
    summary: '了解判决后申诉、执行及社区矫正相关的一般程序常识。',
    status: '待法律复核',
  },
]
