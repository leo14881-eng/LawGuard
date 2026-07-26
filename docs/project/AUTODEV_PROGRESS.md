# Auto Dev Progress

## Project Stage
LawGuard V1 —— Auto Dev 全自动开发循环

## Last Update
2026-07-26T11:40:00

## Last Commit
（本次人工会话尚未提交，见下方"P0.2 收尾"记录；此前一次 Auto Dev 自动提交为
task-003: feat: 首页新增 QuickNavCard 快速导航区块并嵌入 HomeView，链接至 /official-chan）

## Completed Tasks
- task-001: 在法律来源页面完善官方来源展示顺序与无障碍性，显示版本记录信息并复用现有组件与设计令牌
- task-002: Official Channels 页面新增官方来源与版本记录区块
- task-003: 在首页新增快速导航区块，指向 Official Channels、Legal Sources、Stages 三大入口

## Current Task
（无，等待 Planner 规划下一任务）

## Next Candidate Tasks
（无）

## Known Issues
（无）

## 功能状态表（人工维护，2026-07-26 盘点）

> **重要说明**：以上 7 个字段（Project Stage ~ Known Issues）由
> `automation/progress.py` 固定模板自动生成；下次通过
> `python automation/orchestrator.py` 成功提交新任务时，该工具会用固定模板整体
> 重写本文件，**本节及以下内容会被覆盖丢失**。这是当前 Auto Dev V1 Progress 机制
> 与本次人工功能盘点需求之间的已知缺口——本次审计未修改 `automation/progress.py`
> （属于 Auto Dev V1 架构，不在本次允许修改范围内）。建议：每次人工会话结束前，或
> 未来决定扩展 `progress.py` 支持本表结构后再解决持久化问题。状态定义见
> `CLAUDE.md`"开发前去重检查"一节：PLANNED / IN_PROGRESS / IMPLEMENTED / VERIFIED /
> BLOCKED / REJECTED。

