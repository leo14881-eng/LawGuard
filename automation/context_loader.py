"""项目上下文读取模块：为 OpenAI 规划器与评审器准备受限、可控大小的项目上下文。

只读取项目根目录内的信息，不递归读取全部源码全文，
并对发送给 OpenAI 的内容设置长度上限，超出时截断并明确标记。
"""
from __future__ import annotations

from pathlib import Path

from automation import backlog
from automation import config as cfg
from automation import progress as progress_mod
from automation import value_gate
from automation.git_service import GitService
from automation.models import CommandResult, DevelopmentTask

# 生成文件树时忽略的目录名
_IGNORE_DIR_NAMES = {
    ".git", "node_modules", "dist", ".idea", ".vscode",
    "__pycache__", ".venv",
}
# 生成文件树时忽略的相对路径（自动化系统自身的运行产物）
_IGNORE_RELATIVE_DIRS = {"automation/runtime", "automation/reports"}

_MAX_TREE_FILES = 400
_MAX_TREE_DEPTH = 6
_MAX_FIELD_CHARS = 6000
_MAX_TOTAL_CHARS = 20000
# Validation/Review Fix Prompt 中"当前任务 Git Diff"小节的字符上限，与其余发送给
# 模型的上下文使用同一套"明确截断标记、不静默丢弃"的规则（见 build_diff_for_prompt）。
_MAX_DIFF_PROMPT_CHARS = 8000

# 规划器只需要"当前能做什么、还差什么"这类信息即可决策下一步开发任务；
# P-1/P0/P1/P2 等最高治理原则已经在 planner_system.txt 中以编号方式引用，
# 不需要在每次请求的上下文里重复发送整章原文，借此显著压缩 Token 消耗。
# LAWGUARD_SOT.md 只保存长期稳定事实，不再包含开发进度/下一步计划相关章节
# （职责已统一收归 docs/project/AUTODEV_PROGRESS.md，见下方 progress_mod），
# 因此这里不再提取"当前开发进度""下一步计划"等章节关键词。
_SOT_PLANNER_SECTION_KEYWORDS = (
    "V1 功能范围", "V1 明确不做", "页面清单", "Product Backlog",
)
_CLAUDE_MD_PLANNER_SECTION_KEYWORDS = (
    "项目状态", "仓库结构", "常用命令", "架构说明",
)


def _extract_markdown_sections(text: str, keywords: tuple[str, ...]) -> str:
    """从 Markdown 文本中只提取二级标题（"## "）包含给定关键词的章节。

    用于把发送给 OpenAI 的上下文限制为规划所需的必要章节，而不是整份文档全文。
    找不到任何匹配章节时返回空字符串，调用方应回退到全文（避免因关键词漂移而
    丢失全部上下文）。
    """
    lines = text.splitlines()
    sections: list[str] = []
    current: list[str] | None = None
    for line in lines:
        if line.startswith("## "):
            if current is not None:
                sections.append("\n".join(current))
            current = [line] if any(kw in line for kw in keywords) else None
        elif current is not None:
            current.append(line)
    if current is not None:
        sections.append("\n".join(current))
    return "\n\n".join(sections)


def _truncate(text: str, limit: int) -> str:
    if text is None:
        return ""
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n...[内容过长，已截断，原始长度 {len(text)} 字符]"


def _read_text(path: Path, limit: int = _MAX_FIELD_CHARS) -> str:
    if not path.exists():
        return "（文件不存在）"
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return f"（读取失败：{exc}）"
    return _truncate(text, limit)


def _should_ignore(rel_path: Path) -> bool:
    rel_str = rel_path.as_posix()
    if rel_str in _IGNORE_RELATIVE_DIRS:
        return True
    return any(part in _IGNORE_DIR_NAMES for part in rel_path.parts)


