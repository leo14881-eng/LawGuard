# LawGuard Auto Dev V1（本地自动开发调度系统）

本系统是法护（LawGuard）项目的本地自动化开发调度工具，用于**全自动无人值守**推进 V1
开发。它**不是**产品功能的一部分，不会随前端一起发布，只在本机运行。

## 1. 系统用途

启动后系统会持续自动循环，每一轮：

1. 检查项目环境与 Git 工作区状态；
2. 读取 `LAWGUARD_SOT.md`、`CLAUDE.md`、当前 Git 状态与 Auto Dev 进度台账
   （`docs/project/AUTODEV_PROGRESS.md`，避免重复开发已完成任务）；
3. 调用 OpenAI（担任法护 CTO 角色）规划**一项**明确、可执行的下一步开发任务，或返回
   `DONE`（已无更多可安全规划的新任务）/ `BLOCKED`（存在开发方向但因权限/依赖/环境/
   资源或治理原则限制无法安全继续）；
4. 非交互调用本地 Claude Code CLI 执行该任务；
5. 自动执行构建与验证；
6. 调用 OpenAI 对本次改动进行代码评审；
7. 评审 PASS 且允许自动提交时，先更新 `docs/project/AUTODEV_PROGRESS.md`，再把该文件
   与本次任务代码改动合并为**一次** Git Commit；
8. 立即开始下一个任务，重复以上流程；
9. 每一轮都会生成结构化运行记录与中文摘要报告。

**不会等待人工确认**，只有满足以下条件之一才会停止：Planner 返回 `DONE`、Planner 返回
`BLOCKED`、Claude 执行失败、构建/测试失败、Review 未通过（`FAIL` 或 `BLOCKED`）、OpenAI
调用失败、已有的超时限制触发，或用户按 `Ctrl+C` 主动中断。`--dry-run`、`--no-commit`、
`--allow-dirty` 由于本身不会产生提交，效果等同于只执行一个任务后停止，适合单任务预览
与调试，不会进入连续循环。

## 2. 架构

```
automation/
├── orchestrator.py     # 主入口，串联整个流程并驱动 Auto Loop / Auto Commit
├── config.py            # 读取 .env.local 配置
├── models.py             # DevelopmentTask / CommandResult / ReviewResult / RunReport
├── security.py           # 命令白名单、路径越界拦截、密钥脱敏
├── context_loader.py     # 受限项目上下文读取（供 OpenAI 使用，含进度台账摘要）
├── progress.py            # Auto Dev 进度台账读写、自动创建与自动修复
├── openai_client.py      # OpenAI Responses API 调用（规划器 + 评审器）
├── claude_runner.py      # 非交互调用本地 Claude Code CLI
├── validator.py          # 自动验证（git diff --check、npm run build 等）
├── git_service.py        # 受限 Git 操作（查询 + 安全提交）
├── report_writer.py      # 运行记录与中文摘要报告
├── prompts/               # 规划器 / 评审器系统 Prompt
├── runtime/                # 每次任务的详细记录（不纳入 Git）
├── reports/                 # 中文摘要报告（不纳入 Git）
└── tests/                    # 单元测试（不发起真实 API 调用）

docs/project/AUTODEV_PROGRESS.md   # Auto Dev 进度台账（纳入 Git，跨进程持久化）
```

## Auto Loop / Auto Commit / Progress 管理

- **Auto Loop**：`orchestrator.main()` 在一个 `while True` 循环中反复调用单任务流水线；
  只有某个任务成功评审并自动提交（状态 `COMMITTED`）时才立即开始下一个任务，其余任何
  终止状态都会结束循环。
- **Planner 终止语义**：`DONE` 表示项目在 V1 范围内已没有更多可安全规划的新任务（正常
  结束，`Auto Dev Finished`）；`BLOCKED` 表示确实存在开发方向，但因权限、依赖、环境、
  资源不足，或 P-1/P0/P1/P2 治理原则要求（例如缺少可核验法律来源、涉及个案判断）而无法
  安全继续，两者语义不同，不会混用。
- **Auto Commit**：评审 PASS 且允许自动提交时，先更新 `docs/project/AUTODEV_PROGRESS.md`，
  再把该文件与本次任务代码改动**合并为一次** Git Commit，提交信息统一为
  `AutoDev(task-NNN): <评审器生成的简短说明>`（`NNN` 为任务序号，自动递增，不使用随机
  文案）。一个任务只产生一个 Commit，回滚该 Commit 时代码与 Progress 记录保持一致。
  任何情况下都不会执行 `git push`，所有提交仅保留在本地仓库。
