"""LawGuard Auto Dev V1 —— 本地自动开发调度系统主入口。

用法：
    python automation/orchestrator.py [--dry-run] [--no-commit] [--allow-dirty]
                                       [--model MODEL] [--verbose]

V1 每次运行最多只完成一个任务，禁止无限循环，禁止自动连续开发多个任务。
"""
from __future__ import annotations

import argparse
import datetime
import secrets
import sys
from pathlib import Path

from automation import claude_runner, context_loader, openai_client, validator
from automation.config import PROJECT_ROOT, REPORTS_DIR, RUNTIME_DIR, WEB_DIR, Config, ConfigError, load_config
from automation.git_service import GitError, GitService
from automation.models import ReviewResult, RunReport
from automation.report_writer import (
    setup_run_logger,
    write_json_file,
    write_run_report_json,
    write_summary_markdown,
    write_text_file,
)

# 退出码约定
EXIT_SUCCESS = 0
EXIT_GENERAL_FAILURE = 1
EXIT_CONFIG_ERROR = 2
EXIT_SECURITY_FAILURE = 3
EXIT_CLAUDE_FAILURE = 4
EXIT_VALIDATION_FAILURE = 5
EXIT_REVIEW_FAILED = 6


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python automation/orchestrator.py",
        description=(
            "LawGuard Auto Dev V1 本地自动开发调度系统。\n"
            "每次运行由 OpenAI 规划一项开发任务、调用本地 Claude Code CLI 执行、"
            "自动验证并由 OpenAI 评审，评审通过后才可选地自动提交 Git。"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="只生成并展示任务，不调用 Claude Code，不修改代码，不提交 Git。",
    )
    parser.add_argument(
        "--no-commit", action="store_true",
        help="即使 .env.local 中 LAWGUARD_AUTO_COMMIT=true，本次运行也禁止自动提交。",
    )
    parser.add_argument(
        "--allow-dirty", action="store_true",
        help="允许在 Git 工作区不干净时运行；此模式下禁止自动提交，并会输出风险警告。",
    )
    parser.add_argument(
        "--model", default=None,
        help="临时覆盖 OPENAI_MODEL 环境变量指定的模型。",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="输出更详细的日志（仍不会显示任何密钥）。",
    )
    return parser.parse_args(argv)


def _generate_run_id() -> str:
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = secrets.token_hex(3)
    return f"{now}_{suffix}"


