"""orchestrator.py 主流程单元测试。

全部外部依赖（OpenAI、Claude Code、Git）均通过 unittest.mock 模拟，
不发起真实网络请求、不启动真实子进程、不读写项目真实的 automation/runtime
与 automation/reports 目录（运行目录会被临时重定向到系统临时目录）。
"""
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from automation import orchestrator
from automation.config import Config
from automation.models import CommandResult, DevelopmentTask, ReviewResult


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


def _fake_claude_result(exit_code: int = 0, timed_out: bool = False) -> CommandResult:
    return CommandResult(
        command="claude -p <task_prompt>", cwd=".", exit_code=exit_code,
        stdout="执行摘要：已完成。", stderr="", duration_seconds=1.0, timed_out=timed_out,
    )


class _OrchestratorTestBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        tmp_path = Path(self._tmp.name)
        patches = [
            mock.patch.object(orchestrator, "RUNTIME_DIR", tmp_path / "runtime"),
            mock.patch.object(orchestrator, "REPORTS_DIR", tmp_path / "reports"),
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
        mock_plan.return_value = _fake_task(risk_level="LOW")
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
        mock_plan.return_value = _fake_task(risk_level="LOW")
        mock_run_claude.return_value = _fake_claude_result()
        mock_validate.return_value = ([], True)
        mock_review.return_value = _fake_review(verdict="PASS", safe_to_commit=True)

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
        mock_plan.return_value = _fake_task(risk_level="LOW")
        mock_run_claude.return_value = _fake_claude_result()
        mock_validate.return_value = ([], True)
        mock_review.return_value = _fake_review(verdict="FAIL", safe_to_commit=False)

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
        mock_plan.return_value = _fake_task(risk_level="LOW")
        mock_run_claude.return_value = _fake_claude_result()
        mock_validate.return_value = ([], True)
        mock_review.return_value = _fake_review(verdict="BLOCKED", safe_to_commit=False)

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
        mock_plan.return_value = _fake_task(risk_level="LOW")
        mock_run_claude.return_value = _fake_claude_result()
        failed_result = CommandResult(
            command="npm run build", cwd="web", exit_code=1, stdout="", stderr="类型错误",
            duration_seconds=1.0, timed_out=False,
        )
        mock_validate.return_value = ([failed_result], False)
        mock_review.return_value = _fake_review(verdict="PASS", safe_to_commit=True)

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
        mock_plan.return_value = _fake_task(risk_level="LOW")
        mock_run_claude.return_value = _fake_claude_result(exit_code=1)

        exit_code = orchestrator.main([])

        self.assertEqual(exit_code, orchestrator.EXIT_CLAUDE_FAILURE)
        mock_validate.assert_not_called()
        self.mock_git.commit.assert_not_called()


class TestBlockedByPlannerSkipsClaude(_OrchestratorTestBase):
    @mock.patch("automation.claude_runner.run_claude")
    @mock.patch("automation.openai_client.plan_next_task")
    @mock.patch("automation.openai_client.create_client")
    @mock.patch("automation.context_loader.build_planner_context", return_value="上下文")
    def test_blocked_task_skips_claude_and_commit(self, _ctx, _create_client, mock_plan, mock_run_claude):
        mock_plan.return_value = _fake_task(risk_level="BLOCKED")

        exit_code = orchestrator.main([])

        self.assertEqual(exit_code, orchestrator.EXIT_SECURITY_FAILURE)
        mock_run_claude.assert_not_called()
        self.mock_git.commit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
