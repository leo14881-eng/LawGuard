"""orchestrator.py 主流程单元测试。

全部外部依赖（OpenAI、Claude Code、Git）均通过 unittest.mock 模拟，
不发起真实网络请求、不启动真实子进程、不读写项目真实的 automation/runtime
与 automation/reports 目录（运行目录会被临时重定向到系统临时目录）。
"""
import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from automation import orchestrator, progress
from automation.config import Config
from automation.models import CommandResult, DevelopmentTask, ReviewResult, TokenUsage


def _fake_config(auto_commit: bool = True) -> Config:
    return Config(
        openai_api_key="sk-test-not-real",
        openai_model="gpt-test",
        auto_commit=auto_commit,
        claude_timeout_seconds=10,
        openai_timeout_seconds=10,
    )


def _fake_task(risk_level: str = "LOW") -> DevelopmentTask:
    return DevelopmentTask(
        task_id="T-001", title="示例任务", objective="示例目标", rationale="示例理由",
        scope="示例范围", acceptance_criteria=["构建通过"],
        files_allowed=["web/src/data/stages.ts"], files_forbidden=["LAWGUARD_SOT.md"],
        validation_commands=["npm run build"], risk_level=risk_level,
        requires_sot_update=False, developer_prompt="示例说明",
    )


def _fake_review(verdict: str = "PASS", safe_to_commit: bool = True) -> ReviewResult:
    return ReviewResult(
        verdict=verdict, summary="评审说明", blocking_issues=[],
        non_blocking_suggestions=[], evidence=[], safe_to_commit=safe_to_commit,
        commit_message="feat: 测试改动" if safe_to_commit else "",
    )


def _fake_usage(call_label: str = "planner (第 1 次)") -> TokenUsage:
    return TokenUsage(call_label=call_label, model="gpt-test", prompt_tokens=100, completion_tokens=20, total_tokens=120)


def _fake_plan_result(risk_level: str = "LOW") -> tuple[DevelopmentTask, list[TokenUsage]]:
    return _fake_task(risk_level=risk_level), [_fake_usage()]


def _fake_review_result(verdict: str = "PASS", safe_to_commit: bool = True) -> tuple[ReviewResult, TokenUsage]:
    return _fake_review(verdict=verdict, safe_to_commit=safe_to_commit), _fake_usage("reviewer")


def _fake_claude_result(exit_code: int = 0, timed_out: bool = False) -> CommandResult:
    return CommandResult(
        command="claude -p <task_prompt>", cwd=".", exit_code=exit_code,
        stdout="执行摘要：已完成。", stderr="", duration_seconds=1.0, timed_out=timed_out,
    )


class _OrchestratorTestBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        tmp_path = Path(self._tmp.name)
        self.tmp_path = tmp_path
        self.progress_file = tmp_path / "docs" / "project" / "AUTODEV_PROGRESS.md"
        patches = [
            mock.patch.object(orchestrator, "RUNTIME_DIR", tmp_path / "runtime"),
            mock.patch.object(orchestrator, "REPORTS_DIR", tmp_path / "reports"),
            mock.patch.object(orchestrator, "PROGRESS_FILE", tmp_path / "docs" / "project" / "AUTODEV_PROGRESS.md"),
            mock.patch.object(orchestrator, "load_config", return_value=_fake_config()),
        ]
        self._git_service_cls = mock.patch.object(orchestrator, "GitService")
        patches.append(self._git_service_cls)
        self._mocks = [p.start() for p in patches]
        self.addCleanup(self._tmp.cleanup)
        for p in patches:
            self.addCleanup(p.stop)
        self.mock_git_service_cls = self._mocks[-1]
        self.mock_git = mock.Mock()
        self.mock_git.is_git_repo.return_value = True
        self.mock_git.is_clean.return_value = True
        self.mock_git.get_status_short.return_value = ""
        self.mock_git.get_changed_files.return_value = ["web/src/data/stages.ts"]
        self.mock_git.find_forbidden_violations.return_value = []
        diff_check_result = mock.Mock()
        diff_check_result.returncode = 0
        self.mock_git.diff_check.return_value = diff_check_result
        self.mock_git.commit.return_value = "abc1234"
        self.mock_git_service_cls.return_value = self.mock_git


