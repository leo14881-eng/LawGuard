/**
 * 各路由的页面级 SEO 内容（title / description）。
 *
 * 与 automation 的法律内容治理原则一致：这里只写产品定位与页面用途的说明性文案，
 * 不涉及具体法律条文/条文编号/期限等法律事实，不受 P0 来源核验流程约束；但同样
 * 不得使用"保证解决""专业律师在线"等营销/商业化表达（见 LAWGUARD_SOT.md P-1）。
 *
 * key 对应 router/index.ts 中各路由的 name。
 */
export interface RouteSeoEntry {
  title: string
  description: string
  /** 为 true 时输出 `<meta name="robots" content="noindex, nofollow">`，用于 404 等不应被搜索引擎收录的页面 */
  noindex?: boolean
}

export const routeSeoMap: Record<string, RouteSeoEntry> = {
  home: {
    title: 'LawGuard｜刑事案件公益应急导航平台',
    description:
      'LawGuard 是面向刑事案件当事人及家属的纯公益应急导航平台，提供基于官方法律依据的程序导航、' +
      '权利指引、文书核对和官方救济渠道。永久免费，不主动联系用户，不收集个人信息。',
  },
  stages: {
    title: '刑事诉讼阶段导航｜LawGuard',
    description: '了解刑事拘留、逮捕、审查起诉、法院审理和监狱服刑等阶段的一般程序和当前进展。',
  },
  'stage-detail': {
    title: '诉讼阶段详情｜LawGuard',
    description: '查看具体诉讼阶段的一般程序说明、家属关注要点、下一步建议和官方法律依据。',
  },
  'rights-guide': {
    title: '权利指引｜LawGuard',
    description: '按诉讼阶段了解当事人一般享有哪些合法权利，帮助家属了解可以关注的权利要点。',
  },
  'rights-guide-detail': {
    title: '权利指引详情｜LawGuard',
    description: '查看具体诉讼阶段的一般性权利说明、行使权利的建议和官方法律依据。',
  },
  documents: {
    title: '刑事法律文书核对｜LawGuard',
    description: '帮助普通用户识别常见刑事法律文书，并核对机关、日期、阶段和基本信息。',
  },
  'official-channels': {
    title: '刑事案件官方救济渠道｜LawGuard',
    description: '查询法律援助、司法机关和其他公开官方救济渠道。',
  },
  'emergency-guide': {
    title: '家人被羁押后怎么办｜LawGuard',
    description: '根据案件阶段、与当事人的关系和律师状态，生成一般性紧急行动清单。',
  },
  about: {
    title: '关于项目｜LawGuard',
    description:
      '法护（LawGuard）是免费、公益、独立、非商业的刑事诉讼权利普法平台，面向刑事案件当事人及其家属，' +
      '帮助了解一般性法定权利、基本程序、文书核对方法和官方救济渠道。',
  },
  privacy: {
    title: '隐私说明｜LawGuard',
    description: 'LawGuard 不要求注册、不收集用户身份信息，本页说明具体的隐私保护做法。',
  },
  disclaimer: {
    title: '使用边界说明｜LawGuard',
    description: '本平台提供的是一般性、通俗化的普法信息，不构成针对任何具体案件的法律意见。',
  },
  'legal-sources': {
    title: '法律来源与版本记录｜LawGuard',
    description: '本页面记录法护内容对应的法律依据来源、版本与核验状态，未完成核验的内容不会标注为已核验。',
  },
  'not-found': {
    title: '页面不存在｜LawGuard',
    description: '你访问的页面不存在，可能是链接有误或页面已经调整。',
    noindex: true,
  },
}

export const defaultRouteSeo: RouteSeoEntry = routeSeoMap.home!