- **Progress 管理**：`docs/project/AUTODEV_PROGRESS.md` 是唯一的开发进度来源（Last
  Update / Last Commit / Completed Tasks / Current Task / Next Candidate Tasks /
  Known Issues）。`LAWGUARD_SOT.md` 只保存项目定位、系统架构、设计原则、开发规范、
  技术路线等长期稳定事实，Auto Dev **不会**、也不允许自动修改 `LAWGUARD_SOT.md`
  （已在 Planner 校验与 Git 提交两层强制拦截）。Planner 每轮规划前都会读取进度台账，
  据此避免重复开发 Completed Tasks 中已完成的任务。
- **启动恢复**：每次启动都会优先读取 `docs/project/AUTODEV_PROGRESS.md`；文件不存在时
  自动创建默认模板，格式异常（缺少必需章节）时自动重建为默认模板，均不会因此停止运行；
  任务序号会从已记录的 Completed Tasks 数量之后接续编号，不会在重启后从 `task-001`
  重新计数。

## 3. 安全边界

- 只在 `D:\SOFT\LawGuard` 项目根目录内工作，不扫描、不访问项目外任何目录。
- 不读取用户主目录、浏览器数据、钱包、密钥文件或其他项目。
- 不打印、不记录、不回传 `OPENAI_API_KEY`；日志与报告中出现的 `sk-` 开头字符串会被自动脱敏。
- 自动执行的验证命令仅限严格白名单（见 `security.py`），一律以参数数组执行，不使用 `shell=True`。
- 禁止执行 `git push`、`git reset --hard`、`git clean`、`git checkout .`、`git restore .`、
  自动 `git commit`（由系统受控提交除外）等破坏性操作。
- Claude Code 以 `subprocess` 非交互方式调用，工作目录固定为项目根目录，设有超时保护。
- 调用时附带 `--permission-mode acceptEdits`：仅自动放行文件编辑类工具（Edit /
  Write / NotebookEdit），使非交互模式下的代码改动无需人工逐次点击"允许"；
  Bash 等其他工具仍走正常权限流程，非交互模式下同样会被拒绝而非被绕过，因此
  不会放宽 git commit / push / 任意 Shell 命令的限制。未额外传入 `--add-dir`，
  写入范围仍被 Claude Code 自身限制在项目根目录内，不会扩大到项目目录之外。
- 自动提交前必须同时满足：Claude 执行成功、自动验证成功、OpenAI 评审明确返回 `PASS` 且
  `safe_to_commit=true`、`.env.local` 中 `LAWGUARD_AUTO_COMMIT=true`、未使用 `--no-commit` /
  `--allow-dirty`。
- 若运行开始前 Git 工作区不干净，默认立即停止；`--allow-dirty` 可显式跳过检查，但该模式下
  **永远禁止自动提交**。
- 默认禁止自动修改 `LAWGUARD_SOT.md`，除非任务明确要求且评审确认必要。

## 4. 安装命令

```
python -m pip install -r requirements-automation.txt
```

## 5. 环境变量

在项目根目录 `.env.local` 中配置（不要提交该文件到 Git）：

```
OPENAI_API_KEY=你的密钥（必填）
OPENAI_MODEL=你的 OpenAI 账户实际可访问的模型名（必填，无内置默认值）
LAWGUARD_AUTO_COMMIT=false（可选，默认 false）
LAWGUARD_CLAUDE_TIMEOUT_SECONDS=1800（可选，默认 1800）
LAWGUARD_OPENAI_TIMEOUT_SECONDS=180（可选，默认 180）
```

- `OPENAI_API_KEY` 缺失时程序会输出中文错误提示并安全退出，不会静默继续；程序不会读取、
  打印或以任何形式回传该密钥。
- `OPENAI_MODEL` **没有内置默认值**：请根据你自己 OpenAI API 账户实际可访问的模型填写，
  未配置（且未通过 `--model` 指定）时程序会输出中文错误提示并安全退出，不会静默使用某个
  猜测的模型名。若填写的模型在你的账户下不可用，OpenAI 接口会返回错误，程序会如实报告
  并停止，**不会自动降级或切换到其他模型**。

