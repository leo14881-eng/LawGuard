"""Value Gate（价值门）：Auto Dev Planner 升级的核心逻辑。

背景（2026-07-26 Project Audit 结论）：Auto Dev 最近 13 个自动完成任务里，10 个
（约 77%）属于打印按钮/aria-label/响应式网格一类的重复小优化，其中 3 个任务连代码
改动都没有产生，只是重新验证已完成的工作——说明 Planner 已经进入"为了保持运行而
制造任务"的状态。本模块把"Auto Dev 的目标是持续提升产品价值，而不是生成更多
Task"落实为可执行、可测试的规则，不再只依赖 Prompt 里的一句提醒：

1. 每个候选任务必须由 Planner 自评分（用户价值/产品价值/法律价值/技术债收益，
   减去重复惩罚与维护成本），只有 ValueScore >= VALUE_GATE_THRESHOLD 才允许放行；
   分数由本模块基于 Planner 返回的分项重新计算，不信任 Planner 自己汇总的总分。
2. 独立于 Planner 自评分，本模块还会用确定性规则扫描"最近 N 个任务"的标题/目标，
   识别同一类重复任务（打印按钮/分享按钮/aria-label/CSS/间距/文案/图标/SEO微调/
   响应式微调/无障碍微调），达到 3 次以上时强制拒绝，除非任务明确声称在修复
   "严重缺陷"（不是"进一步完善"）。
3. 统计最近 20 个任务的平均 ValueScore，低于阈值时触发 Stop Rule，Auto Dev 应
   主动停止并建议进入 Project Audit / V2 规划，而不是继续生成任务。

历史数据来源：不新增复杂的状态文件/Run Manifest（`docs/project/AUTODEV_PROGRESS.md`
的"功能状态表"已被证明会被 `progress.py` 的固定模板重写机制反复清空，不适合作为
可靠的历史数据源）。本模块改为直接扫描 `automation/runtime/<run_id>/task.json`——
这是每个任务本来就会生成的既有产物（见 orchestrator.py 的 `write_json_file(run_dir
/ "task.json", ...)`），按运行目录名（时间戳前缀，天然可排序）取最近若干条，
足够支撑重复检测与滚动平均分统计，不需要额外的持久化机制。
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from automation.models import DevelopmentTask

# ValueScore 及分项取值范围（与 Planner Prompt 中的评分规则一一对应）
VALUE_DIMENSION_RANGE = {
    "value_user": (0, 10),
    "value_product": (0, 10),
    "value_legal": (0, 10),
    "value_tech_debt": (0, 5),
    "repetition_penalty": (0, 10),  # 存正数，计分时做减法（对应需求里的 -10~0）
    "maintenance_cost": (0, 5),  # 存正数，计分时做减法（对应需求里的 -5~0）
}

# 只有生成实际开发任务（LOW/MEDIUM/HIGH）时才要求价值评分与分类；
# DONE/BLOCKED 是终止信号，不代表"一个低价值任务"，不受 Value Gate 约束。
_VALUE_GATED_RISK_LEVELS = {"LOW", "MEDIUM", "HIGH"}

VALUE_GATE_THRESHOLD = 15

TASK_CATEGORIES = {
    "新增功能",
    "产品能力提升",
    "法律内容完善",
    "用户体验重大提升",
    "性能提升",
    "架构优化",
    "技术债清理",
}

# 重复任务识别：同一类任务连续/累计出现达到 REPETITION_LIMIT 次后，默认不再生成，
# 除非任务在 rationale/why_valuable 中明确声称修复"严重缺陷"（见
# _SEVERE_DEFECT_OVERRIDE_PATTERN）。关键词均为大小写不敏感、中英文皆有覆盖。
REPETITION_LIMIT = 3

REPETITIVE_CATEGORY_PATTERNS: dict[str, list[str]] = {
    "PrintButton": [r"打印本页", r"打印按钮", r"printpagebutton", r"print\s*page\s*button", r"打印入口"],
    "ShareButton": [r"分享按钮", r"分享面板", r"sharepanel", r"share\s*button"],
    "aria-label": [r"aria-label", r"无障碍标签", r"可访问性标签"],
    "CSS/间距": [r"间距", r"spacing", r"css\s*(微调|调整|优化)", r"样式微调"],
    "文案": [r"文案(调整|优化|措辞)", r"措辞", r"\bwording\b"],
    "Icon": [r"图标", r"\bicon\b"],
    "SEO微调": [r"seo\s*(微调|优化|调整)"],
    "Responsive微调": [r"响应式(网格|布局|微调)", r"\bresponsive\b"],
    "Accessibility微调": [r"无障碍(体验|优化|增强)", r"\baccessibility\b", r"\ba11y\b"],
}

_SEVERE_DEFECT_PATTERN = re.compile(r"严重缺陷|重大缺陷|阻断性|无法正常使用|完全失效|存在明显故障", re.IGNORECASE)


def _now_run_id_sort_key(dir_name: str) -> str:
    # runtime 目录名形如 20260726_123515_5ff3c7，字符串排序即时间排序。
    return dir_name


def load_recent_tasks(runtime_dir: Path, limit: int = 30) -> list[dict[str, Any]]:
    """扫描 automation/runtime/<run_id>/task.json，按时间倒序返回最近 limit 条。

    单条记录读取/解析失败时跳过，不因个别损坏文件中断整体统计；返回的字典额外
    附带 "_run_id" 字段，便于调用方/测试追溯来源。
    """
    if not runtime_dir.exists():
        return []
    run_dirs = sorted(
        (p for p in runtime_dir.iterdir() if p.is_dir()),
        key=lambda p: _now_run_id_sort_key(p.name),
        reverse=True,
    )
    results: list[dict[str, Any]] = []
    for run_dir in run_dirs:
        if len(results) >= limit:
            break
        task_file = run_dir / "task.json"
        if not task_file.exists():
            continue
        try:
            data = json.loads(task_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        data = dict(data)
        data["_run_id"] = run_dir.name
        results.append(data)
    return results


def classify_repetitive_category(title: str, objective: str = "") -> str | None:
    """判断标题/目标文本命中哪一类"已知重复类别"，未命中返回 None。"""
    text = f"{title or ''} {objective or ''}".lower()
    for category, patterns in REPETITIVE_CATEGORY_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return category
    return None


def count_recent_category_occurrences(history: list[dict[str, Any]], category: str) -> int:
    """统计历史记录（load_recent_tasks 的返回值）中命中指定类别的次数。"""
    count = 0
    for entry in history:
        matched = classify_repetitive_category(entry.get("title", ""), entry.get("objective", ""))
        if matched == category:
            count += 1
    return count


def compute_value_score(task: DevelopmentTask) -> int:
    """按公式重新计算 ValueScore，不信任 Planner 自己汇总的总分：

    ValueScore = 用户价值 + 产品价值 + 法律价值 + 技术债收益
                 - 重复惩罚 - 维护成本
    """
    return (
        task.value_user
        + task.value_product
        + task.value_legal
        + task.value_tech_debt
        - task.repetition_penalty
        - task.maintenance_cost
    )


@dataclass
class GateDecision:
    """Value Gate 的评估结果。"""

    passed: bool
    score: int
    reasons: list[str]
    repetitive_category: str | None
    repetitive_count: int


def validate_value_fields(task: DevelopmentTask) -> list[str]:
    """校验价值评分分项与任务分类是否在允许范围内，返回问题列表（空表示通过）。

    仅对 LOW/MEDIUM/HIGH 任务生效；DONE/BLOCKED 不要求填写有意义的价值评分。
    """
    if task.risk_level not in _VALUE_GATED_RISK_LEVELS:
        return []

    issues: list[str] = []
    if task.task_category not in TASK_CATEGORIES:
        issues.append(f"task_category 取值非法或缺失：{task.task_category!r}，必须是 {sorted(TASK_CATEGORIES)} 之一")

    for field_name, (lo, hi) in VALUE_DIMENSION_RANGE.items():
        value = getattr(task, field_name)
        if not isinstance(value, int) or isinstance(value, bool):
            issues.append(f"{field_name} 必须是整数")
            continue
        if not (lo <= value <= hi):
            issues.append(f"{field_name} 取值 {value} 超出允许范围 [{lo}, {hi}]")

    for text_field in ("why_valuable", "why_not_other_candidates", "why_not_duplicate", "expected_user_benefit"):
        if not isinstance(getattr(task, text_field, ""), str) or not getattr(task, text_field, "").strip():
            issues.append(f"{text_field} 必须是非空字符串（Planner 必须说明理由，不能空着）")

    return issues


def evaluate_task(task: DevelopmentTask, history: list[dict[str, Any]]) -> GateDecision:
    """Value Gate 主入口：判断该任务是否允许放行进入 Claude 执行阶段。

    DONE/BLOCKED 不受 Value Gate 约束，直接放行（它们是已有的终止信号，语义与
    "低价值任务"完全不同）。
    """
    if task.risk_level not in _VALUE_GATED_RISK_LEVELS:
        return GateDecision(passed=True, score=0, reasons=["DONE/BLOCKED 不受 Value Gate 约束"], repetitive_category=None, repetitive_count=0)

    score = compute_value_score(task)
    reasons: list[str] = [
        f"ValueScore = {task.value_user}(用户) + {task.value_product}(产品) + {task.value_legal}(法律) + "
        f"{task.value_tech_debt}(技术债收益) - {task.repetition_penalty}(重复惩罚) - {task.maintenance_cost}(维护成本) = {score}"
    ]

    category = classify_repetitive_category(task.title, task.objective)
    repetitive_count = count_recent_category_occurrences(history, category) if category else 0

    # 规则一：重复任务硬性拦截，独立于分数——即使 Planner 给自己打了高分，也不能
    # 靠自评分绕过"这一类任务已经重复 3 次以上"的事实判断，除非明确声称严重缺陷。
    has_defect_claim = bool(
        _SEVERE_DEFECT_PATTERN.search(task.rationale or "")
        or _SEVERE_DEFECT_PATTERN.search(task.why_valuable or "")
    )
    if category and repetitive_count >= REPETITION_LIMIT and not has_defect_claim:
        reasons.append(
            f"任务类别「{category}」在最近 {len(history)} 个任务中已出现 {repetitive_count} 次"
            f"（达到 {REPETITION_LIMIT} 次上限），且未声明存在严重缺陷，默认不再生成。"
        )
        return GateDecision(passed=False, score=score, reasons=reasons, repetitive_category=category, repetitive_count=repetitive_count)

    # 规则二：分数门槛
    if score < VALUE_GATE_THRESHOLD:
        reasons.append(f"ValueScore {score} 低于门槛 {VALUE_GATE_THRESHOLD}，不允许生成任务。")
        return GateDecision(passed=False, score=score, reasons=reasons, repetitive_category=category, repetitive_count=repetitive_count)

    reasons.append(f"ValueScore {score} >= {VALUE_GATE_THRESHOLD}，且未触发重复任务硬性拦截，允许放行。")
    return GateDecision(passed=True, score=score, reasons=reasons, repetitive_category=category, repetitive_count=repetitive_count)


def should_stop_auto_dev(
    history: list[dict[str, Any]], window: int = 20, threshold: float = 8.0
) -> tuple[bool, float | None, int]:
    """Stop Rule：统计最近 window 个"实际参与过 Value Gate 评分"的任务
    （即 risk_level 为 LOW/MEDIUM/HIGH 的历史记录，DONE/BLOCKED/评分字段缺失的
    记录不计入，避免被无意义的 0 分稀释平均值），若平均 ValueScore 低于 threshold
    则应停止 Auto Dev。

    返回 (是否应停止, 平均分（不足以计算时为 None）, 参与计算的任务数)。
    """
    scored: list[int] = []
    for entry in history[:window]:
        if entry.get("risk_level") not in _VALUE_GATED_RISK_LEVELS:
            continue
        # 兼容旧版 task.json（本次升级之前生成，没有价值评分字段）：这类记录
        # 无法反映"新规则下的真实价值"，不计入平均分统计，避免用旧数据误判。
        # 注意：这里只读取 compute_value_score 实际用到的 6 个数值字段，不重建
        # 完整 DevelopmentTask——task.json 里缺失 rationale/scope 等其它字段
        # （不影响计分）不应导致这条记录被静默丢弃、扭曲平均分统计。
        if "value_user" not in entry:
            continue
        try:
            score = (
                int(entry.get("value_user", 0))
                + int(entry.get("value_product", 0))
                + int(entry.get("value_legal", 0))
                + int(entry.get("value_tech_debt", 0))
                - int(entry.get("repetition_penalty", 0))
                - int(entry.get("maintenance_cost", 0))
            )
        except (TypeError, ValueError):
            continue
        scored.append(score)

    if not scored:
        return False, None, 0

    average = sum(scored) / len(scored)
    return average < threshold, average, len(scored)


# ---------------------------------------------------------------------------
# Capability Matrix：人工审计得出的模块完成度基线（见 2026-07-26 Project Audit），
# 不做自动化扫描计算——"完成度"本质上是主观判断（功能是否可用、内容是否可信、
# 体验是否达标），机械统计文件数/路由数容易得出误导性结论。此处只提供一份
# 结构化基线，供 Planner 参考"哪些模块已经 >=90%，应优先寻找其它模块"，人工
# 复审时可以直接编辑更新，不需要额外的自动化系统。
# ---------------------------------------------------------------------------
CAPABILITY_MATRIX: dict[str, int] = {
    "Home": 95,
    "Stages（诉讼阶段）": 90,
    "Rights Guide（权利指引）": 90,
    "Legal Sources（法律来源，内容层面待人工核验）": 60,
    "Official Channels（官方渠道，链接待核验）": 55,
    "Documents（文书核对，仅通用框架）": 50,
    "Emergency Guide（紧急行动指引）": 90,
    "Privacy / Disclaimer / About": 95,
    "Search（本地全文搜索）": 0,
    "SEO": 90,
    "分享（Share）": 95,
    "打印（Print）": 95,
    "Accessibility（无障碍）": 85,
    "Responsive（响应式）": 90,
    "Automation（Auto Dev 自身）": 90,
    "Offline / PWA": 0,
    "Performance": 70,
}

CAPABILITY_MATRIX_SATURATION_THRESHOLD = 90


def build_capability_matrix_context() -> str:
    """生成供 Planner 上下文使用的 Capability Matrix 文本，标注哪些模块已饱和。"""
    lines = ["## Capability Matrix（人工审计基线，2026-07-26；完成度 >= 90% 的模块应优先避开，去找其它模块）"]
    for module, pct in sorted(CAPABILITY_MATRIX.items(), key=lambda kv: kv[1]):
        flag = "（已饱和，避免继续在此模块生成任务）" if pct >= CAPABILITY_MATRIX_SATURATION_THRESHOLD else ""
        lines.append(f"- {module}：约 {pct}%{flag}")
    return "\n".join(lines)


def build_repetition_context(history: list[dict[str, Any]]) -> str:
    """生成供 Planner 上下文使用的"最近任务重复情况"文本。"""
    if not history:
        return "## 最近任务重复情况\n（无历史任务记录）"
    lines = [f"## 最近任务重复情况（基于最近 {len(history)} 条 automation/runtime/*/task.json）"]
    any_flag = False
    for category in REPETITIVE_CATEGORY_PATTERNS:
        count = count_recent_category_occurrences(history, category)
        if count > 0:
            marker = "（已达到/超过重复上限，默认不再生成，除非严重缺陷）" if count >= REPETITION_LIMIT else ""
            lines.append(f"- {category}：最近已出现 {count} 次{marker}")
            any_flag = True
    if not any_flag:
        lines.append("（未检测到已知重复类别达到 1 次以上）")
    return "\n".join(lines)
