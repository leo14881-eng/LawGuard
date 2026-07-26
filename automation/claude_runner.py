"""Claude Code 执行器：以非交互方式调用本地 Claude Code CLI 执行开发任务。

不得使用 shell=True，工作目录固定为项目根目录，不把 API Key 传入提示词。
"""
from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path

from automation.models import CommandResult

_CANDIDATE_NAMES = ("claude", "claude.cmd", "claude.exe")


def locate_claude_executable() -> str | None:
    """在系统 PATH 中查找 Claude Code CLI 可执行文件（兼容 Windows 的 claude.cmd）。"""
    for name in _CANDIDATE_NAMES:
        found = shutil.which(name)
        if found:
            return found
    return None


def build_task_prompt(
    *,
    task_title: str,
    objective: str,
    scope: str,
    files_allowed: list[str],
    files_forbidden: list[str],
    acceptance_criteria: list[str],
    validation_commands: list[str],
    developer_prompt: str,
) -> str:
    """构建下发给 Claude Code 的完整任务 Prompt（全部使用中文）。"""
    allowed_text = "\n".join(f"- {f}" for f in files_allowed) or "（无）"
    forbidden_text = "\n".join(f"- {f}" for f in files_forbidden) or "（无）"
    criteria_text = "\n".join(f"- {c}" for c in acceptance_criteria) or "（无）"
    commands_text = "\n".join(f"- {c}" for c in validation_commands) or "（无）"

    return f"""你正在为"法护（LawGuard）"项目执行一次受限的自动化开发任务。

【项目定位】
法护是免费、公益、独立、非商业的刑事诉讼权利普法平台。
不属于政府机关、公检法或律所，不提供个案分析、辩护策略、在线咨询或 AI 聊天，不收费，不收集用户材料。
开始前请先阅读项目根目录的 LAWGUARD_SOT.md 与 CLAUDE.md，严格遵守其中记录的产品边界与开发规则。

【当前任务】
标题：{task_title}
目标：{objective}
范围：{scope}

【允许修改的文件】
{allowed_text}

【禁止修改的文件】
{forbidden_text}

【验收条件】
{criteria_text}

【必须执行的验证命令】
{commands_text}

【任务详细说明】
{developer_prompt}

【强制要求，必须严格遵守】
1. 先检查相关文件的现状，再实施改动，不要臆测文件内容。
2. 严格只修改"允许修改的文件"范围内的内容，绝不触碰"禁止修改的文件"。
3. 不得访问或修改本项目目录之外的任何文件、目录。
4. 完成实施后必须执行上述验证命令，确认全部通过；若无法通过需如实说明原因。
5. 最后必须用简体中文输出一份简短的执行摘要，说明改动内容与验证结果。
6. 不要执行 git commit。
7. 不要执行 git push。
8. 不要新建任何与本任务无关的 Markdown 文档。
9. 【P0 法律内容真实性原则，最高优先级】不得依据模型记忆新增或推断法律条文、条文编号、
   权利义务、法定期限、法律程序、适用条件、法律后果、司法解释、办案流程、救济渠道等法律
   事实。如果任务要求补充的法律内容在项目内没有可核验的官方来源，必须立即停止实施该部分
   内容，不得编造、不得凭记忆润色，并在最终执行摘要中明确报告"BLOCKED：缺少可核验法律
   来源"及具体原因。已有"待法律复核"标注的内容可以保留，但不得擅自"坐实"为正式内容。
"""