### 如何查看账户可用模型 / 配置 OPENAI_MODEL

先在 `.env.local` 中配置好 `OPENAI_API_KEY`（`OPENAI_MODEL` 可以先不填），然后运行：

```
python automation/orchestrator.py --list-models
```

该命令只读查询当前 `OPENAI_API_KEY` 可访问的模型列表并打印出来，**不会做任何文本生成、
不会调用 Claude Code、不会修改代码、不会提交**。展示的候选列表已过滤掉音频、实时语音、
转录、Sora、Web 搜索专用、embedding、审核、语音合成、旧版 instruct、babbage/davinci
等明显不适合"文本规划/评审"场景的模型，优先覆盖 `gpt-5.x`、`gpt-4.1`、`o1`、`o3`、`o4`
系列；这只是启发式过滤，仅供参考。命令还会给出选型建议：

- `gpt-5-nano`：推荐默认使用（成本最低，足够完成 Planner/Review 的 JSON 输出）；
- `gpt-5.5`：高质量，建议仅在正式发布前的最终评审临时使用。

> **重要提示**：Models API 仅表示当前 API Key 可以看到该模型，不保证该模型一定支持当前
> 请求参数和 Responses API；最终以首次实际请求结果为准。

从打印结果中选择一个你确认可用、且支持文本生成的模型名，写入 `.env.local` 的
`OPENAI_MODEL=<模型名>`。

如果你在未配置 `OPENAI_MODEL` 的情况下直接运行 `python automation/orchestrator.py`（或
`--dry-run`），程序会自动尝试用你的 `OPENAI_API_KEY` 做同样的模型自检，把查询到的可用
模型列表打印在错误信息里，方便你直接抄写；如果查询也失败（例如网络不可用、Key 无权限），
则如实输出中文错误并安全退出。**无论哪种情况，程序都不会替你自动选择或静默切换模型**，
你必须显式把最终选定的模型名写入 `OPENAI_MODEL` 或通过 `--model` 传入后才能继续运行。

## 成本推荐

本系统默认遵循 **Cost First（成本优先）**：在不降低任何安全 Gate 的前提下，把 OpenAI
API 成本压缩到最低。

推荐配置：

- **开发阶段**：
  ```
  OPENAI_MODEL=gpt-5-nano
  ```
  原因：成本最低；足够完成 Planner 的 JSON 任务规划与 Reviewer 的基础评审；真正的编码
  工作由本地 Claude Code 承担，不依赖 OpenAI 模型的代码生成能力；`npm run build`/测试等
  Validator + 单元测试 + Review Gate 已经是主要的安全防线，不依赖更贵的模型来兜底。

- **正式发布前**：可以临时切换到更高质量的模型完成最终评审：
  ```
  OPENAI_MODEL=gpt-5.5
  ```
  完成后可以再切回 `gpt-5-nano`。**切换必须由你自己显式修改 `.env.local` 或使用
  `--model`，系统不会自动切换。**

每次运行结束后，`automation/reports/<run_id>.md` 的"OpenAI Token 用量"一节会列出本次
Planner/Reviewer 调用的 Prompt/Completion/Total Tokens（API 未返回时显示 `Unknown`，
不做任何估算），Estimated Cost 固定显示 `Unknown`——项目内没有内置价格表（OpenAI 定价会
变化，硬编码费率本身就是一种编造数据的风险），费用请你自行按 OpenAI 官方定价核算。

## 6. 首次安全测试

在真正调用 OpenAI / Claude 之前，建议先运行单元测试确认安全边界生效：

```
python -m unittest discover -s automation/tests -p "test_*.py"
```

测试全程不会发起真实的 OpenAI 或 Claude 调用。

## 7. dry-run 用法（只看任务，不动代码）

```
python automation/orchestrator.py --dry-run
```

会调用 OpenAI 规划任务并展示，但不会调用 Claude Code、不修改任何代码、不提交 Git。

## 8. 正式运行用法（单任务预览/调试）

```
python automation/orchestrator.py --no-commit
```

会完整执行规划、Claude 执行、验证、评审，但强制禁止本次自动提交，改动会保留在工作区，
由你人工检查后自行 `git add` / `git commit`。由于不会产生提交，Auto Loop 在此模式下
只会执行一个任务后停止。

## 9. 全自动无人值守运行