class TestDryRunDoesNotCallClaude(_OrchestratorTestBase):
    @mock.patch("automation.claude_runner.run_claude")
    @mock.patch("automation.openai_client.plan_next_task")
    @mock.patch("automation.openai_client.create_client")
    @mock.patch("automation.context_loader.build_planner_context", return_value="上下文")
    def test_dry_run_skips_claude_and_commit(
        self, _ctx, _create_client, mock_plan, mock_run_claude
    ):
        mock_plan.return_value = _fake_plan_result(risk_level="LOW")
        exit_code = orchestrator.main(["--dry-run"])
        self.assertEqual(exit_code, orchestrator.EXIT_SUCCESS)
        mock_run_claude.assert_not_called()
        self.mock_git.commit.assert_not_called()


class TestDirtyWorkspaceBlocksOpenAI(_OrchestratorTestBase):
    @mock.patch("automation.openai_client.plan_next_task")
    @mock.patch("automation.openai_client.create_client")
    def test_dirty_workspace_without_allow_dirty_skips_openai(self, mock_create_client, mock_plan):
        self.mock_git.is_clean.return_value = False
        exit_code = orchestrator.main([])
        self.assertEqual(exit_code, orchestrator.EXIT_SECURITY_FAILURE)
        mock_create_client.assert_not_called()
        mock_plan.assert_not_called()


class TestAllowDirtyBlocksCommit(_OrchestratorTestBase):
    @mock.patch("automation.claude_runner.run_claude")
    @mock.patch("automation.validator.run_validation")
    @mock.patch("automation.openai_client.review_change")
    @mock.patch("automation.openai_client.plan_next_task")
    @mock.patch("automation.openai_client.create_client")
    @mock.patch("automation.context_loader.build_reviewer_context", return_value="评审上下文")
    @mock.patch("automation.context_loader.build_planner_context", return_value="上下文")
    def test_allow_dirty_never_commits_even_when_review_passes(
        self, _ctx1, _ctx2, _create_client, mock_plan, mock_review, mock_validate, mock_run_claude
    ):
        self.mock_git.is_clean.return_value = False
        mock_plan.return_value = _fake_plan_result(risk_level="LOW")
        mock_run_claude.return_value = _fake_claude_result()
        mock_validate.return_value = ([], True)
        mock_review.return_value = _fake_review_result(verdict="PASS", safe_to_commit=True)

        exit_code = orchestrator.main(["--allow-dirty"])

        self.assertEqual(exit_code, orchestrator.EXIT_SUCCESS)
        self.mock_git.commit.assert_not_called()


class TestReviewNotPassBlocksCommit(_OrchestratorTestBase):
    @mock.patch("automation.claude_runner.run_claude")
    @mock.patch("automation.validator.run_validation")
    @mock.patch("automation.openai_client.review_change")
    @mock.patch("automation.openai_client.plan_next_task")
    @mock.patch("automation.openai_client.create_client")
    @mock.patch("automation.context_loader.build_reviewer_context", return_value="评审上下文")
    @mock.patch("automation.context_loader.build_planner_context", return_value="上下文")
    def test_fail_verdict_blocks_commit(
        self, _ctx1, _ctx2, _create_client, mock_plan, mock_review, mock_validate, mock_run_claude
    ):
        mock_plan.return_value = _fake_plan_result(risk_level="LOW")
        mock_run_claude.return_value = _fake_claude_result()
        mock_validate.return_value = ([], True)
        mock_review.return_value = _fake_review_result(verdict="FAIL", safe_to_commit=False)

        exit_code = orchestrator.main([])

        self.assertEqual(exit_code, orchestrator.EXIT_REVIEW_FAILED)
        self.mock_git.commit.assert_not_called()

    @mock.patch("automation.claude_runner.run_claude")
    @mock.patch("automation.validator.run_validation")
    @mock.patch("automation.openai_client.review_change")
    @mock.patch("automation.openai_client.plan_next_task")
    @mock.patch("automation.openai_client.create_client")
    @mock.patch("automation.context_loader.build_reviewer_context", return_value="评审上下文")
    @mock.patch("automation.context_loader.build_planner_context", return_value="上下文")
    def test_blocked_verdict_blocks_commit(
        self, _ctx1, _ctx2, _create_client, mock_plan, mock_review, mock_validate, mock_run_claude
    ):
        mock_plan.return_value = _fake_plan_result(risk_level="LOW")
        mock_run_claude.return_value = _fake_claude_result()
        mock_validate.return_value = ([], True)
        mock_review.return_value = _fake_review_result(verdict="BLOCKED", safe_to_commit=False)

        exit_code = orchestrator.main([])

        self.assertEqual(exit_code, orchestrator.EXIT_REVIEW_FAILED)
        self.mock_git.commit.assert_not_called()


