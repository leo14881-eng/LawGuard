# 法护 LawGuard

面向刑事案件当事人及其家属的公益应急导航平台。

> LawGuard is a free, non-profit navigation platform for people affected by criminal
> proceedings in China and their families.

## 这是什么

法护（LawGuard）帮助刑事案件当事人及其家属在关键时刻知道下一步该怎么办：提供基于
官方法律依据的一般性程序导航、权利指引、文书核对方法和官方救济渠道。

**LawGuard 不是律师、不是律所、不是政府机关，不提供个案法律意见，不接受案件委托。**
如需针对具体案件的帮助，请咨询执业律师或当地法律援助机构。

- 纯公益、独立、非商业，永久免费，不收费；
- 不要求注册，不主动联系用户，不收集个人信息；
- 不推荐具体律师，不代收费用，不承诺任何案件结果。

完整产品定位、边界与治理原则见 [`LAWGUARD_SOT.md`](./LAWGUARD_SOT.md)。

## 技术栈

- Vue 3 + `<script setup lang="ts">` + TypeScript
- Vite + Vue Router
- 原生 CSS（统一 Design Tokens，无 CSS 框架）
- Vitest + @vue/test-utils（前端单元/组件测试）
- 内容以本地静态 TypeScript 数据维护，无后端、无数据库、无用户系统

## 快速开始

```bash
cd web
npm install
npm run dev       # 本地开发服务器
npm run build     # 类型检查 + 生产构建
npm run test      # 运行单元/组件测试
npm run preview   # 预览生产构建
```

## 目录结构

```
LawGuard/
├─ LAWGUARD_SOT.md         # 项目唯一事实源：产品定位、边界、治理原则
├─ CLAUDE.md                 # AI/人工开发执行规则
├─ AUTOMATION_README.md       # Auto Dev 本地自动开发系统说明（非产品文档）
├─ automation/                 # Auto Dev V1（Python）
├─ docs/project/AUTODEV_PROGRESS.md  # 开发进度与功能状态的唯一来源
└─ web/                          # 前端项目（Vue 3 + TypeScript + Vite）
```

## 文档索引

| 文档 | 用途 |
| --- | --- |
| [`LAWGUARD_SOT.md`](./LAWGUARD_SOT.md) | 产品定位、用户、功能范围、法律内容治理原则（唯一事实源） |
| [`CLAUDE.md`](./CLAUDE.md) | 开发执行规则、去重检查、命令说明 |
| [`docs/project/AUTODEV_PROGRESS.md`](./docs/project/AUTODEV_PROGRESS.md) | 各功能真实开发状态（PLANNED/IMPLEMENTED/VERIFIED 等） |
| [`AUTOMATION_README.md`](./AUTOMATION_README.md) | 本地 Auto Dev 自动开发系统使用说明 |

## 参与开发

任何新功能开发前，请先阅读 `LAWGUARD_SOT.md` 与 `docs/project/AUTODEV_PROGRESS.md`，
确认是否已有相同或相似实现，避免重复开发（详见 `CLAUDE.md`"开发前去重检查"一节）。
涉及法律内容的改动必须能追溯到可核验的官方来源，无法核验时一律标注"待法律复核"，
不得凭记忆编造或推断。
