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


# 【2026-07-26 修复】Task #8（Privacy 页面新增打印按钮）真实误判：Claude
# 因为 Bash 工具需要审批、暂时无法执行 `npm run build`，在执行摘要里写"命令被
# 权限系统拦截，需要你手动批准后我才能继续执行验证"——这里的"权限系统"指
# Claude Code 自身的工具审批沙箱，与本项目要不要实现用户登录/角色权限系统
# 毫无关系；实际代码 Diff 只是新增两行"引入并渲染 PrintPageButton"，不含任何
# 敏感内容。旧逻辑对 `added_lines_lower`（Diff 新增行）和 `stdout_lower`
# （Claude 执行摘要）两处都做关键词包含判断，导致 Claude 在摘要里提到自己的
# 工具权限受限、或以否定句提到某个词时也会被误伤。
#
# 修复：安全停止必须基于"Diff 里真实发生的代码行为"，不能基于 Claude 用自然
# 语言怎么描述这件事——本类关键词现在只扫描 Diff 新增行，不再扫描 Claude 执行
# 摘要；任务描述（DevelopmentTask 的 title/objective/scope 等）从未参与本类
# 扫描（detect_unsafe_fix_signal 的入参本就只有 claude_stdout 与 diff_text，
# 不接收任务对象），只用于人类理解任务，不作为阻塞证据。Claude 摘要唯一还能
# 触发停止的路径是上面的 _EXPLICIT_HUMAN_BLOCK_PHRASES（明确表达"需要人工
# 决策"意图的完整短语），与这里的关键词表相互独立。
#
# 关键词/模式本身仍然只保持简单、可解释的黑名单，但收紧为具体的 API 名称/
# 组合短语，避免用会在正常代码里频繁出现的孤立单词（例如本项目 CSS 里到处
# 都是"Design Token"、无障碍属性里到处都是 `role="listitem"`，如果收录裸词
# "token"/"role" 会把几乎所有页面改动都误伤）。
_FIX_FORBIDDEN_KEYWORDS = [
    # 数据库迁移/删除数据（本项目无数据库，出现即视为异常）
    "数据库迁移", "drop table", "alter table", "delete from", "truncate table",
    # 新增或修改登录认证逻辑
    "身份认证", "authentication", "authorization", "password hash", "password_hash",
    # 新增或修改角色、权限、授权判断
    "权限系统", "permission system", "role-based", "rbac", "acl", "haspermission",
    "has_permission", "hasrole", "has_role", "checkpermission", "check_permission",
    "isadmin", "is_admin", "grantaccess", "grant_access",
    # 修改路由守卫（Vue Router 具体 API，不是泛泛的"路由"一词）
    "router.beforeeach", "router.beforeresolve", "beforeenter", "beforerouteenter",
    "navigation guard",
    # 中间件（本项目为纯静态 SPA，无后端/中间件，出现即视为异常）
    "middleware",
    # token/session/cookie 安全逻辑（用具体组合短语，不用会在正常代码里出现的
    # 裸词 "token"/"session"/"cookie"）
    "access_token", "access token", "auth_token", "auth token", "session_token",
    "csrf_token", "csrf token", "document.cookie", "set-cookie", "jwt.sign", "jsonwebtoken",
    # 密钥/支付
    "密钥", "secret key", "secret_key", "api_key", "api key", "password",
    "支付", "收费", "payment gateway",
]

# 为让测试/验证"看起来通过"而弱化质量的常见写法，一旦出现在本次修复新增的行中，
# 视为不安全修复信号（对应 P-1/P0 之外、Auto Fix 自身治理要求的第五类禁止情形）。
_FIX_TEST_WEAKENING_PATTERNS = [
    "@ts-ignore", "@ts-nocheck", "eslint-disable", ".skip(", "xit(", "xdescribe(",
    "it.skip", "describe.skip", "test.skip",
]

# 【2026-07-26 修复】原实现是 `"blocked" in stdout_lower` 这种单词包含判断，
# 造成 Task #4（Official Channels 页面新增打印按钮）真实误判：Claude 因为
# Claude Code 非交互环境下 Bash 工具权限受限、无法实际执行 `npx vue-tsc`/
# `npm run build`，在执行摘要里写了"验证结果：BLOCKED —— 无法执行验证命令"，
# 本意是"请人工在有权限的环境里手动跑一遍验证命令"，属于工具/环境限制，
# 不是需要人工做产品/法律/安全层面决策；但旧逻辑只要文本里出现"blocked"这个
# 单词就直接停止，把这类场景、以及"no blockers"/"not blocked"/
# "blockers: none"等否定语境全部一并误伤。
#
# 新实现改为"短语级"匹配，不再对 blocked/blocker/human 等单词做裸词包含判断：
# 1. 先在文本中挖掉已知的否定短语（_NEGATED_HUMAN_BLOCK_PHRASES），避免它们
#    被后续的正向短语判断命中；
# 2. 只有命中明确表达"需要人工决策/无法安全继续"意图的完整短语
#    （_EXPLICIT_HUMAN_BLOCK_PHRASES）才判定为需要人工决策。
# claude_runner.py 的 P0 Prompt 约定 Claude 在缺少可核验法律来源时应写
# "BLOCKED：缺少可核验法律来源"，这里改为直接匹配"缺少可核验法律来源"这个
# 无歧义的具体短语，不再依赖单独的"BLOCKED"一词，同样能可靠捕获该场景。
_NEGATED_HUMAN_BLOCK_PHRASES = [
    "no blockers", "no blocker", "not blocked", "no blocked issues",
    "nothing is blocked", "no human decision needed", "no human decision is needed",
    "does not require human input", "doesn't require human input",
    "does not need human input", "doesn't need human input",
    "blocked issues: none", "blockers: none", "blocker: none", "blocked: none",
    "未阻塞", "无阻塞项", "没有阻塞问题", "没有阻塞项", "不需要人工决策",
    "无需用户确认", "不涉及人工选择", "无需人工决策",
]