def _now_iso() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def should_auto_commit(
    *, safe_to_commit: bool, auto_commit_enabled: bool, no_commit_flag: bool, allow_dirty_flag: bool
) -> bool:
    """判断本次运行是否允许自动提交。

    --allow-dirty 模式下永远返回 False，即便评审通过、配置允许自动提交。
    """
    return safe_to_commit and auto_commit_enabled and not no_commit_flag and not allow_dirty_flag


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    run_id = _generate_run_id()
    run_dir = RUNTIME_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    logger = setup_run_logger(run_dir, args.verbose)

    report = RunReport(
        run_id=run_id,
        started_at=_now_iso(),
        finished_at=None,
        task=None,
        claude_result=None,
        validation_results=[],
        review=None,
        git_commit=None,
        final_status="RUNNING",
        error_message=None,
    )

    def finalize(status: str, error_message: str | None, exit_code: int) -> int:
        report.finished_at = _now_iso()
        report.final_status = status
        report.error_message = error_message
        write_run_report_json(run_dir, report)
        try:
            git = GitService(PROJECT_ROOT)
            changed_files = git.get_changed_files() if git.is_git_repo() else []
        except Exception:  # noqa: BLE001 - 报告阶段不因辅助信息失败而中断
            changed_files = []
        summary_path = write_summary_markdown(REPORTS_DIR, report, changed_files)
        logger.info("运行结束，最终状态：%s", status)
        logger.info("摘要报告：%s", summary_path)
        # 运行结束后主动释放日志文件句柄，避免同一进程内重复调用 main()
        # （例如测试或脚本内嵌调用）时文件句柄被长期占用。
        for handler in list(logger.handlers):
            handler.close()
            logger.removeHandler(handler)
        return exit_code

    logger.info("===== LawGuard Auto Dev V1 开始运行 =====")
    logger.info("运行 ID：%s", run_id)
    logger.info("项目根目录：%s", PROJECT_ROOT)

    # 第一步：加载配置
    try:
        config = load_config(model_override=args.model)
    except ConfigError as exc:
        logger.error("配置错误：%s", exc)
        return finalize("CONFIG_ERROR", str(exc), EXIT_CONFIG_ERROR)

    logger.info("使用模型：%s", config.openai_model)
    logger.info(
        "自动提交：%s（--no-commit=%s，--allow-dirty=%s）",
        config.auto_commit, args.no_commit, args.allow_dirty,
    )

    # 第二步：安全检查——必须是 Git 仓库，工作区状态检查
    git = GitService(PROJECT_ROOT)
    if not git.is_git_repo():
        msg = "当前目录不是 Git 仓库，自动化系统拒绝运行。"
        logger.error(msg)
        return finalize("SECURITY_FAILED", msg, EXIT_SECURITY_FAILURE)

    is_dirty = not git.is_clean()
    if is_dirty and not args.allow_dirty:
        msg = "Git 工作区不干净，为避免覆盖未提交的修改，已停止运行。可使用 --allow-dirty 显式跳过（该模式下禁止自动提交）。"
        logger.error(msg)
        logger.error("当前 git status --short：\n%s", git.get_status_short())
        return finalize("SECURITY_FAILED", msg, EXIT_SECURITY_FAILURE)
    if is_dirty and args.allow_dirty:
        logger.warning("检测到工作区不干净，已通过 --allow-dirty 显式跳过检查；本次运行将禁止自动提交。")

    # 第三步：读取项目上下文
    logger.info("读取项目上下文（LAWGUARD_SOT.md / CLAUDE.md / package.json / 文件树 / Git 状态）...")
    project_context = context_loader.build_planner_context()

    # 第四步：调用 OpenAI 规划下一项任务
    client = openai_client.create_client(config)
    logger.info("调用 OpenAI 规划下一项开发任务...")
    try:
        task = openai_client.plan_next_task(client, config, project_context)
    except openai_client.PlannerError as exc:
        logger.error("规划任务失败：%s", exc)
        return finalize("PLANNER_FAILED", str(exc), EXIT_GENERAL_FAILURE)
    except Exception as exc:  # noqa: BLE001 - OpenAI SDK 可能抛出多种异常（鉴权、模型不可用等）
        logger.error("调用 OpenAI 规划器时发生错误：%s", exc)
        return finalize("PLANNER_FAILED", str(exc), EXIT_GENERAL_FAILURE)

    report.task = task
    write_json_file(run_dir / "task.json", task.to_dict())
    logger.info("任务已生成：%s", task.title)
    logger.info("任务目标：%s", task.objective)
    logger.info("风险等级：%s", task.risk_level)

    if task.risk_level == "BLOCKED":
        msg = f"规划器判断当前无法安全生成任务，已停止（不调用 Claude，不提交）。原因：{task.rationale}"
        logger.warning(msg)
        return finalize("BLOCKED_BY_PLANNER", msg, EXIT_SECURITY_FAILURE)

    if args.dry_run:
        logger.info("--dry-run 模式：仅展示任务，不调用 Claude Code，不修改代码，不提交。")
        logger.info("允许修改的文件：%s", task.files_allowed)
        logger.info("禁止修改的文件：%s", task.files_forbidden)
        logger.info("验收条件：%s", task.acceptance_criteria)
        logger.info("验证命令：%s", task.validation_commands)
        return finalize("DRY_RUN_COMPLETE", None, EXIT_SUCCESS)

    # 第五步：非交互调用 Claude Code CLI 执行任务
    logger.info("调用 Claude Code CLI 执行任务，超时时间：%d 秒...", config.claude_timeout_seconds)
    claude_prompt = claude_runner.build_task_prompt(
        task_title=task.title,
        objective=task.objective,
        scope=task.scope,
        files_allowed=task.files_allowed,
        files_forbidden=task.files_forbidden,
        acceptance_criteria=task.acceptance_criteria,
        validation_commands=task.validation_commands,
        developer_prompt=task.developer_prompt,
    )
    claude_result = claude_runner.run_claude(
        claude_prompt, project_root=PROJECT_ROOT, timeout_seconds=config.claude_timeout_seconds
    )
    report.claude_result = claude_result
    write_text_file(run_dir / "claude_stdout.txt", claude_result.stdout)
    write_text_file(run_dir / "claude_stderr.txt", claude_result.stderr)

    if claude_result.timed_out:
        msg = "Claude Code 执行超时，已终止。"
        logger.error(msg)
        return finalize("CLAUDE_FAILED", msg, EXIT_CLAUDE_FAILURE)
    if claude_result.exit_code != 0:
        msg = f"Claude Code 执行失败，退出码：{claude_result.exit_code}"
        logger.error(msg)
        return finalize("CLAUDE_FAILED", msg, EXIT_CLAUDE_FAILURE)

    logger.info("Claude Code 执行完成，耗时 %.1f 秒。", claude_result.duration_seconds)

    # 第六步：自动验证
    logger.info("执行自动验证（基础验证 + 任务附加验证命令）...")
    validation_results, validation_passed = validator.run_validation(
        project_root=PROJECT_ROOT, web_dir=WEB_DIR, extra_commands=task.validation_commands
    )
    report.validation_results = validation_results
    write_json_file(run_dir / "validation.json", {"results": [r.to_dict() for r in validation_results]})
    for r in validation_results:
        status = "超时" if r.timed_out else ("通过" if r.exit_code == 0 else "失败")
        logger.info("验证命令 [%s] cwd=%s：%s", r.command, r.cwd, status)

    # 第七步：调用 OpenAI 评审器（无论验证是否通过，均收集证据供评审与人工复核）
    logger.info("调用 OpenAI 对本次改动进行代码评审...")
    review_context = context_loader.build_reviewer_context(
        task=task, claude_result=claude_result, validation_results=validation_results
    )
    review: ReviewResult | None = None
    try:
        review = openai_client.review_change(client, config, review_context)
    except openai_client.ReviewerError as exc:
        logger.error("评审器输出不合法：%s", exc)
    except Exception as exc:  # noqa: BLE001 - OpenAI SDK 可能抛出多种异常
        logger.error("调用 OpenAI 评审器时发生错误：%s", exc)

    if review is not None:
        report.review = review
        write_json_file(run_dir / "review.json", review.to_dict())
        logger.info("评审结论：%s；是否允许提交：%s", review.verdict, review.safe_to_commit)
        logger.info("评审摘要：%s", review.summary)
        if review.blocking_issues:
            logger.warning("阻塞问题：%s", review.blocking_issues)

    if not validation_passed:
        msg = "自动验证未全部通过，已停止，不允许提交。"
        logger.error(msg)
        return finalize("VALIDATION_FAILED", msg, EXIT_VALIDATION_FAILURE)

    if review is None:
        msg = "评审器未能生成有效评审结果，视为未通过，不允许提交。"
        logger.error(msg)
        return finalize("REVIEW_FAILED", msg, EXIT_REVIEW_FAILED)

    if review.verdict != "PASS":
        msg = f"评审未通过（verdict={review.verdict}），不允许提交。"
        logger.error(msg)
        return finalize("REVIEW_FAILED", msg, EXIT_REVIEW_FAILED)

    # 第八步：根据规则决定是否自动提交
    can_commit = should_auto_commit(
        safe_to_commit=review.safe_to_commit,
        auto_commit_enabled=config.auto_commit,
        no_commit_flag=args.no_commit,
        allow_dirty_flag=args.allow_dirty,
    )
    if not can_commit:
        reasons = []
        if not review.safe_to_commit:
            reasons.append("评审未标记 safe_to_commit=true")
        if not config.auto_commit:
            reasons.append("LAWGUARD_AUTO_COMMIT 未设为 true")
        if args.no_commit:
            reasons.append("已指定 --no-commit")
        if args.allow_dirty:
            reasons.append("本次运行处于 --allow-dirty 模式，禁止自动提交")
        logger.info("评审通过，但本次不自动提交，原因：%s", "；".join(reasons) or "未知")
        return finalize("REVIEW_PASSED_NOT_COMMITTED", None, EXIT_SUCCESS)

    violations = git.find_forbidden_violations(task.files_forbidden)
    if violations:
        msg = f"检测到禁止修改的文件被改动，取消自动提交：{violations}"
        logger.error(msg)
        return finalize("REVIEW_PASSED_NOT_COMMITTED", msg, EXIT_SUCCESS)

    diff_check_result = git.diff_check()
    if diff_check_result.returncode != 0:
        msg = "git diff --check 未通过，取消自动提交。"
        logger.error(msg)
        return finalize("REVIEW_PASSED_NOT_COMMITTED", msg, EXIT_SUCCESS)

    changed_files = git.get_changed_files()
    if not changed_files:
        logger.info("没有检测到文件改动，无需提交。")
        return finalize("REVIEW_PASSED_NOT_COMMITTED", None, EXIT_SUCCESS)

    try:
        commit_hash = git.commit(changed_files, review.commit_message)
        report.git_commit = commit_hash
        logger.info("已自动提交，commit hash：%s", commit_hash)
        return finalize("COMMITTED", None, EXIT_SUCCESS)
    except GitError as exc:
        msg = f"自动提交失败：{exc}"
        logger.error(msg)
        return finalize("COMMIT_FAILED", msg, EXIT_GENERAL_FAILURE)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n已手动中断运行。", file=sys.stderr)
        sys.exit(1)