def build_validation_fix_prompt(
    *,
    task_title: str,
    task_objective: str,
    scope: str,
    files_allowed: list[str],
    files_forbidden: list[str],
    risk_level: str,
    attempt_number: int,
    max_attempts: int,
    failed_command: str,
    exit_code: int,
    stdout: str,
    stderr: str,
    validation_results_text: str,
    git_diff_text: str,
) -> str:
    """构建 Validation Fix Attempt 下发给 Claude Code 的"仅修复验证失败"Prompt（全部使用中文）。

    只用于 LOW Risk 任务在 git diff --check / 类型检查 / 测试 / Build / 任务附加验证命令
    失败后的自动修复：严格限定为"只修复本次验证失败"，不得删除/跳过/弱化测试、不得用
    any/@ts-ignore/setTimeout 等方式掩盖问题，交由流水线重新执行完整验证。
    """
    allowed_text = "\n".join(f"- {f}" for f in files_allowed) or "（无）"
    forbidden_text = "\n".join(f"- {f}" for f in files_forbidden) or "（无）"

    return f"""你正在为"法护（LawGuard）"项目的自动化开发任务执行一次 Validation Fix 修复。

本次自动验证未通过。

当前任务：
{task_title}

任务目标：
{task_objective}

任务范围（不得扩大或改变）：
{scope}

风险等级：
{risk_level}

当前 Attempt：
{attempt_number} / {max_attempts}

失败命令：
{failed_command}

退出码：
{exit_code}

标准输出：
{stdout}

错误输出：
{stderr}

其他验证结果：
{validation_results_text}

当前任务 Git Diff：
{git_diff_text}

【允许修改的文件（与原任务一致，不得扩大）】
{allowed_text}

【禁止修改的文件】
{forbidden_text}

【要求，必须严格遵守】
1. 仅修复上述验证失败，不得修改无关代码。
2. 不重新规划任务，不改变任务目标或验收条件。
3. 不新增功能，不修改产品设计。
4. 不修改无关文件。
5. 不修改法律内容（如涉及法律内容问题，直接在执行摘要中报告 BLOCKED，不得自行编造或推断）。
6. 不得删除、跳过或弱化测试（禁止 .skip/xit/xdescribe/降低断言强度/注释掉功能）。
7. 不得使用 any、@ts-ignore、@ts-nocheck、setTimeout 等方式掩盖问题、隐藏错误。
8. 不得修改原任务验收标准，不得删除 Review 阻塞项对应的功能代码。
9. 保留当前已有的有效改动。
10. 严格只修改"允许修改的文件"范围内的内容，绝不触碰"禁止修改的文件"。
11. 不得访问或修改本项目目录之外的任何文件、目录。
12. 修复完成后立即结束，由流水线自动重新执行完整验证，不需要你自行判断是否通过。
13. 最后用简体中文简短说明本次修复了什么，不要展开无关分析。
14. 不要执行 git commit，不要执行 git push。
"""


def build_review_fix_prompt(
    *,
    task_title: str,
    task_objective: str,
    scope: str,
    files_allowed: list[str],
    files_forbidden: list[str],
    attempt_number: int,
    max_attempts: int,
    review_summary: str,
    blocking_issues: list[str],
    non_blocking_suggestions: list[str],
    validation_results_text: str,
    git_diff_text: str,
) -> str:
    """构建 Review Fix Attempt 下发给 Claude Code 的"仅修复评审问题"Prompt（全部使用中文）。

    只用于 LOW Risk 任务在 Review FAIL 后的自动修复：严格限定为"只修复评审指出的问题"，
    不重新规划任务、不改变任务目标、不新增功能、不扩大修改范围，交由流水线重新验证。
    """
    allowed_text = "\n".join(f"- {f}" for f in files_allowed) or "（无）"
    forbidden_text = "\n".join(f"- {f}" for f in files_forbidden) or "（无）"
    blocking_text = "\n".join(f"- {i}" for i in blocking_issues) or "（无）"
    suggestions_text = "\n".join(f"- {s}" for s in non_blocking_suggestions) or "（无）"

    return f"""你正在为"法护（LawGuard）"项目的自动化开发任务执行一次 Review Fix 修复。

本次 Code Review 未通过。

当前任务：
{task_title}

任务目标：
{task_objective}

任务范围（不得扩大或改变）：
{scope}

当前 Attempt：
{attempt_number} / {max_attempts}

Review Summary：
{review_summary}

Blocking Issues：
{blocking_text}

Non-blocking Suggestions：
{suggestions_text}

最近验证结果：
{validation_results_text}

当前任务 Git Diff：
{git_diff_text}

【允许修改的文件（与原任务一致，不得扩大）】
{allowed_text}

【禁止修改的文件】
{forbidden_text}

【要求，必须严格遵守】
1. 只修复 Blocking Issues 指出的问题，不得修改无关代码。
2. Non-blocking Suggestions 仅在不扩大修改范围时可以顺手处理，不强制。
3. 不重新规划任务，不改变任务目标或验收条件。
4. 不新增功能，不修改产品设计。
5. 不修改无关文件。
6. 不修改法律内容（如涉及法律内容问题，直接在执行摘要中报告 BLOCKED，不得自行编造或推断）。
7. 不得删除、跳过或弱化测试，不得用 any/@ts-ignore/setTimeout 等方式掩盖问题。
8. 严格只修改"允许修改的文件"范围内的内容，绝不触碰"禁止修改的文件"。
9. 不得访问或修改本项目目录之外的任何文件、目录。
10. 修复完成后立即结束，由流水线自动重新执行完整验证和评审，不需要你自行判断是否通过。
11. 最后用简体中文简短说明本次修复了什么，不要展开无关分析。
12. 不要执行 git commit，不要执行 git push。
"""