def build_file_tree(root: Path) -> str:
    """生成受限的项目文件树文本，限制最大文件数与最大深度。"""
    lines: list[str] = []
    state = {"file_count": 0, "truncated": False}

    def walk(dir_path: Path, depth: int) -> None:
        if state["truncated"] or depth > _MAX_TREE_DEPTH:
            return
        try:
            entries = sorted(dir_path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        except OSError:
            return
        for entry in entries:
            if state["truncated"]:
                return
            rel = entry.relative_to(root)
            if _should_ignore(rel):
                continue
            indent = "  " * depth
            if entry.is_dir():
                lines.append(f"{indent}{entry.name}/")
                walk(entry, depth + 1)
            else:
                if state["file_count"] >= _MAX_TREE_FILES:
                    lines.append(f"{indent}...[文件数已达上限 {_MAX_TREE_FILES}，已截断]")
                    state["truncated"] = True
                    return
                lines.append(f"{indent}{entry.name}")
                state["file_count"] += 1

    walk(root, 0)
    return "\n".join(lines)


def build_planner_context() -> str:
    """构建供 OpenAI 规划器使用的项目上下文文本。"""
    root = cfg.PROJECT_ROOT
    git = GitService(root)

    sot_full = _read_text(cfg.SOT_FILE)
    sot_sections = _extract_markdown_sections(sot_full, _SOT_PLANNER_SECTION_KEYWORDS)
    sot = sot_sections or sot_full  # 关键词未命中任何章节时回退全文，避免上下文丢失

    claude_md_full = _read_text(cfg.CLAUDE_MD_FILE)
    claude_md_sections = _extract_markdown_sections(claude_md_full, _CLAUDE_MD_PLANNER_SECTION_KEYWORDS)
    claude_md = claude_md_sections or claude_md_full

    package_json = _read_text(cfg.WEB_DIR / "package.json", 2000)
    file_tree = build_file_tree(root)
    recent_log = git.get_recent_log(5)
    status = git.get_status_short()
    progress_state, _, _ = progress_mod.load_or_repair(cfg.PROGRESS_FILE)
    progress_section = progress_mod.build_planner_context_section(progress_state)

    recent_task_history = value_gate.load_recent_tasks(cfg.RUNTIME_DIR, limit=30)
    capability_matrix_text = value_gate.build_capability_matrix_context()
    repetition_text = value_gate.build_repetition_context(recent_task_history)
    backlog_text = backlog.build_planner_backlog_context(cfg.RUNTIME_DIR)

    parts = [
        progress_section,
        "",
        backlog_text,
        "",
        capability_matrix_text,
        "",
        repetition_text,
        "",
        "## LAWGUARD_SOT.md 摘录（仅规划相关章节：功能范围/页面清单/开发进度/下一步计划；"
        "P-1/P0/P1/P2 等治理原则已在系统提示中以编号引用，此处不重复全文）",
        sot,
        "",
        "## CLAUDE.md 摘录（仅规划相关章节：项目状态/仓库结构/常用命令/架构说明）",
        claude_md,
        "",
        "## web/package.json",
        package_json,
        "",
        "## 项目文件树（已忽略 node_modules/dist/.git 等目录，数量与深度均有上限）",
        file_tree,
        "",
        "## 最近 5 条 Git 提交",
        recent_log or "（无提交记录）",
        "",
        "## 当前 Git 状态（git status --short）",
        status or "（工作区干净）",
        "",
        "## 自动化系统边界提醒",
        (
            "本次任务将由 Claude Code 在本地非交互执行，只能修改 files_allowed 中列出的文件，"
            "不得修改 LAWGUARD_SOT.md（除非任务明确要求且必要），不得引入后端/数据库/登录/"
            "在线咨询/AI 聊天等 V1 明确禁止的能力。"
        ),
    ]
    context_text = "\n".join(parts)
    return _truncate(context_text, _MAX_TOTAL_CHARS)


def build_reviewer_context(
    *,
    task: DevelopmentTask,
    claude_result: CommandResult,
    validation_results: list[CommandResult],
) -> str:
    """构建供 OpenAI 评审器使用的评审上下文文本。"""
    root = cfg.PROJECT_ROOT
    git = GitService(root)

    diff_stat = _truncate(git.get_diff_stat(), 2000)
    diff = _truncate(git.get_diff(), 12000)
    status = _truncate(git.get_status_short(), 2000)
    file_tree = build_file_tree(root)

    validation_text_lines = []
    for r in validation_results:
        status_text = "超时" if r.timed_out else ("通过" if r.exit_code == 0 else "失败")
        validation_text_lines.append(
            f"- 命令：{r.command}\n  工作目录：{r.cwd}\n  结果：{status_text}（退出码 {r.exit_code}，"
            f"耗时 {r.duration_seconds:.1f} 秒）\n  stderr 摘要：{_truncate(r.stderr, 500)}"
        )
    validation_text = "\n".join(validation_text_lines) or "（无验证记录）"

    claude_summary = (
        f"退出码：{claude_result.exit_code}；是否超时：{claude_result.timed_out}；"
        f"耗时：{claude_result.duration_seconds:.1f} 秒\n"
        f"stdout 摘要：{_truncate(claude_result.stdout, 3000)}\n"
        f"stderr 摘要：{_truncate(claude_result.stderr, 1000)}"
    )

    task_json_lines = [
        f"task_id: {task.task_id}",
        f"title: {task.title}",
        f"objective: {task.objective}",
        f"scope: {task.scope}",
        f"acceptance_criteria: {task.acceptance_criteria}",
        f"files_allowed: {task.files_allowed}",
        f"files_forbidden: {task.files_forbidden}",
        f"validation_commands: {task.validation_commands}",
        f"risk_level: {task.risk_level}",
        f"requires_sot_update: {task.requires_sot_update}",
    ]

    parts = [
        "## 原始任务",
        "\n".join(task_json_lines),
        "",
        "## Claude Code 执行结果",
        claude_summary,
        "",
        "## Git diff --stat",
        diff_stat or "（无改动）",
        "",
        "## Git diff",
        diff or "（无改动）",
        "",
        "## Git status --short",
        status or "（工作区干净）",
        "",
        "## 自动验证结果",
        validation_text,
        "",
        "## 当前项目结构（受限文件树）",
        file_tree,
    ]
    context_text = "\n".join(parts)
    return _truncate(context_text, _MAX_TOTAL_CHARS)


def truncate_for_prompt(text: str, limit: int = _MAX_FIELD_CHARS) -> str:
    """公开的文本截断工具，供 orchestrator 构建 Validation/Review Fix Prompt 时复用，
    与发送给 OpenAI 的上下文使用同一套"超出上限即截断并显式标记"的规则。
    """
    return _truncate(text, limit)


def build_diff_for_prompt(diff_text: str) -> str:
    """为 Validation/Review Fix Prompt 准备"当前任务 Git Diff"小节。

    过长时截断，但保留改动文件列表（diff --git 头部行）与正文起始部分，并在截断处
    显式标记"[Diff 已截断]"，不静默丢弃内容，便于 Claude 判断本次修复的完整改动范围。
    """
    if not diff_text or not diff_text.strip():
        return "（无改动）"
    if len(diff_text) <= _MAX_DIFF_PROMPT_CHARS:
        return diff_text

    file_headers = [line for line in diff_text.splitlines() if line.startswith("diff --git ")]
    file_list_text = "\n".join(file_headers) or "（未解析到文件列表）"
    body_limit = max(_MAX_DIFF_PROMPT_CHARS - len(file_list_text) - 200, 1000)
    truncated_body = diff_text[:body_limit]
    return (
        f"改动文件列表：\n{file_list_text}\n\n"
        f"{truncated_body}\n"
        f"...[Diff 已截断，原始长度 {len(diff_text)} 字符]"
    )


def build_validation_summary_text(validation_results: list[CommandResult]) -> str:
    """把本轮全部验证命令的结果格式化为简短文本，用于 Fix Prompt 的"其他验证结果"小节。"""
    if not validation_results:
        return "（无验证记录）"
    lines = []
    for r in validation_results:
        status = "超时" if r.timed_out else ("通过" if r.exit_code == 0 else "失败")
        lines.append(f"- {r.command}：{status}（退出码 {r.exit_code}，耗时 {r.duration_seconds:.1f} 秒）")
    return "\n".join(lines)
