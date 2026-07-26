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
    # LAWGUARD_SOT.md 只保存长期稳定事实，开发进度统一记录在
    # docs/project/AUTODEV_PROGRESS.md；Auto Dev 不得自动修改 LAWGUARD_SOT.md，
    # 此处在校验与提交两层同时拦截，不依赖 Planner Prompt 单方面遵守。
    "LAWGUARD_SOT.md",
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


def _is_structurally_safe_relative_path(path_str: str) -> bool:
    """只检查路径本身格式是否安全：非空、非绝对路径/盘符/UNC、不含目录穿越、非通配符。

    不检查是否命中 FORBIDDEN_PATH_PREFIXES——是否允许命中全局禁止前缀由调用方
    根据语境决定（见 is_safe_relative_path 与 is_safe_declared_forbidden_path）。
    """
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
    return True


def is_safe_relative_path(path_str: str) -> bool:
    """校验路径是否为项目内合法相对路径，且不命中全局禁止前缀。

    供 files_allowed（即将被 Claude 写入的文件）与实际 Git 提交文件列表使用，
    这两处都代表"即将被修改/提交"的路径，必须严格排除 `.env.local`、
    `LAWGUARD_SOT.md`、`.git` 等受保护路径。
    """
    if not _is_structurally_safe_relative_path(path_str):
        return False
    p = _normalize_path_string(path_str)
    parts = [seg for seg in p.split("/") if seg not in ("", ".")]
    normalized = "/".join(parts)
    # Windows 文件系统不区分大小写，禁止路径的比较必须同样忽略大小写，
    # 否则 ".ENV.LOCAL"、"NODE_MODULES" 等大小写变体可绕过禁止列表。
    normalized_lower = normalized.lower()
    for forbidden in FORBIDDEN_PATH_PREFIXES:
        forbidden_lower = forbidden.lower()
        if normalized_lower == forbidden_lower or normalized_lower.startswith(forbidden_lower + "/"):
            return False
    return True


def is_safe_declared_forbidden_path(path_str: str) -> bool:
    """校验 files_forbidden 中声明的路径本身格式是否合法。

    files_forbidden 表示"本次任务不允许修改"的路径；即使该路径恰好命中全局
    禁止前缀（如 LAWGUARD_SOT.md、.git、.env.local 等）也不是错误——把一个
    本就禁止的路径声明为"禁止修改"是合理且安全的冗余声明，不应导致 Planner
    输出被判定为非法（此前曾因此误伤 Planner 正常声明 LAWGUARD_SOT.md 为
    files_forbidden 的输出）。这里只做基础路径格式校验，不检查全局禁止前缀。
    """
    return _is_structurally_safe_relative_path(path_str)


def check_files_lists(files_allowed: list[str], files_forbidden: list[str]) -> list[str]:
    """校验允许/禁止文件列表的合法性与冲突，返回问题列表（空列表表示通过）。"""
    issues: list[str] = []
    if not files_allowed:
        issues.append("files_allowed 不能为空")
    for f in files_allowed or []:
        if not is_safe_relative_path(f):
            issues.append(f"files_allowed 中存在非法路径：{f}")
    for f in files_forbidden or []:
        if not is_safe_declared_forbidden_path(f):
            issues.append(f"files_forbidden 中存在非法路径：{f}")

    allowed_set = {_normalize_path_string(f) for f in (files_allowed or [])}
    forbidden_set = {_normalize_path_string(f) for f in (files_forbidden or [])}
    conflict = allowed_set & forbidden_set
    if conflict:
        issues.append(f"files_allowed 与 files_forbidden 冲突：{sorted(x for x in conflict if x)}")
    return issues


# Validation/Review 自动修复（Auto Fix）安全边界：命中任意一项即禁止继续自动重试，
# 即使任务原始风险等级为 LOW，也必须立即停止并交由人工决策（BLOCKED）。
# 关键词只扫描"本次改动新增的行"（diff 中以 + 开头的行）与 Claude 执行摘要，
# 不扫描项目已有代码，避免误伤与本次修复无关的既有内容。
_FIX_FORBIDDEN_KEYWORDS = [
    "数据库迁移", "drop table", "alter table", "delete from", "truncate table",
    "身份认证", "authentication", "authorization", "权限系统", "permission system",
    "role-based", "rbac", "密钥", "secret key", "secret_key", "api_key", "api key",
    "password", "支付", "收费", "payment gateway",
]

# 为让测试/验证"看起来通过"而弱化质量的常见写法，一旦出现在本次修复新增的行中，
# 视为不安全修复信号（对应 P-1/P0 之外、Auto Fix 自身治理要求的第五类禁止情形）。
_FIX_TEST_WEAKENING_PATTERNS = [
    "@ts-ignore", "@ts-nocheck", "eslint-disable", ".skip(", "xit(", "xdescribe(",
    "it.skip", "describe.skip", "test.skip",
]

# Claude 在执行摘要中报告"无法安全判断/需要人工决策"时使用的既定约定标记
# （见 claude_runner.py 的各 Prompt Builder），只要出现即视为需要人工决策。
_UNSAFE_STDOUT_MARKERS = ["blocked", "需要人工决策", "无法安全判断"]


def _added_diff_lines(diff_text: str) -> str:
    """从 unified diff 中提取本次改动新增的行（以 + 开头，排除 +++ 文件头）。"""
    lines: list[str] = []
    for line in (diff_text or "").splitlines():
        if line.startswith("+++"):
            continue
        if line.startswith("+"):
            lines.append(line[1:])
    return "\n".join(lines)


def detect_unsafe_fix_signal(*, claude_stdout: str, diff_text: str) -> str | None:
    """检测 Validation/Review 自动修复本轮是否出现禁止继续自动重试的信号。

    命中任意一项时返回中文原因说明（调用方应立即停止、标记 BLOCKED，不得继续重试）；
    未命中返回 None。这是一个有意保持简单、可解释的关键词/模式黑名单检测，不做语义
    理解——宁可对可疑内容保守拦截，也不在自动化流水线中静默放行敏感改动。
    """
    stdout_lower = (claude_stdout or "").lower()
    for marker in _UNSAFE_STDOUT_MARKERS:
        if marker in stdout_lower:
            return f"Claude 在执行摘要中报告了「{marker}」，视为需要人工决策"

    added_lines_lower = _added_diff_lines(diff_text).lower()

    for keyword in _FIX_FORBIDDEN_KEYWORDS:
        if keyword in added_lines_lower or keyword in stdout_lower:
            return f"改动或执行摘要中出现禁止自动修复的敏感内容关键词：{keyword}"

    for pattern in _FIX_TEST_WEAKENING_PATTERNS:
        if pattern.lower() in added_lines_lower:
            return f"改动中检测到疑似削弱测试/绕过类型检查的写法：{pattern}"

    return None


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
