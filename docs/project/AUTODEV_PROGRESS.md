# Auto Dev Progress

## Project Stage
LawGuard V1 —— Auto Dev 全自动开发循环

## Last Update
2026-07-26T16:30:00

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
| 分享 LawGuard（navigator.share/复制链接/二维码/分享图片） | VERIFIED（本行此前长期标注 PLANNED"尚未开始编码"，与实际代码不符，本次核实后更正） | `components/SharePanel.vue`（`utils/shareCard.ts` 本地生成分享卡片图片、`utils/downloadDataUrl.ts` 本地下载、`qrcode` 库本地生成二维码），已接入首页及绝大多数内容页 | `npm run build` 通过；人工核实分享/复制链接/二维码/下载图片四个入口在多个页面正常工作 | 2026-07-26 | 全部本地生成，不调用第三方在线接口，不采集分享行为数据 |
| SEO 基础设施（title/description/OG/Twitter/canonical/JSON-LD/robots/sitemap） | VERIFIED（同上，此前误标 PLANNED） | `utils/seo.ts`（`applyRouteSeo` 由 `router.afterEach` 驱动）、`data/seo.ts`（各路由 title/description）、`composables/useJsonLd.ts`（首页 `WebSite` 结构化数据）、`vite.config.ts` 的 `siteFilesPlugin`（`VITE_SITE_URL` 配置后生成 `robots.txt` 的 Sitemap 行与 `sitemap.xml`） | `npm run build` 通过；设置 `VITE_SITE_URL` 后人工核实 `dist/sitemap.xml`/`dist/robots.txt` 内容正确 | 2026-07-26 | — |
| 详情页动态 SEO（诉讼阶段详情/权利指引详情） | VERIFIED | 新增 `utils/seo.ts` 的 `applyPageSeoOverride()`，`StageDetailView.vue`/`RightsGuideDetailView.vue` 在 `watch(stage/entry, ..., {immediate:true})` 里用具体条目标题/摘要覆盖 `routeSeoMap` 里 `stage-detail`/`rights-guide-detail` 的通用兜底文案 | Playwright 人工核实 `/stages/trial` 与 `/stages/interrogation` 等不同详情页的 `document.title`/`og:title`/`description` 各不相同、准确对应当前条目 | 2026-07-26 | 此前 6 个诉讼阶段详情页、6 个权利指引详情页分别共用同一条通用标题，搜索结果/分享标题无法区分具体条目 |
| sitemap.xml 路由覆盖 | VERIFIED | `vite.config.ts` 的 `PUBLIC_ROUTES` 补齐 `/legal-sources`、`/disclaimer`、`/rights-guide`，并新增 `STAGE_IDS`/`RIGHTS_GUIDE_IDS` 生成全部 12 个详情页 URL（`/stages/:id`、`/rights-guide/:id`） | 设置 `VITE_SITE_URL` 构建后人工核实 `dist/sitemap.xml` 含 22 条 URL，均为绝对地址 | 2026-07-26 | 此前遗漏 3 个静态页面与全部 12 个详情页；`STAGE_IDS`/`RIGHTS_GUIDE_IDS` 需与 `data/stages.ts`/`data/rightsGuide.ts` 手动保持同步（未直接 import，避免 `vite.config.ts` 所属 `tsconfig.node.json`(nodenext) 与 `src/` 所属 `tsconfig.app.json`(bundler) 的模块解析规则冲突导致 `vue-tsc -b` 报错），已在代码注释中说明 |
| 本地全文搜索（V1 功能范围第 7 项） | PLANNED | — | — | — | 仅 `AppEmptyState.vue` 注释提及"未来的本地全文搜索功能"，无实际实现 |
| 首页信息层级重设计 | VERIFIED | `HomeView.vue`/`HeroSection.vue`/`TrustBanner.vue`/`QuickNavCard.vue`/`AppFooter.vue` | 29 个前端测试通过；`npm run build` 通过；桌面 1440/平板 768/移动 375 三档 Playwright 截图确认无横向滚动、标题无孤字换行、Hero 在平板正确切换上下布局 | 2026-07-26 | Trust Banner 由大黄框改为紧凑单行+可展开；Hero 改左右两栏；新增 4 张任务卡替代原快速导航；移除首页重复的紧急指引 CTA 大卡片 |
| 全站 Design System 审计与组件统一 | VERIFIED（审计范围内的 10 项发现已处理完成；未展开的部分见备注） | 审计发现见本次会话记录；修复：`style.css` 新增 `--header-height` 与全局 `.lead` 类、删除零引用的 `FeatureCard.vue`、`StageCard.vue`/`ChannelCard.vue` 改用 `.card--interactive` 与既有 Token、`StagesView`/`DocumentsView`/`OfficialChannelsView`/`AboutView`/`EmergencyGuideView`/`PrivacyView` 统一改用 `PageHeader`、`AboutView` 免责声明与 `LegalDisclaimer` 合并去重、`NoticeBanner` 纯状态说明由 caution 改为 info | `npm run build`/`npm run test`（29 项）通过；桌面/移动端 6 个页面 Playwright 截图人工检查 | 2026-07-26 | 未做的部分（保留为待办，未强行推进）：未对每种"页面类型"建立独立骨架模板文件，仅在 LAWGUARD_SOT.md 12.3 节做文字规范；ComingSoonView 的少量魔法数（`80px 20px`）未处理，风险低、未纳入本轮 |
| ComingSoon 占位页 | REJECTED（已删除，功能被诉讼阶段详情页取代） | 原 `web/src/views/ComingSoonView.vue` 与 `/coming-soon` 路由已删除，`robots.txt` 同步移除对应 Disallow 规则 | `npm run build`/`npm run test` 通过；Playwright 39 项页面×视口检查无残留引用 | 2026-07-26 | 原"魔法数 `80px 20px`"已知问题随文件删除一并消除 |
| 诉讼阶段详情页 | VERIFIED | `web/src/views/StageDetailView.vue`（路由 `/stages/:id`）+ `data/stages.ts` 扩展字段（`whatIsThisStage`/`whatGenerallyHappens`/`familyFocus`/`generalRights`/`nextSteps`/`legalSourceIds`）；`StageCard.vue` 改为跳转详情页 | `vue-tsc -b`/`npm run test`（29 项）/`npm run build` 通过；Playwright 桌面/平板/移动三档截图人工检查 6 个阶段详情、返回链接、打印按钮 | 2026-07-26 | 内容为一般性表述，统一标注"待法律复核"，不引用具体法条编号/期限，官方来源沿用 `legal_sources.ts` 既有"待核验"条目 |
| 权利指引（独立模块） | VERIFIED | 新增 `data/rightsGuide.ts`、`components/RightsGuideCard.vue`、`views/RightsGuideView.vue`（`/rights-guide`）、`views/RightsGuideDetailView.vue`（`/rights-guide/:id`）；与"诉讼阶段"模块页面/路由/内容完全独立，两侧详情页互相链接但不重复正文 | 同上 | 2026-07-26 | 修复历史遗留问题：`AppHeader` 导航"权利指引"此前误指向 `/stages`，`QuickNavCard`"想了解当前权利"此前指向不存在的 `/rights-guide`（悬空链接），均已修复为正确路由 |
| 统一详情页模板 | VERIFIED | 新增 `components/DetailPageLayout.vue`（PageHeader→关键结论→正文→下一步→官方来源→打印→边界说明→返回），供诉讼阶段详情与权利指引详情复用 | 同上 | 2026-07-26 | — |
| 路由懒加载 loading 状态 | VERIFIED | `App.vue` 的 `<RouterView>` 改为 `v-slot` + `<Suspense>`，`fallback` 复用既有 `AppLoading.vue` | Playwright 检查无控制台报错；人工验证刷新/切页不再出现内容区空白导致 Footer 瞬间贴近 Header 的跳动 | 2026-07-26 | 对应 P3.4"页面须覆盖 loading 状态"要求，此前遗漏 |
| 首页"使用边界"窄栏孤字换行 | VERIFIED | `HomeView.vue` `.boundary__lead` 移除仅适用于桌面双栏布局的 `max-width:320px`；"不能提供什么"用 `.text-keep` 包裹（不使用 `text-wrap:balance`，理由见下方"全站正文排版统一"） | Playwright 桌面/平板截图确认不再出现"…不能提供 / 什么。"两字孤行 | 2026-07-26 | — |
| 紧急指引第一步提示语拆词 | VERIFIED | `EmergencyGuideView.vue` "不要混用"用 `.text-keep` 包裹，避免"不/要混用"跨行拆词 | 同上 | 2026-07-26 | — |
| 首屏 theme-color 深蓝闪烁（浏览器 chrome 层面，已修复但非用户反馈问题的主因） | VERIFIED | `index.html`/`site.webmanifest` 的 `theme-color`/`theme_color` 由 `#14335c` 改为 `#ffffff` | `npm run build` 通过 | 2026-07-26 | 修复了但不是根因：修完之后用户反馈刷新时依旧闪蓝，说明这只是次要因素，见下一行才是真正根因 |
| 刷新页面 Footer 提前闪现（真正根因，已修复） | VERIFIED | 根因：刷新（reload，非站内跳转）后最初 300～900ms（弱网/降速下更明显），`<RouterView v-slot="{ Component }">` 的 `Component` 还是 `undefined`（路由未解析完成），`<Suspense>` 相当于没有子节点、不会触发 pending/resolve，`<main>` 高度为 0，而 `AppFooter`（深蓝色 `#0B2545` 通栏）已渲染在其后，紧贴 Header 出现在视口顶部，内容到位后又被推到底部；只在刷新时出现是因为站内跳转时目标 chunk 通常已加载，空档极短。修复：`App.vue` 把 `<main>` 移入 `<RouterView v-slot>` 内部，用 `!Component \|\| loading` 驱动 `.main--loading`（`min-height: calc(100svh - var(--header-height))`），`Component` 为空或 `Suspense` pending 时都生效 | CDP 逐帧采样：修复前 8 个场景（dev/preview × 4 路由）均有 25～35/160+ 帧 Footer 提前出现在视口内，修复后全部为 0；Playwright 视频截帧人工复核；`npm run test:e2e` 4 项通过 | 2026-07-26 | 中途有一版基于 `Suspense` `pending`/`resolve` 事件的修复未生效（`Component` 为 `undefined` 时 Suspense 不触发这两个事件，`loading` ref 从未被设为 true），已定位并改正 |
| 首屏闪烁回归测试 | VERIFIED | `web/playwright.config.ts` + `web/e2e/first-paint-flash.spec.ts`（覆盖 `/`、`/about`、`/stages`、`/rights-guide`，先 `goto` 再 `reload` 复现真实刷新场景，断言无大面积蓝色元素、Footer 刷新早期不进入视口），`package.json` 新增 `test:e2e` 脚本与 `@playwright/test` devDependency | `npm run test:e2e` 4 项通过 | 2026-07-26 | 不影响 `npm run test`（已在 `vite.config.ts` 的 Vitest `exclude` 中排除 `e2e/**`） |
| QuickNavCard aria-label 严格等于标题 | VERIFIED | `QuickNavCard.vue` 的 `aria-label` 由"标题+描述"拼接改为直接使用 `item.title`，删除不再使用的 `ariaLabel` 字段 | `vue-tsc -b`/`npm run test`/`npm run build` 通过 | 2026-07-26 | 未改动可见文案与样式 |
| 全站正文排版统一（P0.2 收尾第二轮） | VERIFIED | 新增 Design Token `--content-width: 760px`；全局 `.prose` 工具类（统一阅读宽度/字号 16px/行高 1.8/分节间距 32px）；`/about`、`/documents`、`/official-channels`、`/privacy`、`/disclaimer`、`/legal-sources` 及 `DetailPageLayout.vue`（`/stages/:id`、`/rights-guide/:id`）统一接入；`.lead`/`.status-note`/`PageHeader__desc` 改用同一 Token；全局 `p`/`li` 改为 `text-wrap: wrap` + `overflow-wrap: break-word` + `word-break: normal`（不再用于普通正文的 `text-wrap: balance`/`pretty`，仅 h1/h2/Hero 短标题允许 balance）；`AboutView.vue` "直接访问者" 由错误包裹"主要是："改为正确包裹"直接访问者"本身 | `vue-tsc -b`/`npm run test`（29 项）/`npm run build` 通过；Playwright 对 8 个页面 × 桌面 1440/平板 768/移动 375 × fold/full 共 24 组截图人工检查，0 处横向滚动、0 处孤字/断词 | 2026-07-26 | 用户反馈"直接访问者"被拆成"直接访问"+"者主要是："，根因是 `.text-keep` 只包裹了"主要是："而未包裹"直接访问者"本身，叠加 `.lead` 640px 宽度约束；本轮同时修复标题/导语/列表/正文/提示框宽度不统一、正文与边界提示框留白过大两项问题 |
| Auto Dev Auto Fix（Validation + Review 统一 3-Attempt 自动修复） | VERIFIED | `automation/orchestrator.py`（`run_task_cycle` 重构为统一 Attempt 循环：INITIAL/VALIDATION_FIX/REVIEW_FIX 三种 Attempt 共享同一个 `MAX_ATTEMPTS=3` 计数，不会出现 Validation Retry 3 次 + Review Retry 3 次共 6 次；Validation 未通过时不调用 Review，只有 Validation 全部通过才进入 Review）；`automation/claude_runner.py` 新增 `build_validation_fix_prompt`（附带失败命令/退出码/stdout/stderr/完整验证结果/当前 Git Diff）与 `build_review_fix_prompt`（在原有 summary/blocking_issues/non_blocking_suggestions 基础上新增当前任务信息/当前 Attempt/最近一次完整 Validation 结果/当前 Git Diff）；`automation/context_loader.py` 新增 `build_diff_for_prompt`（Git Diff 过长时截断但保留文件列表，标记"[Diff 已截断]"）与 `build_validation_summary_text`；`automation/git_service.py` 的 `get_diff` 改用 `git diff --no-ext-diff --unified=3`；`automation/security.py` 新增 `detect_unsafe_fix_signal`（Claude 自报 BLOCKED/需要人工决策、敏感领域关键词、测试弱化写法三类安全边界，命中即停止不重试，不受 risk_level 影响）；`automation/orchestrator.py` 新增"无进展保护"（连续两次修复后 Git Diff 与失败信息完全相同则提前停止）；`automation/models.py` 的 `RunReport.review_attempts` 扩展为记录 prompt_type/Claude 起止时间/改动文件/failed_command/review_duration/retry_reason 等完整字段；`automation/report_writer.py` 运行报告新增"15. Attempt 记录"与"16. Attempt 总结"小节 | `python -m pytest automation/tests`（176 项通过，较升级前 162 项新增 14 项：8 项 Validation Auto Fix/无进展保护/Reviewer API 失败区分/Fix Prompt 内容断言，6 项 `detect_unsafe_fix_signal` 单测），覆盖 LOW Risk Validation FAIL→Fix→PASS→Commit、LOW Risk Validation FAIL→Fix→Review FAIL→Fix→PASS（3 Attempt 共享计数）、连续 3 次 Validation/Review FAIL 后 RETRY_EXHAUSTED、MEDIUM Risk 不重试、verdict=BLOCKED 不重试、Review API 失败不当作代码 FAIL 处理、Validation FAIL 时不调用 Review 等场景 | 2026-07-26 | 以真实失败的 task-004（QuickNavCard aria-label）与"TypeScript 类型错误导致 Build FAIL"构造的场景为原型；BLOCKED 类终止（Review 判 BLOCKED、Claude 自报需人工决策、命中敏感关键词/测试弱化写法）统一使用与 Planner 级 BLOCKED 一致的 `EXIT_SECURITY_FAILURE`；Reviewer API 失败（网络错误等）归为 `EXECUTION_FAILED`/`EXIT_GENERAL_FAILURE`，与代码 Review FAIL 区分，不做自动修复；Planner→Claude→Validation→Review→Commit→Report→Git 既有结构与 `git push` 禁令保持不变 |
| Auto Dev 仓库级单实例运行锁 | VERIFIED | 新增 `automation/run_lock.py`（`RepositoryRunLock` 类：`acquire`/`release`/`update_task`/`inspect`/`is_owned`/`archive_stale_path`，支持 `with` 上下文管理器）。**触发原因**：本次会话过程中在 `automation/` 目录下真实观察到被另一个进程并发修改的文件（最终以 commit `00ce043` 落地），证实"两个 Auto Dev 进程同时操作同一工作区"的风险不是假设。**作用域**：绑定到 `git rev-parse --show-toplevel` 规范化后的仓库根目录，不同仓库互不影响。**锁文件**：`<repo-root>/.autodev/autodev.lock`（`.gitignore` 新增 `.autodev/`），JSON 内容含 pid/process_start_time/autodev_start_time/hostname/repo_root/run_id/task_id/command/version，不写入密钥/隐私/法律业务数据。**原子获取**：`os.open(O_CREAT\|O_EXCL\|O_WRONLY)`，Windows/Linux 通用。**活跃/陈旧/损坏判定**：新增依赖 `psutil`（标准库无可靠跨平台方式获取进程创建时间，见 `requirements-automation.txt` 内的说明注释）同时核对 PID 是否存在与创建时间是否匹配，防止 PID 复用误判；psutil 不可用时保守返回"unknown"，不清理不抢占。陈旧锁归档为 `autodev.lock.stale.<timestamp>`（保留证据，不静默删除）；损坏锁/无法确认一律停止，要求人工用 `--lock-status`/`--unlock-stale` 处理；不提供强制抢锁/强制杀进程能力。**接入 `orchestrator.py`**：`main()` 在 `--list-models` 之后新增 `--lock-status`（只读查询 FREE/ACTIVE/STALE/CORRUPTED，不修改锁）与 `--unlock-stale`（只清理已确认陈旧的锁，活跃/损坏/无法确认一律拒绝）；正式运行路径（含 `--dry-run`/`--no-commit`/`--allow-dirty`）严格按"解析仓库根目录→获取锁→（成功后才）读取/修复 Progress→Auto Loop"顺序执行，获取锁之前不调用 Planner/Claude/Build/Review/Commit、不修改 `AUTODEV_PROGRESS.md`；锁覆盖整个 Run（可含多个 Task），每个 Task 开始时 `lock.update_task()` 更新 task_id；`try/finally` 保证正常成功、Planner/Claude 异常、Validation/Review 失败、BLOCKED、Retry Exhausted、Commit 失败、KeyboardInterrupt 等所有路径都释放锁；新增 SIGTERM 处理器（转换为 KeyboardInterrupt，复用既有清理路径，不在信号处理函数内做文件操作）。**退出码**：新增 `EXIT_LOCK_BUSY=7`/`EXIT_LOCK_UNDETERMINED=8`/`EXIT_UNLOCK_STALE_FAILED=9`（沿用已有 0-6 号退出码含义，不重新赋值避免破坏既有语义）。`RunReport`/`report_writer.py` 新增"运行锁"字段与报告章节。 | `python -m pytest automation/tests`（205 项全部通过，其中 `test_run_lock.py` 新增 29 项，覆盖需求列出的全部 20 个场景，含真实双进程并发竞争测试——用 `multiprocessing.Process` + `Event` 强制同时起跑，断言结果集合恰为 `{ACQUIRED, BUSY}` 且不依赖执行顺序）；另在临时 scratch Git 仓库中做真实双进程手工验证（进程 A 持锁 20 秒，进程 B 在 A 持锁期间查询得到 BUSY 且 owner PID/run_id 与 A 一致，`--lock-status` 报告 ACTIVE 且退出码 7，A 结束后 B 立即再次查询成功获取并释放），过程中未使用任何真实 LawGuard 产品任务 | 2026-07-26 | 修复了实现过程中发现的两个真实 Bug：① `is_owned()`/`release()` 最初依赖 `inspect()` 的存活判定（需要 psutil）来验证"当前进程自己刚创建的锁"，导致 psutil 不可用时进程永远释放不了自己的锁（连锁触发已有 23 个测试因遗留锁文件而失败），已改为直接比对 run_id/pid/repo_root，不再依赖存活判定；② `requirements-automation.txt` 加入中文注释后 `pip install -r` 在 Windows 默认 GBK locale 下因编码探测失败报 `UnicodeDecodeError`，已改存为带 UTF-8 BOM 保存解决。单实例锁不替代、也不删除既有 dirty-file 保护（`git status` 干净检查、`--allow-dirty` 显式跳过语义均原样保留），两者独立生效。边界：锁只能防止"遵守该锁规则的 Auto Dev 实例"并发，无法阻止用户手动编辑、IDE 自动格式化、人工直接执行 git 命令，或未来其他不经过 `automation/orchestrator.py` 入口的脚本；已确认 `automation/` 目录下仅 `orchestrator.py` 定义 `__main__` 入口（见 `test_orchestrator_is_the_only_entrypoint_with_main_guard`），暂无绕开锁的第二入口 |

### 重复实现检查结果（本次设计审计，2026-07-26）

发现并已修复：`FeatureCard.vue`（零引用死组件，已删除）、`StageCard`/`FeatureCard`
自写的 `.card:hover` 与全局 `.card--interactive` 逻辑重复（已改用后者）、`.lead`
样式在 5 个文件重复声明（已收编为全局类）、`AboutView` 的"非官方与公益性质"
NoticeBanner 与 `LegalDisclaimer` 内容重叠（已合并）。
`TrustBanner`（公益声明）、`NoticeBanner`（通用提示）、`LegalDisclaimer`（P-1 非法律
意见声明）三者职责已在 LAWGUARD_SOT.md 12.2 节明确，未再发现混用。当前所有路由均
对应实际存在且启用的页面组件，容器宽度（`--max-width: 1200px`）与响应式断点
（640/960px）全站统一，未发现例外。
SEO 相关信息（title/description/OpenGraph/canonical/robots/sitemap/JSON-LD）已实现
（见上方功能状态表"SEO 基础设施"一行，此前本节留下的"尚未存在"记录已过期，2026-07-26
核实并更正）。