def run_claude(
    prompt: str,
    *,
    project_root: Path,
    timeout_seconds: int,
) -> CommandResult:
    """非交互调用 Claude Code CLI 执行任务，返回执行结果。

    超时或找不到可执行文件时同样返回 CommandResult，由调用方判断是否终止流程。
    """
    executable = locate_claude_executable()
    command_label = f"claude -p <task_prompt, {len(prompt)} 字符> --permission-mode acceptEdits"

    if executable is None:
        return CommandResult(
            command=command_label,
            cwd=str(project_root),
            exit_code=-1,
            stdout="",
            stderr="未在系统 PATH 中找到 Claude Code CLI（claude 或 claude.cmd），请确认已正确安装。",
            duration_seconds=0.0,
            timed_out=False,
        )

    # 非交互模式（-p）下，Claude Code 默认权限模式（default）会像交互式会话一样
    # 为每次文件写入弹出确认提示；但非交互模式没有终端可供确认，请求会被直接
    # 拒绝，Claude 只能在回复文本里说明"需要您批准写入权限"，无法真正落盘。
    # 这正是编排器此前表现为"只读"、每次都要人工手动授权的根本原因。
    #
    # 这里改用 --permission-mode acceptEdits：只自动放行文件编辑类工具
    # （Edit / Write / NotebookEdit），其余工具（如 Bash）仍走正常权限流程，
    # 在非交互模式下同样会被拒绝而不是被绕过，因此不会放宽对 git commit /
    # git push / 任意 Shell 命令的限制。写入范围仍被 Claude Code 自身限制在
    # 当前工作目录（cwd=project_root）内，这里没有传入 --add-dir，因此不会
    # 扩大到项目目录之外。
    args = [executable, "-p", prompt, "--permission-mode", "acceptEdits"]
    started = time.monotonic()
    try:
        completed = subprocess.run(
            args,
            cwd=project_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
        )
        duration = time.monotonic() - started
        return CommandResult(
            command=command_label,
            cwd=str(project_root),
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            duration_seconds=duration,
            timed_out=False,
        )
    except subprocess.TimeoutExpired as exc:
        # subprocess.run 在 TimeoutExpired 时已自动终止子进程
        duration = time.monotonic() - started
        stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", "replace")
        stderr = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr or b"").decode("utf-8", "replace")
        return CommandResult(
            command=command_label,
            cwd=str(project_root),
            exit_code=-1,
            stdout=stdout,
            stderr=stderr + "\n[Claude Code 执行超时，进程已终止]",
            duration_seconds=duration,
            timed_out=True,
        )
