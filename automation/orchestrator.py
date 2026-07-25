"""LawGuard Auto Dev V1 —— 本地自动开发调度系统主入口。

用法：
    python automation/orchestrator.py [--dry-run] [--no-commit] [--allow-dirty]
                                       [--model MODEL] [--verbose] [--list-models]

Auto Dev 启动后持续自动循环执行「Planner → Claude Code → Build → Test → Review →
Git Commit → 下一任务」，不等待人工确认，直到满足下方任一停止条件才退出：
Planner 判断已无更多可安全规划的任务、Claude 执行失败、构建/测试失败、Review 未通过
（FAIL 或 BLOCKED）、OpenAI 调用失败、已有的超时限制触发，或用户按 Ctrl+C 主动中断。
每个任务评审通过后立即自动 `git add` + `git commit`（提交信息统一为
`AutoDev(task-NNN): ...`，任务序号自动递增），仅提交到本地仓库，任何情况下都不会执行
`git push`。`--dry-run`、`--no-commit`、`--allow-dirty` 仍只用于单任务预览/调试，
使用这些参数时不会进入连续循环。
"""
from __future__ import annotations

import argparse
import datetime
import secrets
import sys
from pathlib import Path

if __package__ in (None, ""):
    # 支持 `python automation/orchestrator.py` 直接运行：以脚本方式启动时，Python
    # 只会把 automation/ 目录本身加入 sys.path，而不是项目根目录，导致下面的
    # `from automation import ...` 找不到 automation 包。这里补上项目根目录，
    # 使脚本无论以 `python automation/orchestrator.py` 还是
    # `python -m automation.orchestrator` 启动都能正确导入。
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from automation import claude_runner, context_loader, openai_client, progress, validator
from automation.config import (
    PROGRESS_FILE,
    PROGRESS_FILE_RELATIVE,
    PROJECT_ROOT,
    REPORTS_DIR,
    RUNTIME_DIR,
    WEB_DIR,
    Config,
    ConfigError,
    ModelNotConfiguredError,
    load_api_key_only,
    load_config,
)
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
            "默认启动后持续自动循环：由 OpenAI 规划一项开发任务、调用本地 Claude Code CLI 执行、"
            "自动验证并由 OpenAI 评审，评审通过后自动提交 Git 并立即开始下一项任务，直到规划器"
            "判断无更多任务或触发停止条件为止；--dry-run/--no-commit/--allow-dirty 仍只用于"
            "单任务预览与调试。"
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
        "--list-models", action="store_true",
        help="列出当前 OPENAI_API_KEY 可访问的模型后退出；不生成任务、不调用 Claude、不提交。",
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


def _print_model_options(model_ids: list[str], print_fn) -> None:
    """将模型列表以中文提示打印出来（print_fn 可以是 print 或 logger.error 等）。"""
    text_models = openai_client.filter_likely_text_models(model_ids)
    print_fn(
        f"当前 OPENAI_API_KEY 可访问的模型共 {len(model_ids)} 个，其中适合 Responses API "
        "普通文本规划/评审场景的候选模型："
    )
    for model_id in text_models:
        print_fn(f"  - {model_id}")
    print_fn("")
    print_fn("选型建议（仅供参考，不会自动选择，你仍需显式配置）：")
    for model_id, note in openai_client.MODEL_RECOMMENDATION_NOTES:
        print_fn(f"  - {model_id}：{note}")
    print_fn("")
    print_fn(f"提示：{openai_client.MODELS_API_DISCLAIMER}")
    print_fn(
        "请从上方列表中选择一个模型，在项目根目录 .env.local 中设置 "
        "OPENAI_MODEL=<模型名>，或运行时加上 --model <模型名> 后重试。"
    )


def handle_list_models(args: argparse.Namespace) -> int:
    """处理 --list-models：只读查询当前账户可访问的模型并打印，不做任何文本生成。"""
    print("正在查询当前 OPENAI_API_KEY 可访问的模型列表（不会进行任何文本生成）...")
    try:
        api_key = load_api_key_only()
    except ConfigError as exc:
        print(f"配置错误：{exc}")
        return EXIT_CONFIG_ERROR

    try:
        model_ids = openai_client.list_available_models(api_key)
    except openai_client.ModelListError as exc:
        print(f"获取模型列表失败：{exc}")
        print("请检查网络连接与 OPENAI_API_KEY 权限后重试。")
        return EXIT_GENERAL_FAILURE

    if not model_ids:
        print("未查询到任何可访问的模型，请确认该 API Key 拥有访问模型列表的权限。")
        return EXIT_GENERAL_FAILURE

    _print_model_options(model_ids, print)
    return EXIT_SUCCESS