class TestValidationFailureBlocksCommit(_OrchestratorTestBase):
    @mock.patch("automation.claude_runner.run_claude")
    @mock.patch("automation.validator.run_validation")
    @mock.patch("automation.openai_client.review_change")
    @mock.patch("automation.openai_client.plan_next_task")
    @mock.patch("automation.openai_client.create_client")
    @mock.patch("automation.context_loader.build_reviewer_context", return_value="评审上下文")
    @mock.patch("automation.context_loader.build_planner_context", return_value="上下文")
    def test_validation_failure_blocks_commit(
        self, _ctx1, _ctx2, _create_client, mock_plan, mock_review, mock_validate, mock_run_claude
    ):
        mock_plan.return_value = _fake_plan_result(risk_level="LOW")
        mock_run_claude.return_value = _fake_claude_result()
        failed_result = CommandResult(
            command="npm run build", cwd="web", exit_code=1, stdout="", stderr="类型错误",
            duration_seconds=1.0, timed_out=False,
        )
        mock_validate.return_value = ([failed_result], False)
        mock_review.return_value = _fake_review_result(verdict="PASS", safe_to_commit=True)

        exit_code = orchestrator.main([])

        self.assertEqual(exit_code, orchestrator.EXIT_VALIDATION_FAILURE)
        self.mock_git.commit.assert_not_called()


class TestClaudeFailureBlocksValidationAndCommit(_OrchestratorTestBase):
    @mock.patch("automation.claude_runner.run_claude")
    @mock.patch("automation.validator.run_validation")
    @mock.patch("automation.openai_client.plan_next_task")
    @mock.patch("automation.openai_client.create_client")
    @mock.patch("automation.context_loader.build_planner_context", return_value="上下文")
    def test_claude_failure_skips_validation_and_commit(
        self, _ctx, _create_client, mock_plan, mock_validate, mock_run_claude
    ):
        mock_plan.return_value = _fake_plan_result(risk_level="LOW")
        mock_run_claude.return_value = _fake_claude_result(exit_code=1)

        exit_code = orchestrator.main([])

        self.assertEqual(exit_code, orchestrator.EXIT_CLAUDE_FAILURE)
        mock_validate.assert_not_called()
        self.mock_git.commit.assert_not_called()


class TestBlockedByPlannerSkipsClaude(_OrchestratorTestBase):
    """risk_level=BLOCKED：存在开发方向，但因权限/依赖/环境/资源等原因无法安全继续。"""

    @mock.patch("automation.claude_runner.run_claude")
    @mock.patch("automation.openai_client.plan_next_task")
    @mock.patch("automation.openai_client.create_client")
    @mock.patch("automation.context_loader.build_planner_context", return_value="上下文")
    def test_blocked_task_skips_claude_and_commit(self, _ctx, _create_client, mock_plan, mock_run_claude):
        mock_plan.return_value = _fake_plan_result(risk_level="BLOCKED")

        exit_code = orchestrator.main([])

        self.assertEqual(exit_code, orchestrator.EXIT_SECURITY_FAILURE)
        mock_run_claude.assert_not_called()
        self.mock_git.commit.assert_not_called()


class TestPlannerDoneEndsAutoDevSuccessfully(_OrchestratorTestBase):
    """risk_level=DONE：项目在 V1 范围内已没有更多可安全规划的新开发任务，正常结束。"""

    @mock.patch("automation.claude_runner.run_claude")
    @mock.patch("automation.openai_client.plan_next_task")
    @mock.patch("automation.openai_client.create_client")
    @mock.patch("automation.context_loader.build_planner_context", return_value="上下文")
    def test_done_task_skips_claude_and_exits_successfully(self, _ctx, _create_client, mock_plan, mock_run_claude):
        mock_plan.return_value = _fake_plan_result(risk_level="DONE")

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = orchestrator.main([])
        output = stdout.getvalue()

        # DONE 代表正常结束（没有更多任务），而不是安全故障，退出码应为 EXIT_SUCCESS。
        self.assertEqual(exit_code, orchestrator.EXIT_SUCCESS)
        mock_run_claude.assert_not_called()
        self.mock_git.commit.assert_not_called()
        self.assertIn("Planner: DONE", output)
        self.assertIn("Auto Dev Finished", output)


