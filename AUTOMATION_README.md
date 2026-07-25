# LawGuard Auto Dev V1（本地自动开发调度系统）

本系统是法护（LawGuard）项目的本地自动化开发调度工具，帮助以"人工监督、单任务、可审计"的方式
推进 V1 开发。它**不是**产品功能的一部分，不会随前端一起发布，只在本机运行。

## 1. 系统用途

每次运行本系统会：

1. 检查项目环境与 Git 工作区状态；
2. 读取 `LAWGUARD_SOT.md`、`CLAUDE.md` 与当前 Git 状态；
3. 调用 OpenAI（担任法护 CTO 角色）规划**一项**明确、可执行的下一步开发任务；
4. 非交互调用本地 Claude Code CLI 执行该任务；
5. 自动执行构建与验证；
6. 调用 OpenAI 对本次改动进行代码评审；
7. 仅当评审明确通过、验证全部成功、且配置允许时，才自动提交 Git（默认关闭）；
8. 生成结构化运行记录与中文摘要报告。

**V1 每次运行最多完成一个任务，不会自动连续开发，不会无限循环。**

## 2. 架构

```
automation/
├── orchestrator.py     # 主入口，串联整个流程
├── config.py            # 读取 .env.local 配置
├── models.py             # DevelopmentTask / CommandResult / ReviewResult / RunReport
├── security.py           # 命令白名单、路径越界拦截、密钥脱敏
├── context_loader.py     # 受限项目上下文读取（供 OpenAI 使用）
├── openai_client.py      # OpenAI Responses API 调用（规划器 + 评审器）
├── claude_runner.py      # 非交互调用本地 Claude Code CLI
├── validator.py          # 自动验证（git diff --check、npm run build 等）
├── git_service.py        # 受限 Git 操作（查询 + 安全提交）
├── report_writer.py      # 运行记录与中文摘要报告
├── prompts/               # 规划器 / 评审器系统 Prompt
├── runtime/                # 每次运行的详细记录（不纳入 Git）
├── reports/                 # 中文摘要报告（不纳入 Git）
└── tests/                    # 单元测试（不发起真实 API 调用）
```

## 3. 安全边界

- 只在 `D:\SOFT\LawGuard` 项目根目录内工作，不扫描、不访问项目外任何目录。
- 不读取用户主目录、浏览器数据、钱包、密钥文件或其他项目。
- 不打印、不记录、不回传 `OPENAI_API_KEY`；日志与报告中出现的 `sk-` 开头字符串会被自动脱敏。
- 自动执行的验证命令仅限严格白名单（见 `security.py`），一律以参数数组执行，不使用 `shell=True`。
- 禁止执行 `git push`、`git reset --hard`、`git clean`、`git checkout .`、`git restore .`、
  自动 `git commit`（由系统受控提交除外）等破坏性操作。
- Claude Code 以 `subprocess` 非交互方式调用，工作目录固定为项目根目录，设有超时保护。
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

## 8. 正式运行用法

```
python automation/orchestrator.py --no-commit
```

会完整执行规划、Claude 执行、验证、评审，但强制禁止本次自动提交，改动会保留在工作区，
由你人工检查后自行 `git add` / `git commit`。

## 9. 自动提交默认关闭

自动提交默认关闭。启用前必须由你自行在 `.env.local` 中设置：

```
LAWGUARD_AUTO_COMMIT=true
```

设置后，直接运行：

```
python automation/orchestrator.py
```

系统仍会在评审未通过、验证失败、工作区不干净（`--allow-dirty` 模式）等情况下拒绝提交。

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

## 12. 如何停止

- 运行中可直接 `Ctrl+C` 中断，系统不会在中断瞬间执行提交。
- 本系统不启动任何后台常驻服务，关闭终端窗口即代表停止运行。

## 13. V1 限制

- 每次运行只完成一个任务，不做多任务连续开发，不做无限循环。
- 不引入数据库、后端服务、用户登录、任务队列、容器化部署。
- 不会自动安装前端/Python 依赖，缺少依赖时会明确报告，由你决定是否安装。
- 不会执行 `git push`，所有提交仍需你自行推送。

## 14. Windows CMD 示例

```cmd
cd /d D:\SOFT\LawGuard
python -m pip install -r requirements-automation.txt
python -m unittest discover -s automation/tests -p "test_*.py"
python automation\orchestrator.py --dry-run
python automation\orchestrator.py --no-commit
python automation\orchestrator.py --no-commit --verbose
python automation\orchestrator.py --model gpt-5.5 --dry-run
```