_EXPLICIT_HUMAN_BLOCK_PHRASES = [
    "i am blocked and need human input",
    "i'm blocked and need human input",
    "requires human decision",
    "requires a human decision",
    "requires human input",
    "requires human approval",
    "require human approval",
    "cannot proceed without user confirmation",
    "cannot proceed without human",
    "cannot safely proceed",
    "cannot safely continue",
    "need human input",
    "needs human input",
    "need a human decision",
    "needs a human decision",
    "需要人工决策",
    "需要用户确认",
    "需要用户选择",
    "需要人工确认",
    "无法继续，需要用户确认",
    "无法安全继续",
    "无法安全判断",
    "无法安全地继续执行",
    "缺少可核验法律来源",
    "涉及法律内容，无法自动判断",
    "涉及安全或权限设计，需要人工批准",
]


def _added_diff_lines(diff_text: str) -> str:
    """从 unified diff 中提取本次改动新增的行（以 + 开头，排除 +++ 文件头）。"""
    lines: list[str] = []
    for line in (diff_text or "").splitlines():
        if line.startswith("+++"):
            continue
        if line.startswith("+"):
            lines.append(line[1:])
    return "\n".join(lines)


def _contains_explicit_human_block_phrase(stdout_lower: str) -> str | None:
    """在排除已知否定短语后，判断文本中是否出现明确的"需要人工决策"短语。

    先把命中的否定短语从文本中挖掉（替换为空格），再去匹配正向短语列表，避免
    "no human decision needed" 这类否定句里恰好包含 "human decision" 从而被
    误判。返回命中的具体短语；未命中返回 None。
    """
    masked = stdout_lower
    for phrase in _NEGATED_HUMAN_BLOCK_PHRASES:
        if phrase in masked:
            masked = masked.replace(phrase, " ")

    for phrase in _EXPLICIT_HUMAN_BLOCK_PHRASES:
        if phrase in masked:
            return phrase
    return None


def detect_unsafe_fix_signal(*, claude_stdout: str, diff_text: str) -> str | None:
    """检测 Validation/Review 自动修复本轮是否出现禁止继续自动重试的信号。

    命中任意一项时返回中文原因说明（调用方应立即停止、标记 BLOCKED，不得继续重试）；
    未命中返回 None。这是一个有意保持简单、可解释的关键词/模式黑名单检测，不做语义
    理解——宁可对可疑内容保守拦截，也不在自动化流水线中静默放行敏感改动；但"是否
    需要人工决策"这一项改为短语级匹配（见 _EXPLICIT_HUMAN_BLOCK_PHRASES /
    _NEGATED_HUMAN_BLOCK_PHRASES 上方注释），不再对 blocked/blocker/human 等
    单词做裸词包含判断，避免把"no blockers""not blocked"等否定语境或
    "验证结果：BLOCKED——因权限受限无法执行验证命令"这类工具/环境限制说明误判为
    需要人工做产品/法律/安全决策。

    敏感关键词/危险修复写法两类检测（见 _FIX_FORBIDDEN_KEYWORDS /
    _FIX_TEST_WEAKENING_PATTERNS 上方注释）只扫描 Diff 新增行，不扫描 Claude
    执行摘要——安全停止必须基于"代码里真实发生了什么"，不是"Claude 用自然语言
    怎么描述这件事"；Claude 摘要在提到自己工具受限、或以否定句提到某个敏感词时
    （例如 Task #8"命令被权限系统拦截"，指 Claude Code 自身的工具审批沙箱，与
    应用本身要不要做权限系统无关）都不应触发。任务描述（DevelopmentTask）从未
    参与这两类扫描，本函数入参本就不接收任务对象。
    """
    stdout_lower = (claude_stdout or "").lower()

    matched_phrase = _contains_explicit_human_block_phrase(stdout_lower)
    if matched_phrase:
        return f"Claude 在执行摘要中明确表示需要人工决策：「{matched_phrase}」"

    added_lines_lower = _added_diff_lines(diff_text).lower()

    for keyword in _FIX_FORBIDDEN_KEYWORDS:
        if keyword in added_lines_lower:
            return f"本次改动新增的代码中出现禁止自动修复的敏感内容关键词：{keyword}"

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