def should_auto_commit(
    *, safe_to_commit: bool, auto_commit_enabled: bool, no_commit_flag: bool, allow_dirty_flag: bool
) -> bool:
    """判断本次运行是否允许自动提交。

    --allow-dirty 模式下永远返回 False，即便评审通过、配置允许自动提交。
    """
    return safe_to_commit and auto_commit_enabled and not no_commit_flag and not allow_dirty_flag


def build_autodev_commit_message(task_number: int, base_message: str) -> str:
    """将评审器生成的简短提交说明包装为统一的 Auto Dev 提交信息格式。

    统一格式为 `AutoDev(task-NNN): <说明>`，NNN 为本次 Auto Loop 内的任务序号
    （从 1 开始递增，三位数补零），不使用随机或评审器自拟的提交信息前缀。
    GitService 要求首行不超过 80 字符，这里做防御性截断，避免因说明文字过长
    导致本可安全提交的改动被无谓拦截。
    """
    prefix = f"AutoDev(task-{task_number:03d}): "
    stripped = (base_message or "").strip()
    first_line = stripped.splitlines()[0] if stripped else "自动开发任务已完成"
    max_len = 80 - len(prefix)
    if len(first_line) > max_len:
        first_line = first_line[:max_len]
    return prefix + first_line


def run_task_cycle(args: argparse.Namespace, task_number: int) -> tuple[int, str]:
    """执行一次完整的单任务流水线：Planner → Claude → Build/Test → Review → Commit。

    返回 (退出码, 最终状态字符串)。main() 中的 Auto Loop 依据 final_status 判断是否
    立即开始下一个任务：只有状态为 "COMMITTED" 时才会继续循环，其余任何终止状态
    （规划器无更多任务、Claude 失败、验证失败、评审 FAIL/BLOCKED、配置或安全检查
    失败等）都会结束 Auto Loop。
    """
    run_id = _generate_run_id()
    run_dir = RUNTIME_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    logger = setup_run_logger(run_dir, args.verbose)
    logger.info("===== Task #%d 开始 =====", task_number)

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

    def finalize(status: str, error_message: str | None, exit_code: int) -> tuple[int, str]:
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
        logger.info("Task #%d 结束，最终状态：%s", task_number, status)
        logger.info("摘要报告：%s", summary_path)
        # 任务结束后主动释放日志文件句柄，避免 Auto Loop 连续执行多个任务
        # （或测试中反复调用 run_task_cycle）时文件句柄被长期占用。
        for handler in list(logger.handlers):
            handler.close()
            logger.removeHandler(handler)
        return exit_code, status

    logger.info("===== LawGuard Auto Dev V1 —— Task #%d =====", task_number)
    logger.info("运行 ID：%s", run_id)
    logger.info("项目根目录：%s", PROJECT_ROOT)

    # 第一步：加载配置
    try:
        config = load_config(model_override=args.model)
    except ModelNotConfiguredError as exc:
        # 未配置 OPENAI_MODEL：先尝试用已验证的 API Key 做模型自检，
        # 帮助用户了解应该填写哪个模型；无论是否查询成功，都不会自动选择或
        # 静默切换模型，最终仍然安全退出。
        logger.error("配置错误：%s", exc)
        logger.info("正在尝试查询你的 OpenAI 账户可访问的模型，用于提示配置（不会进行任何文本生成）...")
        try:
            model_ids = openai_client.list_available_models(exc.api_key)
            if model_ids:
                _print_model_options(model_ids, logger.error)
            else:
                logger.error("未查询到任何可访问的模型，请确认该 API Key 拥有访问模型列表的权限。")
        except openai_client.ModelListError as list_exc:
            logger.error("尝试查询可用模型列表也失败：%s", list_exc)
            logger.error("请手动确认你的 OpenAI 账户可访问的模型名后，通过 OPENAI_MODEL 或 --model 配置。")
        return finalize("CONFIG_ERROR", str(exc), EXIT_CONFIG_ERROR)
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
        task, planner_usages = openai_client.plan_next_task(client, config, project_context)
    except openai_client.PlannerError as exc:
        report.token_usages.extend(exc.usages)
        logger.error("规划任务失败：%s", exc)
        return finalize("PLANNER_FAILED", str(exc), EXIT_GENERAL_FAILURE)
    except Exception as exc:  # noqa: BLE001 - OpenAI SDK 可能抛出多种异常（鉴权、模型不可用等）
        logger.error("调用 OpenAI 规划器时发生错误：%s", exc)
        return finalize("PLANNER_FAILED", str(exc), EXIT_GENERAL_FAILURE)

    report.token_usages.extend(planner_usages)

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
    logger.info("Build/Test 验证：%s", "PASS" if validation_passed else "FAIL")

    # 第七步：调用 OpenAI 评审器（无论验证是否通过，均收集证据供评审与人工复核）
    logger.info("调用 OpenAI 对本次改动进行代码评审...")
    review_context = context_loader.build_reviewer_context(
        task=task, claude_result=claude_result, validation_results=validation_results
    )
    review: ReviewResult | None = None
    try:
        review, review_usage = openai_client.review_change(client, config, review_context)
        report.token_usages.append(review_usage)
    except openai_client.ReviewerError as exc:
        if exc.usage is not None:
            report.token_usages.append(exc.usage)
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
        commit_message = build_autodev_commit_message(task_number, review.commit_message)
        logger.info("Auto Commit 中，Commit Message：%s", commit_message)
        commit_hash = git.commit(changed_files, commit_message)
        report.git_commit = commit_hash
        logger.info("已自动提交，Commit Hash：%s", commit_hash)
    except GitError as exc:
        msg = f"自动提交失败：{exc}"
        logger.error(msg)
        return finalize("COMMIT_FAILED", msg, EXIT_GENERAL_FAILURE)

    # 第九步：更新 Auto Dev 进度台账（docs/project/AUTODEV_PROGRESS.md）。
    # 单独提交这一文件（而不是并入上一步的任务提交），保持任务代码提交内容纯粹，
    # 同时确保提交后工作区恢复干净，供下一任务的工作区检查正常通过。
    logger.info("Update Progress...")
    try:
        next_candidates = context_loader.read_sot_next_steps()
        progress.record_completed_task(
            PROGRESS_FILE,
            task_number=task_number,
            task_title=task.title,
            commit_hash=commit_hash,
            now_iso=_now_iso(),
            next_candidate_tasks=next_candidates,
        )
        progress_commit_message = build_autodev_commit_message(
            task_number, f"更新 Auto Dev 进度（{task.title}）"
        )
        progress_commit_hash = git.commit([PROGRESS_FILE_RELATIVE], progress_commit_message)
        logger.info("Auto Dev 进度已更新，Commit Hash：%s", progress_commit_hash)
    except GitError as exc:
        # 进度台账提交失败不推翻本任务已经成功提交的事实，只记录警告；
        # 工作区会因此保留未提交的进度文件改动，下一任务启动前的工作区检查
        # 会据此判断是否能安全继续，Auto Loop 无需为此单独增加处理逻辑。
        logger.warning("Auto Dev 进度提交失败（任务本身已成功提交）：%s", exc)

    return finalize("COMMITTED", None, EXIT_SUCCESS)


