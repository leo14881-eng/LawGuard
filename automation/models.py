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
# 或 P-1/P0/P1/P2 治理原则要求（例如缺少可核验法律来源、涉及个案判断），
# 或需要人工做出产品/法律/安全决策，而无法安全生成具体任务——这是真正的
# 阻塞场景，不包括"单纯找不到值得做的任务"。
# NO_HIGH_VALUE_TASK（2026-07-26 新增）表示 Planner 没有权限/依赖/环境/资源
# 障碍、也不需要人工决策，只是在 Value Gate 规则下找不到分数达标、非重复的
# 候选任务——这是正常的"当前没有高价值任务"信号，不是阻塞，不应与 BLOCKED
# 混用（历史上曾因两者语义混淆，把"没有高价值任务"误报为 BLOCKED，见
# automation/orchestrator.py 的 Planner Candidate Loop 处理逻辑）。
RISK_LEVELS = {"LOW", "MEDIUM", "HIGH", "BLOCKED", "DONE", "NO_HIGH_VALUE_TASK"}
# 评审结论允许的取值
REVIEW_VERDICTS = {"PASS", "FAIL", "BLOCKED"}


@dataclass
class DevelopmentTask:
    """OpenAI 规划器（CTO 角色）生成的下一项开发任务。

    2026-07-26 Value Gate 升级新增字段（见 automation/value_gate.py）：
    task_category 与 value_* / *_penalty / *_cost 用于计算 ValueScore，
    why_* / expected_user_benefit 要求 Planner 对每个任务给出可核查的理由，
    不能只凭一句"完善某页面"就生成任务。全部新字段都带默认值，兼容本次升级
    之前生成的历史 task.json 记录（反序列化时缺失字段按默认值处理，不报错）。
    仅 risk_level 为 LOW/MEDIUM/HIGH 的任务才要求这些字段有意义的取值，
    DONE/BLOCKED 不受 Value Gate 约束，保留默认值即可。
    """

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
    # Value Gate 相关字段（见 automation/value_gate.py）
    task_category: str = ""
    value_user: int = 0
    value_product: int = 0
    value_legal: int = 0
    value_tech_debt: int = 0
    repetition_penalty: int = 0
    maintenance_cost: int = 0
    why_valuable: str = ""
    why_not_other_candidates: str = ""
    why_not_duplicate: str = ""
    expected_user_benefit: str = ""
    # Product Backlog 溯源字段（2026-07-26 新增，见 automation/backlog.py 与
    # LAWGUARD_SOT.md 第 21 节）：LOW/MEDIUM/HIGH 任务必须填写来源 Backlog 条目
    # ID（如 "BL-003"）或其下某个切片 ID（如 "BL-003-1"），用于杜绝"无来源的
    # 低价值微优化任务"；DONE/BLOCKED/NO_HIGH_VALUE_TASK 不要求填写。
    backlog_id: str = ""

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
    # 仓库级运行锁信息（见 automation/run_lock.py），覆盖整个 Auto Dev Run（可能
    # 包含多个 Task），因此同一次 Run 内各 Task 的报告会展示相同的锁信息。字段：
    # repo_root、lock_path、run_id、pid、acquired_at、released（是否已释放）、
    # stale_lock_found（是否发现过陈旧锁）、stale_lock_archived_path（陈旧锁归档
    # 路径，未发生时为 None）。未持有锁（例如 --list-models 等只读子命令）时为
    # None。
    lock_info: dict[str, Any] | None = None
    # Value Gate 评估结果（见 automation/value_gate.py 的 GateDecision），字段：
    # score、passed、reasons、repetitive_category、repetitive_count。未生成实际
    # 任务（如 Planner 调用失败）或任务本身是 DONE/BLOCKED（不受 Value Gate 约束）
    # 时为 None。
    value_gate_info: dict[str, Any] | None = None
    # Planner Candidate Loop 明细（2026-07-26 新增，见 orchestrator.py 的
    # PLANNER_CANDIDATE_LIMIT）：每个候选一条记录，字段包含 candidate_number、
    # title、task_category、score（Python 实算 ValueScore）、passed、reasons、
    # repetitive_category、repetitive_count、duplicate_of_candidate（命中候选
    # 去重时指向被判定为同一候选的更早候选编号，否则为 None）。未触发候选循环
    # （例如 Stop Rule 提前拦截）时为空列表。
    candidate_evaluations: list[dict[str, Any]] = dataclasses.field(default_factory=list)

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
            "lock_info": self.lock_info,
            "value_gate_info": self.value_gate_info,
            "candidate_evaluations": self.candidate_evaluations,
        }

    def to_safe_json(self) -> str:
        """生成脱敏后的 JSON 字符串，用于写入报告文件。"""
        from automation.security import redact_secrets

        raw = json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
        return redact_secrets(raw)