| 功能 | 状态 | 实现位置 | 测试/验证 | 最后核验 | 备注 |
|---|---|---|---|---|---|
| 全站 Trust Banner（公益与安全声明） | VERIFIED | `web/src/components/TrustBanner.vue`，接入 HomeView（full）/StagesView/DocumentsView/OfficialChannelsView/AboutView/EmergencyGuideView（compact）/Stages/Documents/LegalSources/EmergencyGuideView（print） | 单测 4 项通过（`components/__tests__/TrustBanner.test.ts`）；Playwright 截图人工检查首屏可见、打印模拟正常 | 2026-07-26 | 首页只保留 full 版，未叠加 compact（避免重复堆砌） |
| 首页首屏公益安全提示 | VERIFIED | `HomeView.vue`（Header 与 Hero 之间） | 同上，Playwright 截图确认首屏可见 | 2026-07-26 | — |
| 核心页面 Compact 公益提示 | VERIFIED | Stages/Documents/OfficialChannels/About 四页 | 同上 | 2026-07-26 | 法律来源页仅接入 print 版，未接入 compact（不在原始页面清单内） |
| 打印页面第一页顶部公益/防诈骗声明 | VERIFIED | `TrustBanner.vue` variant="print"，接入 Stages/Documents/LegalSources/EmergencyGuideView | Playwright `emulateMedia('print')` 截图确认位于第一页顶部、双线黑白边框、未被移到底部 | 2026-07-26 | — |
| 关于项目页公益/隐私/防诈骗声明 | VERIFIED | `AboutView.vue`"公益与隐私声明"（17 项 ✓）、"谨防诈骗"（7 项） | Playwright 截图人工检查 | 2026-07-26 | — |
| Footer 公益信息 | VERIFIED | `AppFooter.vue` footer__trust-line | Playwright 截图人工检查 | 2026-07-26 | — |
| 被羁押后紧急行动指引（整体功能） | VERIFIED | `web/src/views/EmergencyGuideView.vue` | 29 个 Vitest 单测/组件测试通过；`npm run build` 通过；Playwright 截图人工检查桌面/平板/移动端/打印 | 2026-07-26 | 路由 `/emergency-guide`；首页入口见 Hero 主按钮"开始应急导航"与"你现在需要什么？"任务卡"家人刚被带走" |
| 关系身份选择 / 羁押阶段选择 / 律师状态选择 | VERIFIED | `data/emergencyGuidance.ts` 选项数据 + `EmergencyGuideView.vue` 三步引导 | 同上 | 2026-07-26 | — |
| 自动生成紧急行动清单 | VERIFIED | `buildTodayPriorities`/`getIdentityGuidance` 等纯函数（`emergencyGuidance.ts`） | `data/__tests__/emergencyGuidance.test.ts` 覆盖 8 个场景组合 | 2026-07-26 | 简单查表/条件分支拼接，非通用规则引擎 |
| 未婚恋人/朋友/同事场景行动指引 | VERIFIED | `nonEligibleIdentityGuidance` | 同上 | 2026-07-26 | — |
| 建议寻找适格联系人 | VERIFIED | `suggestedContactOrder` | 同上 | 2026-07-26 | 仅非近亲属/监护人关系时展示 |
| 联系不到近亲属时的替代路径（本人委托/值班律师/法律援助） | VERIFIED | `fallbackPaths` | 同上，断言 3 条路径均存在且含 caveat | 2026-07-26 | 值班律师/法律援助具体来源类别尚待 P0.2 确认，见下方"法律来源"备注 |
| 看守所羁押与监狱服刑差异化说明 | VERIFIED | `getMeetingGuidance` | 同上，覆盖看守所/监狱/取保/不清楚四种阶段 | 2026-07-26 | — |
| 防诈骗行动提醒（紧急指引内） | VERIFIED | `fraudWarnings` | 同上 | 2026-07-26 | — |
| 联系人本地存储（增删改查、清除、持久化） | VERIFIED | `composables/useEmergencyContacts.ts` | `composables/__tests__/useEmergencyContacts.test.ts` 5 项通过 | 2026-07-26 | 仅 localStorage，不上传服务器，key `lawguard.emergencyContacts.v1` |
| 手机号默认脱敏 | VERIFIED | `utils/phoneMask.ts` | `utils/__tests__/phoneMask.test.ts` 3 项通过 | 2026-07-26 | 打印/展示默认脱敏，用户可勾选显示完整号码 |
| 浏览器打印 / Print CSS | VERIFIED | `PrintPageButton.vue`/`PrintFooter.vue`/`style.css` `@media print` | Playwright `emulateMedia('print')` 截图人工检查（无自动化断言，jsdom 不便模拟打印渲染） | 2026-07-26 | 未引入服务端 PDF 生成 |
| 中文 document.title / html lang="zh-CN" | VERIFIED | `index.html`、`PrintPageButton.vue` 的 `pageTitle` prop | Playwright 脚本验证打印前后 title 切换与恢复正确 | 2026-07-26 | — |
| 法律来源核验（紧急指引相关 10 项规则） | IMPLEMENTED（内容为一般性表述，标注"待法律复核"） | `data/legal_sources.ts` 新增 `mps-official-rules`；复用既有 `npc-official-law` | 未经执业律师逐条核验 | 2026-07-26（待核验） | 值班律师/法律援助的具体来源类别（司法部相关规章）尚未在 P0.2 允许清单中确认，措辞已保守处理，未归为已核验 |
| 分享 LawGuard（navigator.share/复制链接/二维码/分享图片/OG/SEO 全套） | PLANNED | — | — | — | 本次审计明确不开发；见新对话中的独立需求，尚未开始编码 |
| 本地全文搜索（V1 功能范围第 7 项） | PLANNED | — | — | — | 仅 `AppEmptyState.vue` 注释提及"未来的本地全文搜索功能"，无实际实现 |
| 首页信息层级重设计 | VERIFIED | `HomeView.vue`/`HeroSection.vue`/`TrustBanner.vue`/`QuickNavCard.vue`/`AppFooter.vue` | 29 个前端测试通过；`npm run build` 通过；桌面 1440/平板 768/移动 375 三档 Playwright 截图确认无横向滚动、标题无孤字换行、Hero 在平板正确切换上下布局 | 2026-07-26 | Trust Banner 由大黄框改为紧凑单行+可展开；Hero 改左右两栏；新增 4 张任务卡替代原快速导航；移除首页重复的紧急指引 CTA 大卡片 |
| 全站 Design System 审计与组件统一 | VERIFIED（审计范围内的 10 项发现已处理完成；未展开的部分见备注） | 审计发现见本次会话记录；修复：`style.css` 新增 `--header-height` 与全局 `.lead` 类、删除零引用的 `FeatureCard.vue`、`StageCard.vue`/`ChannelCard.vue` 改用 `.card--interactive` 与既有 Token、`StagesView`/`DocumentsView`/`OfficialChannelsView`/`AboutView`/`EmergencyGuideView`/`PrivacyView` 统一改用 `PageHeader`、`AboutView` 免责声明与 `LegalDisclaimer` 合并去重、`NoticeBanner` 纯状态说明由 caution 改为 info | `npm run build`/`npm run test`（29 项）通过；桌面/移动端 6 个页面 Playwright 截图人工检查 | 2026-07-26 | 未做的部分（保留为待办，未强行推进）：未对每种"页面类型"建立独立骨架模板文件，仅在 LAWGUARD_SOT.md 12.3 节做文字规范；ComingSoonView 的少量魔法数（`80px 20px`）未处理，风险低、未纳入本轮 |
| ComingSoon 占位页 | REJECTED（已删除，功能被诉讼阶段详情页取代） | 原 `web/src/views/ComingSoonView.vue` 与 `/coming-soon` 路由已删除，`robots.txt` 同步移除对应 Disallow 规则 | `npm run build`/`npm run test` 通过；Playwright 39 项页面×视口检查无残留引用 | 2026-07-26 | 原"魔法数 `80px 20px`"已知问题随文件删除一并消除 |
| 诉讼阶段详情页 | VERIFIED | `web/src/views/StageDetailView.vue`（路由 `/stages/:id`）+ `data/stages.ts` 扩展字段（`whatIsThisStage`/`whatGenerallyHappens`/`familyFocus`/`generalRights`/`nextSteps`/`legalSourceIds`）；`StageCard.vue` 改为跳转详情页 | `vue-tsc -b`/`npm run test`（29 项）/`npm run build` 通过；Playwright 桌面/平板/移动三档截图人工检查 6 个阶段详情、返回链接、打印按钮 | 2026-07-26 | 内容为一般性表述，统一标注"待法律复核"，不引用具体法条编号/期限，官方来源沿用 `legal_sources.ts` 既有"待核验"条目 |
| 权利指引（独立模块） | VERIFIED | 新增 `data/rightsGuide.ts`、`components/RightsGuideCard.vue`、`views/RightsGuideView.vue`（`/rights-guide`）、`views/RightsGuideDetailView.vue`（`/rights-guide/:id`）；与"诉讼阶段"模块页面/路由/内容完全独立，两侧详情页互相链接但不重复正文 | 同上 | 2026-07-26 | 修复历史遗留问题：`AppHeader` 导航"权利指引"此前误指向 `/stages`，`QuickNavCard`"想了解当前权利"此前指向不存在的 `/rights-guide`（悬空链接），均已修复为正确路由 |
| 统一详情页模板 | VERIFIED | 新增 `components/DetailPageLayout.vue`（PageHeader→关键结论→正文→下一步→官方来源→打印→边界说明→返回），供诉讼阶段详情与权利指引详情复用 | 同上 | 2026-07-26 | — |
| 路由懒加载 loading 状态 | VERIFIED | `App.vue` 的 `<RouterView>` 改为 `v-slot` + `<Suspense>`，`fallback` 复用既有 `AppLoading.vue` | Playwright 检查无控制台报错；人工验证刷新/切页不再出现内容区空白导致 Footer 瞬间贴近 Header 的跳动 | 2026-07-26 | 对应 P3.4"页面须覆盖 loading 状态"要求，此前遗漏 |
| 首页"使用边界"窄栏孤字换行 | VERIFIED | `HomeView.vue` `.boundary__lead` 移除仅适用于桌面双栏布局的 `max-width:320px`，改用 `text-wrap: balance` | Playwright 桌面/平板截图确认不再出现"…不能提供 / 什么。"两字孤行 | 2026-07-26 | — |
| 紧急指引第一步提示语拆词 | VERIFIED | `EmergencyGuideView.vue` "不要混用"用 `.text-keep` 包裹，避免"不/要混用"跨行拆词 | 同上 | 2026-07-26 | — |

### 重复实现检查结果（本次设计审计，2026-07-26）

发现并已修复：`FeatureCard.vue`（零引用死组件，已删除）、`StageCard`/`FeatureCard`
自写的 `.card:hover` 与全局 `.card--interactive` 逻辑重复（已改用后者）、`.lead`
样式在 5 个文件重复声明（已收编为全局类）、`AboutView` 的"非官方与公益性质"
NoticeBanner 与 `LegalDisclaimer` 内容重叠（已合并）。
`TrustBanner`（公益声明）、`NoticeBanner`（通用提示）、`LegalDisclaimer`（P-1 非法律
意见声明）三者职责已在 LAWGUARD_SOT.md 12.2 节明确，未再发现混用。当前所有路由均
对应实际存在且启用的页面组件，容器宽度（`--max-width: 1200px`）与响应式断点
（640/960px）全站统一，未发现例外。
SEO 相关信息（title/description/OpenGraph/canonical/robots/sitemap）目前只有基础
`<title>`/`<meta description>`，其余项均为 `PLANNED`，尚未散落形成冲突（因为尚未存在）。