class TestAutoLoopContinuesAfterCommit(_OrchestratorTestBase):
    """验证 Auto Dev 全自动循环：任务提交成功后立即开始下一任务，直到 Planner 返回 DONE 为止。"""

    def setUp(self):
        super().setUp()
        # 模拟真实 Git 行为：Progress 文件已在 commit 前写入磁盘，因此
        # get_changed_files() 应同时包含任务代码文件与 AUTODEV_PROGRESS.md，
        # 用于验证两者被合并进同一次 Commit。
        self.mock_git.get_changed_files.return_value = [
            "web/src/data/stages.ts",
            "docs/project/AUTODEV_PROGRESS.md",
        ]

    @mock.patch("automation.claude_runner.run_claude")
    @mock.patch("automation.validator.run_validation")
    @mock.patch("automation.openai_client.review_change")
    @mock.patch("automation.openai_client.plan_next_task")
    @mock.patch("automation.openai_client.create_client")
    @mock.patch("automation.context_loader.build_reviewer_context", return_value="评审上下文")
    @mock.patch("automation.context_loader.build_planner_context", return_value="上下文")
    def test_committed_task_triggers_next_task_until_planner_done(
        self, _ctx1, _ctx2, _create_client, mock_plan, mock_review, mock_validate, mock_run_claude,
    ):
        # 第一个任务规划为 LOW（可安全执行），第二次调用规划器时返回 DONE，
        # 模拟"当前没有更多可安全规划的新任务"，用于验证 Auto Loop 会在此处正常停止。
        mock_plan.side_effect = [
            _fake_plan_result(risk_level="LOW"),
            _fake_plan_result(risk_level="DONE"),
        ]
        mock_run_claude.return_value = _fake_claude_result()
        mock_validate.return_value = ([], True)
        mock_review.return_value = _fake_review_result(verdict="PASS", safe_to_commit=True)

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = orchestrator.main([])
        output = stdout.getvalue()

        # DONE 代表正常跑完所有可安全规划的任务，退出码应为 EXIT_SUCCESS。
        self.assertEqual(exit_code, orchestrator.EXIT_SUCCESS)
        self.assertEqual(mock_plan.call_count, 2)
        mock_run_claude.assert_called_once()

        # 一个任务只产生一个 Commit：代码改动与 AUTODEV_PROGRESS.md 一起提交。
        self.mock_git.commit.assert_called_once()
        commit_files, commit_message = self.mock_git.commit.call_args[0]
        self.assertEqual(
            set(commit_files),
            {"web/src/data/stages.ts", "docs/project/AUTODEV_PROGRESS.md"},
        )
        self.assertEqual(commit_message, "AutoDev(task-001): feat: 测试改动")

        self.assertIn("Task #1", output)
        self.assertIn("Task #2", output)
        self.assertIn("Planner: DONE", output)
        self.assertIn("Auto Dev Finished", output)

        # 进度台账在 Commit 之前已经写入磁盘，且记录了本次完成的任务。
        self.assertTrue(self.progress_file.exists())
        progress_state, was_missing, was_repaired = progress.load_or_repair(self.progress_file)
        self.assertFalse(was_missing)
        self.assertFalse(was_repaired)
        self.assertEqual(progress_state.completed_tasks, ["task-001: 示例任务"])
        self.assertEqual(progress_state.last_commit, commit_message)

    @mock.patch("automation.claude_runner.run_claude")
    @mock.patch("automation.validator.run_validation")
    @mock.patch("automation.openai_client.review_change")
    @mock.patch("automation.openai_client.plan_next_task")
    @mock.patch("automation.openai_client.create_client")
    @mock.patch("automation.context_loader.build_reviewer_context", return_value="评审上下文")
    @mock.patch("automation.context_loader.build_planner_context", return_value="上下文")
    def test_commit_message_task_number_increments_across_tasks(
        self, _ctx1, _ctx2, _create_client, mock_plan, mock_review, mock_validate, mock_run_claude,
    ):
        # 连续两个任务都成功提交，第三次规划返回 DONE 结束循环；
        # 验证提交信息中的任务序号按 001、002 递增，而非使用随机或固定编号。
        mock_plan.side_effect = [
            _fake_plan_result(risk_level="LOW"),
            _fake_plan_result(risk_level="LOW"),
            _fake_plan_result(risk_level="DONE"),
        ]
        mock_run_claude.return_value = _fake_claude_result()
        mock_validate.return_value = ([], True)
        mock_review.return_value = _fake_review_result(verdict="PASS", safe_to_commit=True)

        exit_code = orchestrator.main([])

        self.assertEqual(exit_code, orchestrator.EXIT_SUCCESS)
        # 每个任务只产生一次 Commit，两个任务共 2 次 git commit 调用。
        self.assertEqual(self.mock_git.commit.call_count, 2)
        task1_message = self.mock_git.commit.call_args_list[0][0][1]
        task2_message = self.mock_git.commit.call_args_list[1][0][1]
        self.assertEqual(task1_message, "AutoDev(task-001): feat: 测试改动")
        self.assertEqual(task2_message, "AutoDev(task-002): feat: 测试改动")

        progress_state, _, _ = progress.load_or_repair(self.progress_file)
        self.assertEqual(
            progress_state.completed_tasks,
            ["task-001: 示例任务", "task-002: 示例任务"],
        )


