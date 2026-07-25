# CLAUDE.md

本文件为 Claude Code 在 LawGuard（法护）项目中的执行规则、开发规范与命令说明。
项目唯一事实源为 `LAWGUARD_SOT.md`，本文件只负责"如何开发"，不重复记录产品事实。

## P-1：非法律意见原则（全项目最高优先级）

`LAWGUARD_SOT.md` 的 "P-1：非法律意见原则" 一章优先级高于本文件包括下方 P0 在内的
其余所有条款。法护永远是公益普法平台，不是律师、不是法律咨询平台、不是案件分析平台。
任何开发行为（人工或 AI）不得让系统判断案件是否合法/是否构成犯罪/是否有罪/可能判几年，
不得评价警方、检察院、法院或律师的具体行为/意见是否正确，不得推荐诉讼策略、辩护方案、
举报方案或规避法律责任的方法。涉及具体案件咨询的任务必须立即 `BLOCKED`（规划阶段）或
`FAIL`（评审阶段），统一按 SOT 中规定的标准话术处理，不得展开个案分析。

## P0：法律内容真实性原则（次高优先级）

`LAWGUARD_SOT.md` 的 "P0：法律内容真实性原则" 一章优先级仅次于 P-1，高于本文件其余所有
条款。任何开发行为（人工或 AI）涉及法律内容时必须先遵守该章节：无可靠来源时必须停止并
输出 `BLOCKED`，不得依据模型记忆编写或推断法律条文、条文编号、权利义务、法定期限、法律
程序、适用条件、法律后果、司法解释、办案流程、救济渠道。

> LawGuard 的核心价值不是生成更多法律内容，而是保证每一句法律内容都真实、准确、可追溯。
> 宁可缺失，不可错误；宁可返回 BLOCKED，也不得猜测或编造。

## P1 / P2：官方优先原则与法律版本管理原则

法律内容页面呈现顺序必须为"官方来源 → LawGuard 解释 → 辅助说明"，不得"AI 解释在前、
官方来源在后"；检测到法律版本变化时，自动开发系统不得自动修改已发布内容，只能生成
"待人工审核"任务。详见 `LAWGUARD_SOT.md` 的 "P1" "P2" 两章。

以上 P-1、P0、P1、P2 四项原则的优先级永久高于开发速度、页面数量、自动化程度和任务完成率。

## P3：产品级界面原则

`LAWGUARD_SOT.md` 的 "P3：产品级界面原则" 一章要求所有用户可见页面同时满足功能完整、
视觉完整、交互完整、响应式完整、状态反馈完整，禁止临时页面上线、默认组件堆砌、展示原始
JSON/开发日志、"以后再美化"式交付、页面各自定义样式、炫技动画、低对比度小字布局。页面须
使用统一设计系统（`web/src/style.css` 中的 Design Tokens 与 `web/src/components/` 中的
通用组件），并覆盖 loading/empty/error/disabled 等状态。**P3 不得覆盖或削弱 P-1/P0/P1/P2**，
法律真实性和非法律意见原则始终高于视觉设计。

## 项目性质

法护（LawGuard）是免费、公益、独立、非商业的刑事诉讼权利普法平台。
不属于政府机关、公安机关、检察院、法院、律师事务所或法律援助机构。
不提供个案分析、辩护策略、在线咨询或 AI 聊天；不收费；不收集用户材料。
详细产品边界见 `LAWGUARD_SOT.md`。

## 开发规则（必须遵守）

1. 所有新增代码注释使用简体中文书写。
2. 所有用户界面文案使用简体中文，不得展示生硬状态码或英文内部名称（如 404、undefined、error code 等）。
3. 每次修改前先阅读 `LAWGUARD_SOT.md`，确保改动符合当前产品边界与既定信息架构。
4. 每次完成开发后，必须更新 `docs/project/AUTODEV_PROGRESS.md` 中的开发进度记录
   （Completed Tasks / Last Update 等）。`LAWGUARD_SOT.md` 只保存项目定位、系统架构、
   设计原则、开发规范、技术路线等长期稳定事实，禁止记录开发进度、已完成任务或下一步
   计划——两者职责不得重叠，不得自动或手动把进度类内容写回 `LAWGUARD_SOT.md`。
