"""Auto Dev 进度管理模块：维护 docs/project/AUTODEV_PROGRESS.md。

这是 Auto Dev 全自动循环专属的进度台账，用于让 Planner 在下一轮规划时知道哪些任务
已经完成，避免重复开发；与 LAWGUARD_SOT.md 的"当前开发进度"章节相互独立——本模块
不读写 LAWGUARD_SOT.md，也不修改任何法律内容治理规则。
"""
from __future__ import annotations

import dataclasses
from pathlib import Path

_HEADER = "# Auto Dev Progress"
_SECTIONS = (
    "Project Stage",
    "Last Update",
    "Last Commit",
    "Completed Tasks",
    "Current Task",
    "Next Candidate Tasks",
    "Known Issues",
)

_DEFAULT_PROJECT_STAGE = "LawGuard V1 —— Auto Dev 全自动开发循环"
_DEFAULT_CURRENT_TASK = "（无，等待 Planner 规划下一任务）"
_NOT_STARTED = "（尚未开始）"
_NONE_TEXT = "（无）"


@dataclasses.dataclass
class ProgressState:
    """AUTODEV_PROGRESS.md 的结构化表示。"""

    project_stage: str
    last_update: str
    last_commit: str
    completed_tasks: list[str]
    current_task: str
    next_candidate_tasks: list[str]
    known_issues: list[str]


def default_state() -> ProgressState:
    """全新项目或进度文件缺失/损坏时使用的初始状态。"""
    return ProgressState(
        project_stage=_DEFAULT_PROJECT_STAGE,
        last_update=_NOT_STARTED,
        last_commit=_NONE_TEXT,
        completed_tasks=[],
        current_task=_DEFAULT_CURRENT_TASK,
        next_candidate_tasks=[],
        known_issues=[],
    )


def _render_list(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else _NONE_TEXT


def render(state: ProgressState) -> str:
    """按固定模板渲染进度文件内容。"""
    return (
        f"{_HEADER}\n\n"
        f"## Project Stage\n{state.project_stage}\n\n"
        f"## Last Update\n{state.last_update}\n\n"
        f"## Last Commit\n{state.last_commit}\n\n"
        f"## Completed Tasks\n{_render_list(state.completed_tasks)}\n\n"
        f"## Current Task\n{state.current_task}\n\n"
        f"## Next Candidate Tasks\n{_render_list(state.next_candidate_tasks)}\n\n"
        f"## Known Issues\n{_render_list(state.known_issues)}\n"
    )


def _extract_section(lines: list[str], heading: str) -> list[str] | None:
    marker = f"## {heading}"
    if marker not in lines:
        return None
    start = lines.index(marker) + 1
    collected: list[str] = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        collected.append(line)
    while collected and not collected[-1].strip():
        collected.pop()
    while collected and not collected[0].strip():
        collected.pop(0)
    return collected


def parse(text: str) -> ProgressState | None:
    """解析进度文件；缺少必需章节视为格式异常，返回 None 由调用方触发自动修复。"""
    if _HEADER not in text:
        return None
    lines = text.splitlines()
    raw: dict[str, list[str]] = {}
    for heading in _SECTIONS:
        section_lines = _extract_section(lines, heading)
        if section_lines is None:
            return None
        raw[heading] = section_lines

    def _text(heading: str, default: str) -> str:
        joined = "\n".join(raw[heading]).strip()
        return joined or default

    def _items(heading: str) -> list[str]:
        items: list[str] = []
        for line in raw[heading]:
            stripped = line.strip()
            if not stripped or stripped == _NONE_TEXT:
                continue
            items.append(stripped[2:].strip() if stripped.startswith("- ") else stripped)
        return items

    return ProgressState(
        project_stage=_text("Project Stage", _DEFAULT_PROJECT_STAGE),
        last_update=_text("Last Update", _NOT_STARTED),
        last_commit=_text("Last Commit", _NONE_TEXT),
        completed_tasks=_items("Completed Tasks"),
        current_task=_text("Current Task", _DEFAULT_CURRENT_TASK),
        next_candidate_tasks=_items("Next Candidate Tasks"),
        known_issues=_items("Known Issues"),
    )


def write(path: Path, state: ProgressState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render(state), encoding="utf-8")


def load_or_repair(path: Path) -> tuple[ProgressState, bool, bool]:
    """启动恢复入口：读取进度文件，不存在则创建，格式异常则重建默认模板。

    返回 (state, was_missing, was_repaired)。永远返回一个可用状态，调用方不应
    因文件缺失或损坏而停止运行；损坏时不做猜测式修补，直接以默认模板重建，
    避免把无法确认真实性的残缺数据当作项目进度使用。
    """
    if not path.exists():
        state = default_state()
        write(path, state)
        return state, True, False

    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        state = default_state()
        write(path, state)
        return state, False, True

    state = parse(text)
    if state is None:
        state = default_state()
        write(path, state)
        return state, False, True

    return state, False, False


def record_completed_task(
    path: Path,
    *,
    task_number: int,
    task_title: str,
    commit_hash: str,
    now_iso: str,
    next_candidate_tasks: list[str],
) -> ProgressState:
    """任务 Review PASS 且 Git Commit 成功后调用：追加已完成任务并写回文件。"""
    state, _, _ = load_or_repair(path)
    new_state = ProgressState(
        project_stage=state.project_stage,
        last_update=now_iso,
        last_commit=commit_hash,
        completed_tasks=[*state.completed_tasks, f"task-{task_number:03d}: {task_title}"],
        current_task=_DEFAULT_CURRENT_TASK,
        next_candidate_tasks=next_candidate_tasks,
        known_issues=state.known_issues,
    )
    write(path, new_state)
    return new_state


def build_planner_context_section(state: ProgressState) -> str:
    """生成供 Planner 上下文使用的进度台账摘要，提示不要重复规划已完成任务。"""
    return (
        "## Auto Dev 进度台账（docs/project/AUTODEV_PROGRESS.md，禁止重复规划 Completed "
        "Tasks 中已完成的任务）\n"
        f"Project Stage：{state.project_stage}\n"
        f"Last Update：{state.last_update}\n"
        f"Last Commit：{state.last_commit}\n"
        f"Current Task：{state.current_task}\n"
        "Completed Tasks：\n"
        f"{_render_list(state.completed_tasks)}\n"
        "Next Candidate Tasks（参考 LAWGUARD_SOT.md 下一步计划，仅供参考，具体任务仍由 "
        "Planner 决策）：\n"
        f"{_render_list(state.next_candidate_tasks)}"
    )
