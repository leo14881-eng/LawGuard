"""安全检查模块：统一实现命令白名单、路径越界拦截与密钥脱敏。

本模块是自动化系统的安全边界核心，其他模块不得绕过本模块自行拼接
shell 命令或放行未经校验的文件路径。
"""
from __future__ import annotations

import re
import shlex

# 允许自动执行的验证命令（严格白名单，按参数数组精确匹配，禁止任意拼接）
ALLOWED_VALIDATION_COMMANDS: list[list[str]] = [
    ["npm", "run", "build"],
    ["npm", "run", "test"],
    ["npm", "run", "lint"],
    ["npm", "run", "type-check"],
    ["npm", "run", "check"],
    ["npx", "vue-tsc", "--noEmit"],
    ["python", "-m", "pytest"],
    ["python", "-m", "unittest"],
    ["git", "diff", "--check"],
]

# 命令字符串中出现以下任意子串即直接拒绝（shell 元字符、危险指令片段）
_FORBIDDEN_COMMAND_SUBSTRINGS = [
    "&&", "||", "|", ">>", ">", "<", ";", "`", "$(", "%",
    "cmd /c", "cmd.exe", "powershell", "pwsh", "bash -c", "sh -c",
    "curl", "wget", "invoke-webrequest", "iwr ",
    "git push", "git reset", "git clean", "git checkout .",
    "git restore .", "git commit", "rm ", "rm-item", "del ",
    "rmdir", "remove-item",
]

# 疑似密钥模式：sk- 开头的字符串（含 sk-proj- 等变体，OpenAI 等服务常见密钥格式）
_SECRET_PATTERN = re.compile(r"sk-[A-Za-z0-9_\-]{6,}")
# 兜底模式：即便密钥不以 sk- 开头，也脱敏形如 KEY=xxx 的赋值形式，覆盖
# OPENAI_API_KEY 等变量名夹在日志/文本中的情况。刻意不匹配包裹值的引号本身，
# 避免误吞 JSON 报告中字符串的结束引号、破坏 JSON 结构。
_ASSIGNMENT_SECRET_PATTERN = re.compile(
    r"(?i)((?:OPENAI_API_KEY|API_KEY|SECRET_KEY)\s*[:=]\s*)([^\s\"',]+)"
)

# 禁止修改/访问的相对路径前缀（统一使用正斜杠比较）
FORBIDDEN_PATH_PREFIXES = [
    ".git",
    ".env.local",
    ".env",
    "node_modules",
    "dist",
    ".idea",
    ".vscode",
    "__pycache__",
    ".venv",
    "automation/runtime",
    "automation/reports",
]


def normalize_command(command: str) -> list[str] | None:
    """校验命令字符串并拆分为参数数组；不在白名单内返回 None。

    调用方必须使用返回的参数数组以列表形式执行命令，禁止 shell=True。
    """
    if not command or not isinstance(command, str):
        return None
    lowered = command.lower()
    for token in _FORBIDDEN_COMMAND_SUBSTRINGS:
        if token in lowered:
            return None
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        return None
    if not tokens:
        return None
    for allowed in ALLOWED_VALIDATION_COMMANDS:
        if tokens == allowed:
            return list(allowed)
    return None


def is_command_allowed(command: str) -> bool:
    """判断命令字符串是否命中验证命令白名单。"""
    return normalize_command(command) is not None


def _normalize_path_string(path_str: str) -> str | None:
    if path_str is None:
        return None
    p = path_str.strip()
    if not p:
        return None
    return p.replace("\\", "/")


def is_safe_relative_path(path_str: str) -> bool:
    """校验路径是否为项目内合法相对路径（不越界、非通配、非绝对路径）。"""
    p = _normalize_path_string(path_str)
    if p is None:
        return False
    if p in ("", ".", "/", "*"):
        return False
    if p.startswith("/") or p.startswith("~"):
        return False
    # 盘符路径，如 D:/xxx 或 D:\xxx
    if re.match(r"^[A-Za-z]:", p):
        return False
    # UNC 路径，如 //server/share
    if p.startswith("//") or p.startswith("\\\\"):
        return False
    parts = [seg for seg in p.split("/") if seg not in ("", ".")]
    if not parts:
        return False
    if ".." in parts:
        return False
    normalized = "/".join(parts)
    # Windows 文件系统不区分大小写，禁止路径的比较必须同样忽略大小写，
    # 否则 ".ENV.LOCAL"、"NODE_MODULES" 等大小写变体可绕过禁止列表。
    normalized_lower = normalized.lower()
    for forbidden in FORBIDDEN_PATH_PREFIXES:
        forbidden_lower = forbidden.lower()
        if normalized_lower == forbidden_lower or normalized_lower.startswith(forbidden_lower + "/"):
            return False
    return True


def check_files_lists(files_allowed: list[str], files_forbidden: list[str]) -> list[str]:
    """校验允许/禁止文件列表的合法性与冲突，返回问题列表（空列表表示通过）。"""
    issues: list[str] = []
    if not files_allowed:
        issues.append("files_allowed 不能为空")
    for f in files_allowed or []:
        if not is_safe_relative_path(f):
            issues.append(f"files_allowed 中存在非法路径：{f}")
    for f in files_forbidden or []:
        if not is_safe_relative_path(f):
            issues.append(f"files_forbidden 中存在非法路径：{f}")

    allowed_set = {_normalize_path_string(f) for f in (files_allowed or [])}
    forbidden_set = {_normalize_path_string(f) for f in (files_forbidden or [])}
    conflict = allowed_set & forbidden_set
    if conflict:
        issues.append(f"files_allowed 与 files_forbidden 冲突：{sorted(x for x in conflict if x)}")
    return issues


def redact_secrets(text: str) -> str:
    """对文本中的疑似密钥进行脱敏，用于日志与报告输出。

    覆盖两类情况：
    1. sk- 开头的字符串（含 sk-proj-、sk-org- 等变体）；
    2. 形如 OPENAI_API_KEY=xxx / "API_KEY": "xxx" 的赋值形式，即便取值不以 sk- 开头。
    """
    if not text:
        return text
    redacted = _SECRET_PATTERN.sub("sk-****REDACTED****", text)
    redacted = _ASSIGNMENT_SECRET_PATTERN.sub(r"\1****REDACTED****", redacted)
    return redacted
