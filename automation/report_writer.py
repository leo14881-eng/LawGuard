"""报告系统：生成运行目录下的结构化文件与最终中文摘要报告。

所有写入文件的文本均经过密钥脱敏处理。
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from automation.models import CommandResult, ReviewResult, RunReport, TokenUsage
from automation.security import redact_secrets


def setup_run_logger(run_dir: Path, verbose: bool) -> logging.Logger:
    """为本次运行创建日志记录器，同时输出到运行目录下的日志文件与控制台。"""
    logger = logging.getLogger("automation")
    logger.setLevel(logging.DEBUG)
    # 显式关闭旧 handler 持有的文件句柄，避免 Windows 下日志文件被长期占用
    # （例如同一进程内多次运行、或测试中反复调用本函数时导致文件无法删除）。
    for handler in list(logger.handlers):
        handler.close()
        logger.removeHandler(handler)
    logger.propagate = False

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")

    file_handler = logging.FileHandler(run_dir / "orchestrator.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    logger.addHandler(console_handler)

    return logger


def write_json_file(path: Path, data: dict) -> None:
    """写入脱敏后的 JSON 文件。"""
    raw = json.dumps(data, ensure_ascii=False, indent=2)
    path.write_text(redact_secrets(raw), encoding="utf-8")


def write_text_file(path: Path, text: str) -> None:
    """写入脱敏后的文本文件。"""
    path.write_text(redact_secrets(text or ""), encoding="utf-8")


def write_run_report_json(run_dir: Path, report: RunReport) -> None:
    write_json_file(run_dir / "run_report.json", report.to_dict())


def _format_command_results(results: list[CommandResult]) -> str:
    if not results:
        return "（无）"
    lines = []
    for r in results:
        if r.timed_out:
            status = "超时"
        elif r.exit_code == 0:
            status = "通过"
        else:
            status = f"失败（退出码 {r.exit_code}）"
        lines.append(f"- `{r.command}`：{status}，耗时 {r.duration_seconds:.1f} 秒")
    return "\n".join(lines)


def _format_token_usages(usages: list[TokenUsage]) -> str:
    """生成 OpenAI Token 用量小节文本。API 未返回的字段一律显示 Unknown，不做任何估算。"""
    if not usages:
        return "（本次运行未发生 OpenAI 调用）"

    def _fmt(value: int | None) -> str:
        return str(value) if value is not None else "Unknown"

    lines = []
    total_prompt = 0
    total_completion = 0
    total_all = 0
    has_unknown = False
    for u in usages:
        lines.append(
            f"- 调用：{u.call_label}｜Model：{u.model}｜Prompt Tokens：{_fmt(u.prompt_tokens)}｜"
            f"Completion Tokens：{_fmt(u.completion_tokens)}｜Total Tokens：{_fmt(u.total_tokens)}"
        )
        if u.prompt_tokens is None or u.completion_tokens is None or u.total_tokens is None:
            has_unknown = True
        else:
            total_prompt += u.prompt_tokens
            total_completion += u.completion_tokens
            total_all += u.total_tokens

    if has_unknown:
        summary_line = "汇总：存在未知字段，暂不汇总合计（避免用部分数据拼出误导性总数）。"
    else:
        summary_line = (
            f"汇总：Prompt Tokens {total_prompt}，Completion Tokens {total_completion}，"
            f"Total Tokens {total_all}。"
        )

    # 不内置任何价格表：OpenAI 定价会变化，项目内没有可核验的最新价格来源，
    # 强行估算金额属于编造数据，因此 Estimated Cost 固定显示 Unknown。
    cost_line = "Estimated Cost：Unknown（未内置价格表，不做估算，请自行按 OpenAI 官方定价核算）。"

    return "\n".join(lines) + "\n\n" + summary_line + "\n" + cost_line


def write_summary_markdown(reports_dir: Path, report: RunReport, changed_files: list[str]) -> Path:
    """生成中文摘要报告并保存到 automation/reports/<run_id>.md。"""
    task = report.task
    review: ReviewResult | None = report.review

    task_title = task.title if task else "（未生成任务）"
    task_objective = task.objective if task else "（无）"

    claude_summary = "（未执行）"
    if report.claude_result:
        cr = report.claude_result
        status = "超时" if cr.timed_out else ("成功" if cr.exit_code == 0 else "失败")
        claude_summary = f"状态：{status}；退出码：{cr.exit_code}；耗时：{cr.duration_seconds:.1f} 秒"

    validation_text = _format_command_results(report.validation_results)

    review_text = "（未执行评审）"
    blocking_text = "（无）"
    if review:
        review_text = (
            f"结论：{review.verdict}；是否允许提交：{'是' if review.safe_to_commit else '否'}\n\n{review.summary}"
        )
        if review.blocking_issues:
            blocking_text = "\n".join(f"- {i}" for i in review.blocking_issues)

    changed_text = "\n".join(f"- {f}" for f in changed_files) or "（无文件改动）"
    commit_text = report.git_commit or "（未提交）"

    next_steps: list[str] = []
    if not report.git_commit:
        next_steps.append("检查 automation/runtime/<run_id>/ 下的详细日志与命令输出，确认未提交的具体原因。")
    if review and review.non_blocking_suggestions:
        next_steps.extend(f"参考建议：{s}" for s in review.non_blocking_suggestions)
    if report.git_commit:
        next_steps.append("本次运行已自动提交，可执行 git log -1 确认提交内容，尚未 push。")
    if not next_steps:
        next_steps.append("请人工检查本次运行的完整日志后决定下一步操作。")
    next_steps_text = "\n".join(f"- {s}" for s in next_steps)

    error_line = f"（错误信息：{report.error_message}）" if report.error_message else ""

    # Attempt 记录：report.review_attempts 中每一项覆盖 INITIAL/VALIDATION_FIX/REVIEW_FIX
    # 三种 Attempt 类型（字段含义见 automation/models.py 的 RunReport.review_attempts 注释）。
    attempt_blocks: list[str] = []
    validation_fix_count = 0
    review_fix_count = 0
    for entry in report.review_attempts:
        attempt_prompt_type = entry.get("prompt_type", "INITIAL")
        if attempt_prompt_type == "VALIDATION_FIX":
            validation_fix_count += 1
        elif attempt_prompt_type == "REVIEW_FIX":
            review_fix_count += 1

        attempt_validation_status = "PASS" if entry.get("validation_passed") else "FAIL"
        attempt_review_verdict = entry.get("review_verdict") or "（未调用 Review）"
        attempt_review_duration = entry.get("review_duration_seconds")
        attempt_review_duration_text = (
            f"{attempt_review_duration:.1f} 秒" if attempt_review_duration is not None else "（未调用）"
        )
        attempt_changed_files_text = "、".join(entry.get("changed_files") or []) or "（无）"
        failed_command_text = f"，失败命令：{entry['failed_command']}" if entry.get("failed_command") else ""

        block_lines = [
            f"### Attempt {entry.get('attempt_number')}",
            f"- 类型：{attempt_prompt_type}",
            f"- Claude 耗时：{entry.get('claude_duration_seconds', 0.0):.1f} 秒"
            f"（{entry.get('claude_started_at', '')} ~ {entry.get('claude_finished_at', '')}）",
            f"- 改动文件：{attempt_changed_files_text}",
            f"- Validation：{attempt_validation_status}"
            f"（耗时 {entry.get('validation_duration_seconds', 0.0):.1f} 秒{failed_command_text}）",
            f"- Review：{attempt_review_verdict}（耗时 {attempt_review_duration_text}）",
        ]
        for issue in entry.get("blocking_issues") or []:
            block_lines.append(f"  - 阻塞问题：{issue}")
        block_lines.append(f"- Retry 原因：{entry.get('retry_reason', '（无）')}")
        attempt_blocks.append("\n".join(block_lines))

    attempts_text = "\n\n".join(attempt_blocks) if attempt_blocks else "（本次未记录任何 Attempt）"

    total_attempts = len(report.review_attempts)
    attempt_summary_text = (
        f"- 总 Attempt 数：{total_attempts}\n"
        f"- Validation Fix 次数：{validation_fix_count}\n"
        f"- Review Fix 次数：{review_fix_count}\n"
        f"- 最终状态：{report.final_status}\n"
        f"- 是否提交：{'是' if report.git_commit else '否'}\n"
        f"- Commit Hash：{report.git_commit or '（未提交）'}\n"
        f"- 是否执行 git push：否"
    )

    value_gate_text = "（本次未生成 LOW/MEDIUM/HIGH 任务，Value Gate 不适用）"
    if report.value_gate_info:
        vg = report.value_gate_info
        reasons_text = "\n".join(f"  - {r}" for r in vg.get("reasons", [])) or "  （无）"
        value_gate_text = (
            f"- Task：{task_title}\n"
            f"- ValueScore：{vg.get('score')}\n"
            f"- 判定结果：{'PASS（放行）' if vg.get('passed') else 'REJECT（丢弃）'}\n"
            f"- 为什么值得开发：{vg.get('why_valuable') or '（无）'}\n"
            f"- 为什么没有选择其它候选任务：{vg.get('why_not_other_candidates') or '（无）'}\n"
            f"- 为什么不是重复任务：{vg.get('why_not_duplicate') or '（无）'}\n"
            f"- 预计用户收益：{vg.get('expected_user_benefit') or '（无）'}\n"
            f"- 重复类别：{vg.get('repetitive_category') or '（无）'}"
            f"（最近已出现 {vg.get('repetitive_count', 0)} 次）\n"
            f"- 判定依据：\n{reasons_text}"
        )

    candidate_lines: list[str] = []
    for ev in report.candidate_evaluations:
        result = "PASS" if ev.get("passed") else "REJECT"
        dup_text = (
            f"（与 Candidate {ev['duplicate_of_candidate']} 判定为同一候选，视为同义改写）"
            if ev.get("duplicate_of_candidate")
            else ""
        )
        reasons_text = "；".join(ev.get("reasons", [])) or "（无）"
        candidate_lines.append(
            f"### Candidate {ev.get('candidate_number')}\n"
            f"- 标题：{ev.get('title')}\n"
            f"- 分类：{ev.get('task_category') or '未知'}\n"
            f"- Python 实算 ValueScore：{ev.get('score')}\n"
            f"- 结果：{result}{dup_text}\n"
            f"- 重复类别：{ev.get('repetitive_category') or '无'}"
            f"（最近已出现 {ev.get('repetitive_count', 0)} 次）\n"
            f"- 判定/拒绝原因：{reasons_text}"
        )
    candidate_text = "\n\n".join(candidate_lines) if candidate_lines else "（本次运行未触发 Planner Candidate Loop，例如 Value Gate Stop Rule 已提前拦截）"

    lock_text = "（本次运行未持有仓库运行锁）"
    if report.lock_info:
        li = report.lock_info
        stale_text = (
            f"是（归档至 {li.get('stale_lock_archived_path')}）"
            if li.get("stale_lock_found")
            else "否"
        )
        lock_text = (
            f"- 仓库：{li.get('repo_root', 'Unknown')}\n"
            f"- 锁文件：{li.get('lock_path', 'Unknown')}\n"
            f"- Run ID：{li.get('run_id', 'Unknown')}\n"
            f"- PID：{li.get('pid', 'Unknown')}\n"
            f"- 获取时间：{li.get('acquired_at', 'Unknown')}\n"
            f"- 释放结果：{'已释放' if li.get('released') else '未释放'}\n"
            f"- 是否发现陈旧锁：{stale_text}"
        )

    content = f"""# LawGuard 自动化开发运行报告

## 1. 运行 ID
{report.run_id}

## 2. 时间
- 开始：{report.started_at}
- 结束：{report.finished_at or "（未结束）"}

## 3. 任务标题
{task_title}

## 4. 任务目标
{task_objective}

## 5. Claude 执行结果
{claude_summary}

## 6. 修改文件
{changed_text}

## 7. 验证结果
{validation_text}

## 8. OpenAI 评审结论
{review_text}

## 9. 是否提交
{"是" if report.git_commit else "否"}

## 10. Git Commit Hash
{commit_text}

## 11. 阻塞问题
{blocking_text}

## 12. 下一步人工操作建议
{next_steps_text}

## 13. 最终状态
{report.final_status}
{error_line}

## 14. OpenAI Token 用量
{_format_token_usages(report.token_usages)}

## 15. Attempt 记录
{attempts_text}

## 16. Attempt 总结
{attempt_summary_text}

## 17. 运行锁
{lock_text}

## 18. Value Gate
{value_gate_text}

## 19. Planner Candidate 评估明细
{candidate_text}
"""
    reports_dir.mkdir(parents=True, exist_ok=True)
    path = reports_dir / f"{report.run_id}.md"
    path.write_text(redact_secrets(content), encoding="utf-8")
    return path