def main(argv: list[str] | None = None) -> int:
    """Auto Dev 入口：解析参数后持续循环执行任务，直到无更多任务或触发停止条件。

    循环规则：仅当某个任务的最终状态为 "COMMITTED"（评审通过并已自动提交）时才
    立即开始下一个任务；其余任何终止状态（Planner 无更多任务、Claude 执行失败、
    构建/测试失败、Review FAIL/BLOCKED、配置或安全检查失败等）都会结束循环并返回
    对应退出码。`--dry-run`/`--no-commit`/`--allow-dirty` 由于本身不会产出
    "COMMITTED" 状态，效果等同于只执行一个任务后停止，用于单任务预览与调试。
    """
    args = parse_args(argv)

    if args.list_models:
        return handle_list_models(args)

    # 启动恢复：优先读取 Auto Dev 进度台账；不存在时自动创建，格式异常时自动修复，
    # 任何情况下都不会因此停止运行。
    progress_state, progress_was_missing, progress_was_repaired = progress.load_or_repair(PROGRESS_FILE)
    if progress_was_missing:
        print(f"未找到 Auto Dev 进度文件，已自动创建：{PROGRESS_FILE}")
    elif progress_was_repaired:
        print(f"Auto Dev 进度文件格式异常，已自动修复为默认模板：{PROGRESS_FILE}")
    else:
        print(
            f"已恢复 Auto Dev 进度：已完成 {len(progress_state.completed_tasks)} 个任务，"
            f"Last Commit={progress_state.last_commit}"
        )

    # 任务序号从已完成任务数量之后接续编号，避免每次重启进程都从 task-001 重新
    # 计数，与其它历史提交的 AutoDev(task-NNN) 编号冲突。
    task_number = len(progress_state.completed_tasks)
    while True:
        task_number += 1
        print(f"\n===== Task #{task_number} =====")
        exit_code, final_status = run_task_cycle(args, task_number)

        if final_status == "COMMITTED":
            print(f"Task #{task_number} Auto Commit 完成，Starting Task #{task_number + 1}...")
            continue

        if final_status == "BLOCKED_BY_PLANNER":
            print("Planner: DONE")
            print("Auto Dev Finished")
        else:
            print(f"Auto Dev 已停止（Task #{task_number}，最终状态：{final_status}）。")
        return exit_code


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n已手动中断运行。", file=sys.stderr)
        sys.exit(1)