class TestAutoLoopStartupRecovery(_OrchestratorTestBase):
    """验证进程重启后能从 AUTODEV_PROGRESS.md 恢复状态，且任务序号接续、不重复计数。"""

    def setUp(self):
        super().setUp()
        self.mock_git.get_changed_files.return_value = [
            "web/src/data/stages.ts",
            "docs/project/AUTODEV_PROGRESS.md",
        ]

    @mock.patch("automation.claude_runner.run_claude")
    @mock.patch("automation.validator.run_validation")
    @mock.patch("automation.openai_client.review_change")
    @mock.patch("automation.openai_client.plan_next_task")
    @mock.patch("automation.openai_client.create_client")
    @mock.patch("automation.context_loader.build_reviewer_context", return_value="评审上下文")
    @mock.patch("automation.context_loader.build_planner_context", return_value="上下文")
    def test_second_run_resumes_task_numbering_and_history(
        self, _ctx1, _ctx2, _create_client, mock_plan, mock_review, mock_validate, mock_run_claude,
    ):
        mock_run_claude.return_value = _fake_claude_result()
        mock_validate.return_value = ([], True)
        mock_review.return_value = _fake_review_result(verdict="PASS", safe_to_commit=True)

        # 第一次“启动”：完成 task-001 后 Planner 返回 DONE，进程正常退出。
        mock_plan.side_effect = [
            _fake_plan_result(risk_level="LOW"),
            _fake_plan_result(risk_level="DONE"),
        ]
        first_exit_code = orchestrator.main([])
        self.assertEqual(first_exit_code, orchestrator.EXIT_SUCCESS)
        self.assertEqual(self.mock_git.commit.call_count, 1)

        # 模拟进程重启：不删除进度文件，重新调用 main()。
        self.mock_git.commit.reset_mock()
        mock_plan.side_effect = [
            _fake_plan_result(risk_level="LOW"),
            _fake_plan_result(risk_level="DONE"),
        ]

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            second_exit_code = orchestrator.main([])
        output = stdout.getvalue()

        # 第二次启动应打印“已恢复”提示，且新任务编号从 task-002 开始，
        # 而不是重新从 task-001 计数。
        self.assertEqual(second_exit_code, orchestrator.EXIT_SUCCESS)
        self.assertIn("已恢复 Auto Dev 进度", output)
        task_commit_message = self.mock_git.commit.call_args_list[0][0][1]
        self.assertEqual(task_commit_message, "AutoDev(task-002): feat: 测试改动")

        progress_state, _, _ = progress.load_or_repair(self.progress_file)
        self.assertEqual(
            progress_state.completed_tasks,
            ["task-001: 示例任务", "task-002: 示例任务"],
        )


if __name__ == "__main__":
    unittest.main()