5. 修改后必须在 `web/` 目录执行 `npm run build`，确保构建通过。
6. 若项目配置了 lint 或 typecheck 命令，也必须一并执行。
7. 不得读取或修改 `D:\SOFT\LawGuard` 之外的文件。
8. 不得访问用户个人目录、钱包、助记词、银行资料、SSH 密钥及其他项目目录。
9. 不得自行扩大 V1 功能范围，新功能需求先在 `LAWGUARD_SOT.md` 中确认后再实现。
10. 不得删除或重写与当前任务无关的内容。
11. 遇到法律内容不确定时，只能在页面上标记"待法律复核"，不得虚构法律条文、案号或链接。
12. 法律条文、司法解释等正式内容不得仅凭模型记忆作为发布依据，必须来自可核验的公开正式文本（见 `LAWGUARD_SOT.md` P0.2 允许来源清单）；无法核验时标记"待法律复核"或"待官方链接核验"，不得凭记忆推断后直接发布。
13. 未经执业律师审核的法律内容，页面状态统一标注为"待法律复核"。
14. 新增法律事实但找不到可靠来源时，必须停止开发并输出 `BLOCKED`，不得为了完成任务而编造或推断（见 `LAWGUARD_SOT.md` P0）。
15. 禁止引入用户系统、登录注册、表单提交、文件上传、评论、论坛、在线咨询、AI 接口、数据统计 SDK、广告 SDK 等 V1 明确禁止的能力。

## 项目状态

`web/` 是唯一的代码目录，为 Vue 3 + TypeScript + Vite + Vue Router 前端项目。
无后端、无数据库、无用户系统。内容以本地 TypeScript/JSON 数据文件维护。

## 仓库结构

- `web/` — 前端项目（Vue 3 + TypeScript + Vite）
- `LAWGUARD_SOT.md` — 项目唯一事实源
- `CLAUDE.md` — 本文件

## 常用命令（在 `web/` 目录下执行）

```
npm run dev       # 启动 Vite 开发服务器
npm run build     # 类型检查（vue-tsc -b）后执行生产构建
npm run preview   # 本地预览生产构建
```

当前未配置独立的 lint 命令；`npm run build` 中包含的 `vue-tsc -b` 承担类型检查职责。

## 架构说明

- 入口：`web/src/main.ts` 创建 Vue 应用、挂载路由，并挂载到 `#app`。
- 路由：`web/src/router/index.ts`，使用 `createWebHistory`。
- 页面组件位于 `web/src/views/`，可复用组件位于 `web/src/components/`。
- 内容数据（如刑事诉讼阶段列表）位于 `web/src/data/`，为静态 TypeScript 数据，不接入任何后端。
- 全局样式与设计变量位于 `web/src/style.css`，主色为深蓝色系，不引入外部字体或第三方 UI 组件库。
- TypeScript 使用 composite tsconfig：`tsconfig.json` 引用 `tsconfig.app.json`（应用源码）与
  `tsconfig.node.json`（Vite 配置）。

## 文档规则

项目只长期维护 `CLAUDE.md` 与 `LAWGUARD_SOT.md` 两份项目级文档。
禁止创建 SESSION_SUMMARY.md、单独架构/产品说明文档、每日总结文档或其他无必要的 Markdown 文件。
`web/README.md` 为脚手架自带说明，可保留，但项目事实以 `LAWGUARD_SOT.md` 为准。
`docs/project/AUTODEV_PROGRESS.md` 为唯一例外：它是 Auto Dev 自动开发系统的进度台账
（Last Update / Last Commit / Completed Tasks / Current Task / Next Candidate Tasks /
Known Issues），由 `automation/progress.py` 自动创建与维护，不属于"说明性 Markdown
文档"，不受本节"禁止创建"限制约束。

## SOT 与 Progress 的职责边界

`LAWGUARD_SOT.md` 与 `docs/project/AUTODEV_PROGRESS.md` 职责不能重叠：

- `LAWGUARD_SOT.md`：只保存项目定位、系统架构、设计原则、开发规范、技术路线等
  长期稳定事实；禁止记录逐日开发进度、已完成任务清单或下一步开发计划。
- `docs/project/AUTODEV_PROGRESS.md`：唯一的开发进度来源，负责 Last Update、
  Last Commit、Completed Tasks、Current Task、Next Candidate Tasks、Known Issues。

Auto Dev 只能自动更新 `docs/project/AUTODEV_PROGRESS.md`，不得自动修改
`LAWGUARD_SOT.md`。
