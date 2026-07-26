/**
 * 本地全文搜索索引数据源（BL-003-1）。
 *
 * 设计原则：
 * - 索引条目全部来自项目内已发布的静态数据（stages.ts / rightsGuide.ts /
 *   legal_sources.ts）与各页面已使用的说明文案，不新增任何法律事实、条文
 *   或期限（见 LAWGUARD_SOT.md P0）；诉讼阶段与权利指引条目的 `status`
 *   字段直接复用来源数据的核验状态，不在本文件重新判断或篡改。
 * - 仅在浏览器本地对该数组做字符串匹配，不请求任何后端接口，索引随前端
 *   静态资源一起构建、分发。
 * - 每个条目对应一个已存在的路由，用于搜索结果的跳转；不新增新的页面。
 */

import { stages, type ReviewStatus } from './stages'
import { rightsGuide } from './rightsGuide'
import { legalSources } from './legal_sources'

/** 搜索结果分类标签，仅用于结果列表展示分组，不代表法律分类 */
export type SearchItemCategory = '诉讼阶段' | '权利指引' | '法律来源' | '页面'

/** 单条可搜索索引条目 */
export interface SearchItem {
  /** 索引条目唯一标识 */
  id: string
  /** 标题：搜索结果列表中加粗展示，参与关键词匹配与高亮 */
  title: string
  /** 摘要/内容：搜索结果列表中的说明文字，参与关键词匹配与高亮 */
  summary: string
  /** 结果分类标签 */
  category: SearchItemCategory
  /** 内容审核状态；仅诉讼阶段/权利指引条目提供，页面级条目不适用 */
  status?: ReviewStatus
  /** 跳转目标路由的 name（对应 router/index.ts 中的路由名称） */
  routeName: string
  /** 跳转目标路由的 :id 动态参数；不需要参数的路由留空 */
  routeId?: string
  /** 补充可搜索关键词，不在结果中展示，仅用于扩大匹配范围 */
  keywords?: string[]
}

/** 诉讼阶段：每个阶段一条索引，跳转到对应阶段详情页 */
const stageItems: SearchItem[] = stages.map((stage) => ({
  id: `stage-${stage.id}`,
  title: stage.name,
  summary: stage.summary,
  category: '诉讼阶段',
  status: stage.status,
  routeName: 'stage-detail',
  routeId: stage.id,
}))

/** 权利指引：每个阶段一条索引，跳转到对应权利指引详情页 */
const rightsGuideItems: SearchItem[] = rightsGuide.map((entry) => ({
  id: `rights-${entry.id}`,
  title: entry.title,
  summary: entry.summary,
  category: '权利指引',
  status: entry.status,
  routeName: 'rights-guide-detail',
  routeId: entry.id,
  keywords: entry.keyRights,
}))

/** 法律来源候选记录：跳转到统一的法律来源与版本记录页面 */
const legalSourceItems: SearchItem[] = legalSources.map((source) => ({
  id: `legal-source-${source.id}`,
  title: source.title,
  summary: source.explanation,
  category: '法律来源',
  routeName: 'legal-sources',
}))

/** 静态页面：标题与摘要沿用各页面已使用的 PageHeader / 首页文案，不新增说明性表述 */
const pageItems: SearchItem[] = [
  {
    id: 'page-home',
    title: '首页',
    summary:
      'LawGuard 是面向刑事案件当事人及家属的纯公益应急导航平台，提供基于官方法律依据的程序导航、权利指引、文书核对和官方救济渠道。',
    category: '页面',
    routeName: 'home',
    keywords: ['法护', 'LawGuard'],
  },
  {
    id: 'page-stages',
    title: '刑事诉讼阶段导航',
    summary: '以下六个阶段仅为页面信息分类，用于组织通俗普法内容，不代表对任何具体案件的程序状态作出判断。',
    category: '页面',
    routeName: 'stages',
  },
  {
    id: 'page-rights-guide',
    title: '权利指引',
    summary: '按诉讼阶段了解当事人一般享有哪些合法权利，帮助家属了解可以关注的权利要点。',
    category: '页面',
    routeName: 'rights-guide',
  },
  {
    id: 'page-documents',
    title: '文书核对清单',
    summary: '核对和签署法律文书是刑事诉讼中的重要环节，提供一般性核对方法框架。',
    category: '页面',
    routeName: 'documents',
  },
  {
    id: 'page-official-channels',
    title: '官方救济渠道',
    summary: '以下为一般性官方渠道说明与入口占位，具体链接与联系方式在核验前不作为正式官方地址展示。',
    category: '页面',
    routeName: 'official-channels',
    keywords: ['12348', '12309'],
  },
  {
    id: 'page-emergency-guide',
    title: '被羁押后紧急行动指引',
    summary: '家人、恋人或朋友突然被羁押，不知道谁可以委托律师？根据关系和案件状态生成下一步行动清单。',
    category: '页面',
    routeName: 'emergency-guide',
  },
  {
    id: 'page-interactive-navigator',
    title: '交互式个人处境导航工具',
    summary: '回答一个简单问题，快速定位到当前所处诉讼阶段对应的说明与权利指引入口，仅作为入口参考，不对具体案件作出判断。',
    category: '页面',
    routeName: 'interactive-navigator',
  },
  {
    id: 'page-legal-sources',
    title: '法律来源与版本记录',
    summary: '本页面记录法护内容对应的法律依据来源、版本与核验状态，未完成核验的内容不会标注为已核验。',
    category: '页面',
    routeName: 'legal-sources',
  },
  {
    id: 'page-about',
    title: '关于法护 LawGuard',
    summary: '法护（LawGuard）是免费、公益、独立、非商业的刑事诉讼权利普法平台，不接受个案委托，不代理案件。',
    category: '页面',
    routeName: 'about',
  },
  {
    id: 'page-disclaimer',
    title: '使用边界说明',
    summary: '本平台提供的是一般性、通俗化的普法信息，不构成针对任何具体案件的法律意见。',
    category: '页面',
    routeName: 'disclaimer',
  },
  {
    id: 'page-privacy',
    title: '隐私说明',
    summary: 'LawGuard 不要求注册、不收集用户身份信息，本页说明具体的隐私保护做法。',
    category: '页面',
    routeName: 'privacy',
  },
]

/** 完整本地搜索索引：合并诉讼阶段、权利指引、法律来源与静态页面条目 */
export const searchItems: SearchItem[] = [
  ...stageItems,
  ...rightsGuideItems,
  ...legalSourceItems,
  ...pageItems,
]
