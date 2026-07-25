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
    command_label = f"claude -p <task_prompt, {len(prompt)} 字符>"

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

    args = [executable, "-p", prompt]
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