自动提交默认关闭。启用前必须由你自行在 `.env.local` 中设置：

```
LAWGUARD_AUTO_COMMIT=true
```

设置后，直接运行：

```
python automation/orchestrator.py
```

系统会持续自动循环执行「规划 → Claude 执行 → 构建/测试 → 评审 → 更新进度 → 自动提交 →
下一任务」，全程无需人工确认，直到 Planner 返回 `DONE`（已无更多可安全规划的新任务，
此时会输出 `Planner: DONE` 与 `Auto Dev Finished` 并正常退出）或触发某个停止条件为止。
系统仍会在评审未通过、验证失败、工作区不干净（`--allow-dirty` 模式）等情况下拒绝提交，
并结束循环。

## 10. 如何查看报告

- 中文摘要报告：`automation/reports/<run_id>.md`
- 详细运行记录：`automation/runtime/<run_id>/`（包含 `task.json`、`claude_stdout.txt`、
  `claude_stderr.txt`、`validation.json`、`review.json`、`run_report.json`、`orchestrator.log`）

两个目录均已加入 `.gitignore`，不会被提交。

## 11. 常见错误

| 现象 | 可能原因 | 处理方式 |
| --- | --- | --- |
| 提示未找到 `OPENAI_API_KEY` | `.env.local` 未配置或路径不对 | 在项目根目录创建/编辑 `.env.local` |
| 提示未配置 `OPENAI_MODEL` | `.env.local` 未设置，且未使用 `--model` | 填写你账户实际可访问的模型名后重试，程序不会替你猜测 |
| 提示未找到 Claude Code CLI | 系统 PATH 中没有 `claude` 或 `claude.cmd` | 确认已安装 Claude Code 并加入 PATH |
| 提示 Git 工作区不干净 | 存在未提交的改动 | 先自行提交/暂存，或使用 `--allow-dirty`（仍不会自动提交） |
| 验证阶段 `npm run build` 失败 | 前端代码本身有类型错误或构建错误 | 查看 `automation/runtime/<run_id>/validation.json` 定位具体错误 |
| OpenAI 报错模型不可用 | `OPENAI_MODEL` 配置了当前账号不可用的模型 | 更换为可用模型，程序不会自动降级或静默切换 |
| Claude 执行摘要提示"需要您批准写入权限"、`claude_stdout.txt` 无实际改动 | 本地 Claude Code CLI 版本过旧，不支持 `--permission-mode` 参数，非交互模式下文件写入请求无法自动放行 | 升级本地 Claude Code CLI 到支持 `--permission-mode acceptEdits` 的版本后重试 |

## 12. 如何停止

Auto Loop 只在以下情况停止，除此之外不会等待人工确认：

1. Planner 返回 `DONE`（已无更多可安全规划的新任务，输出 `Planner: DONE` /
   `Auto Dev Finished`，正常结束）；
2. Planner 返回 `BLOCKED`（存在开发方向但因权限/依赖/环境/资源或治理原则限制无法
   安全继续）；
3. Claude Code 执行失败；
4. 构建（`npm run build`）失败；
5. 任务附加测试命令失败；
6. Review 结论为 `FAIL`；
7. Review 结论为 `BLOCKED`；
8. 调用 OpenAI（Planner 或 Reviewer）失败；
9. 触发已有的 Claude/OpenAI 超时限制；
10. 用户按 `Ctrl+C` 主动中断（系统不会在中断瞬间执行提交）。

本系统不启动任何后台常驻服务，关闭终端窗口即代表停止运行。

## 13. V1 限制

- 启动后持续自动循环开发，直到无更多任务或触发第 12 节列出的停止条件，不做无限重试。
- 不引入数据库、后端服务、用户登录、任务队列、容器化部署。
- 不会自动安装前端/Python 依赖，缺少依赖时会明确报告，由你决定是否安装。
- 不会执行 `git push`，所有提交仍需你自行推送。

## 14. Windows CMD 示例

```cmd
cd /d D:\SOFT\LawGuard
python -m pip install -r requirements-automation.txt
python -m unittest discover -s automation/tests -p "test_*.py"
python automation\orchestrator.py --list-models
python automation\orchestrator.py --dry-run
python automation\orchestrator.py --no-commit
python automation\orchestrator.py --no-commit --verbose
python automation\orchestrator.py --model <你账户可用的模型名> --dry-run
```
