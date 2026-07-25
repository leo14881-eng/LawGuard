"""自动验证模块：执行固定基础验证与任务附加验证命令，产出结构化结果。

不自动安装依赖；命令均以参数数组执行，禁止 shell=True。
"""
from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path

from automation.models import CommandResult
from automation.security import normalize_command

_COMMAND_TIMEOUT_SECONDS = 900


def _resolve_executable(name: str) -> str:
    """解析命令首个 token 对应的可执行文件（处理 Windows 下 npm/npx 的 .cmd 后缀）。"""
    if name in ("npm", "npx"):
        for candidate in (f"{name}.cmd", f"{name}.exe", name):
            found = shutil.which(candidate)
            if found:
                return found
    return name


def _run_command(tokens: list[str], cwd: Path, label: str) -> CommandResult:
    exe = _resolve_executable(tokens[0])
    args = [exe, *tokens[1:]]
    started = time.monotonic()
    try:
        completed = subprocess.run(
            args,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=_COMMAND_TIMEOUT_SECONDS,
        )
        duration = time.monotonic() - started
        return CommandResult(
            command=label,
            cwd=str(cwd),
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            duration_seconds=duration,
            timed_out=False,
        )
    except FileNotFoundError:
        duration = time.monotonic() - started
        return CommandResult(
            command=label,
            cwd=str(cwd),
            exit_code=-1,
            stdout="",
            stderr=f"命令未找到，可能缺少依赖，请手动确认后重试：{label}",
            duration_seconds=duration,
            timed_out=False,
        )
    except subprocess.TimeoutExpired as exc:
        duration = time.monotonic() - started
        stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", "replace")
        stderr = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr or b"").decode("utf-8", "replace")
        return CommandResult(
            command=label,
            cwd=str(cwd),
            exit_code=-1,
            stdout=stdout,
            stderr=stderr + "\n[命令执行超时，已终止]",
            duration_seconds=duration,
            timed_out=True,
        )


def run_validation(
    *,
    project_root: Path,
    web_dir: Path,
    extra_commands: list[str],
) -> tuple[list[CommandResult], bool]:
    """执行基础验证与任务附加验证命令，返回 (结果列表, 是否全部通过)。"""
    results: list[CommandResult] = []
    executed_signatures: set[tuple[str, str]] = set()
    state = {"all_passed": True}

    def run_and_record(tokens: list[str], cwd: Path, label: str) -> None:
        signature = (label, str(cwd))
        if signature in executed_signatures:
            return
        executed_signatures.add(signature)
        result = _run_command(tokens, cwd, label)
        results.append(result)
        if result.exit_code != 0 or result.timed_out:
            state["all_passed"] = False

    # 固定基础验证 1：git diff --check
    run_and_record(["git", "diff", "--check"], project_root, "git diff --check")

    # 固定基础验证 2：若存在 web/package.json，则在 web 目录执行 npm run build
    if (web_dir / "package.json").exists():
        run_and_record(["npm", "run", "build"], web_dir, "npm run build")

    # 任务附加验证命令（已在规划阶段通过白名单校验，此处再次校验以防御性检查）
    for command in extra_commands or []:
        tokens = normalize_command(command)
        if tokens is None:
            results.append(
                CommandResult(
                    command=command,
                    cwd=str(project_root),
                    exit_code=-1,
                    stdout="",
                    stderr="命令未通过安全白名单校验，已跳过执行。",
                    duration_seconds=0.0,
                    timed_out=False,
                )
            )
            state["all_passed"] = False
            continue
        cwd = web_dir if tokens[0] in ("npm", "npx") and web_dir.exists() else project_root
        run_and_record(tokens, cwd, " ".join(tokens))

    return results, state["all_passed"]
