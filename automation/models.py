"""数据模型定义：贯穿整个自动化流程的核心数据结构。"""
from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass
from typing import Any

# 任务风险等级允许的取值：
# LOW/MEDIUM/HIGH 为正常任务的风险分级；
# DONE 表示当前项目已没有新的开发任务（正常结束）；
# BLOCKED 表示存在可规划的开发方向，但由于权限、依赖、环境、资源不足，
# 或 P-1/P0/P1/P2 治理原则要求（例如缺少可核验法律来源、涉及个案判断）
# 而无法安全生成具体任务。
RISK_LEVELS = {"LOW", "MEDIUM", "HIGH", "BLOCKED", "DONE"}
# 评审结论允许的取值
REVIEW_VERDICTS = {"PASS", "FAIL", "BLOCKED"}


@dataclass
class DevelopmentTask:
    """OpenAI 规划器（CTO 角色）生成的下一项开发任务。"""

    task_id: str
    title: str
    objective: str
    rationale: str
    scope: str
    acceptance_criteria: list[str]
    files_allowed: list[str]
    files_forbidden: list[str]
    validation_commands: list[str]
    risk_level: str
    requires_sot_update: bool
    developer_prompt: str

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclass
class CommandResult:
    """一次命令执行的结果记录。"""

    command: str
    cwd: str
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclass
class TokenUsage:
    """一次 OpenAI Responses API 调用的 Token 用量记录。

    字段在 API 未返回对应用量信息时为 None（例如 SDK 版本差异、调用异常提前返回），
    报告展示时一律显示"Unknown"，不进行任何估算或猜测。
    """

    call_label: str
    model: str
    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclass
class ReviewResult:
    """OpenAI 评审器的评审结论。"""

    verdict: str
    summary: str
    blocking_issues: list[str]
    non_blocking_suggestions: list[str]
    evidence: list[str]
    safe_to_commit: bool
    commit_message: str

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclass
class RunReport:
    """一次运行的完整报告。"""

    run_id: str
    started_at: str
    finished_at: str | None
    task: DevelopmentTask | None
    claude_result: CommandResult | None
    validation_results: list[CommandResult]
    review: ReviewResult | None
    git_commit: str | None
    final_status: str
    error_message: str | None
    token_usages: list[TokenUsage] = dataclasses.field(default_factory=list)
    # Auto Fix Attempt 记录：一个任务从初次执行到最终成功/停止的每一个 Attempt
    # （INITIAL 初次执行 / VALIDATION_FIX Validation 自动修复 / REVIEW_FIX Review
    # 自动修复，三者共享同一个最大 Attempt 数）。每项字典包含：
    # attempt_number、prompt_type、claude_started_at/claude_finished_at/
    # claude_duration_seconds、changed_files、validation_passed/
    # validation_duration_seconds、failed_command、review_verdict/review_summary/
    # blocking_issues/review_duration_seconds、retry_reason、
    # proceeded_to_next_attempt。字段名沿用早期 Review Retry 阶段的
    # `review_attempts`，保持与已有报告读取逻辑兼容。
    review_attempts: list[dict[str, Any]] = dataclasses.field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "task": self.task.to_dict() if self.task else None,
            "claude_result": self.claude_result.to_dict() if self.claude_result else None,
            "validation_results": [r.to_dict() for r in self.validation_results],
            "review": self.review.to_dict() if self.review else None,
            "git_commit": self.git_commit,
            "final_status": self.final_status,
            "error_message": self.error_message,
            "token_usages": [u.to_dict() for u in self.token_usages],
            "review_attempts": self.review_attempts,
        }

    def to_safe_json(self) -> str:
        """生成脱敏后的 JSON 字符串，用于写入报告文件。"""
        from automation.security import redact_secrets

        raw = json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
        return redact_secrets(raw)
