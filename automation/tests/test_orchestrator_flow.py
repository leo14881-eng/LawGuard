"""orchestrator.py 主流程单元测试。

全部外部依赖（OpenAI、Claude Code、Git）均通过 unittest.mock 模拟，
不发起真实网络请求、不启动真实子进程、不读写项目真实的 automation/runtime
与 automation/reports 目录（运行目录会被临时重定向到系统临时目录）。
"""
import contextlib
import io
import itertools
import json
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
    # value_* 字段给出足以通过 Value Gate（ValueScore >= 15）的取值：
    # 8 + 8 + 0 + 2 - 0 - 0 = 18，DONE/BLOCKED 不受 Value Gate 约束，取值无所谓，
    # 这里统一给同一组值以保持 fixture 简单。
    return DevelopmentTask(
        task_id="T-001", title="示例任务", objective="示例目标", rationale="示例理由",
        scope="示例范围", acceptance_criteria=["构建通过"],
        files_allowed=["web/src/data/stages.ts"], files_forbidden=["LAWGUARD_SOT.md"],
        validation_commands=["npm run build"], risk_level=risk_level,
        requires_sot_update=False, developer_prompt="示例说明",
        task_category="产品能力提升",
        value_user=8, value_product=8, value_legal=0, value_tech_debt=2,
        repetition_penalty=0, maintenance_cost=0,
        why_valuable="测试用途：模拟一个明显有价值的任务", why_not_other_candidates="测试用途：无其它候选",
        why_not_duplicate="测试用途：非重复类别", expected_user_benefit="测试用途：模拟用户收益",
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


def _fake_scored_task(
    title: str,
    *,
    value_user: int = 0,
    value_product: int = 0,
    value_legal: int = 0,
    value_tech_debt: int = 0,
    repetition_penalty: int = 0,
    maintenance_cost: int = 0,
    task_category: str = "用户体验重大提升",
    files_allowed: list[str] | None = None,
    rationale: str = "",
) -> DevelopmentTask:
    """构造一个可自定义 ValueScore 分项/标题的候选任务，用于 Planner Candidate
    Loop 测试（见 TestPlannerCandidateLoop）。files_allowed 未显式指定时按标题
    派生一个确定性的"唯一"路径，避免多个本意不同的候选任务因为共用同一个默认
    files_allowed 而被候选去重误判为重复（同一文件完全可能承载多个不相关改动，
    见 value_gate.is_duplicate_candidate 的规则 3）。
    """
    return DevelopmentTask(
        task_id="T-CAND", title=title, objective=title, rationale=rationale,
        scope="示例范围", acceptance_criteria=["构建通过"],
        files_allowed=files_allowed or [f"web/src/views/_test_{abs(hash(title)) % 100000}.vue"],
        files_forbidden=["LAWGUARD_SOT.md"],
        validation_commands=["npm run build"], risk_level="LOW",
        requires_sot_update=False, developer_prompt="示例说明",
        task_category=task_category,
        value_user=value_user, value_product=value_product, value_legal=value_legal,
        value_tech_debt=value_tech_debt, repetition_penalty=repetition_penalty, maintenance_cost=maintenance_cost,
        why_valuable="测试用途", why_not_other_candidates="测试用途",
        why_not_duplicate="测试用途", expected_user_benefit="测试用途",
    )


def _plan_result_for(task: DevelopmentTask) -> tuple[DevelopmentTask, list[TokenUsage]]:
    return task, [_fake_usage()]


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
        self.mock_git.get_diff.return_value = ""
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

        # verdict=BLOCKED 代表需要人工决策，与"评审判 FAIL"是两类不同的停止原因，
        # 使用与 Planner 级 BLOCKED 一致的 EXIT_SECURITY_FAILURE。
        self.assertEqual(exit_code, orchestrator.EXIT_SECURITY_FAILURE)
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
        # MEDIUM Risk 不满足 Auto Fix 的 LOW Risk 条件，Validation 失败必须立即停止，
        # 不做自动修复；同时验证 Validation FAIL 时不得调用 Review（避免两套冲突意见）。
        mock_plan.return_value = _fake_plan_result(risk_level="MEDIUM")
        mock_run_claude.return_value = _fake_claude_result()
        failed_result = CommandResult(
            command="npm run build", cwd="web", exit_code=1, stdout="", stderr="类型错误",
            duration_seconds=1.0, timed_out=False,
        )
        mock_validate.return_value = ([failed_result], False)
        mock_review.return_value = _fake_review_result(verdict="PASS", safe_to_commit=True)

        exit_code = orchestrator.main([])

        self.assertEqual(exit_code, orchestrator.EXIT_VALIDATION_FAILURE)
        self.assertEqual(mock_run_claude.call_count, 1)
        mock_review.assert_not_called()
        self.mock_git.commit.assert_not_called()


class TestValidationAutoFixLowRisk(_OrchestratorTestBase):
    """Validation Auto Fix 回归测试：Build/Test/Type Check 失败时，LOW Risk 任务应自动
    修复而不是直接停止；MEDIUM Risk 与连续 3 次仍失败时必须停止。"""

    def setUp(self):
        super().setUp()
        self.mock_git.get_changed_files.return_value = [
            "web/src/components/QuickNavCard.vue",
            "docs/project/AUTODEV_PROGRESS.md",
        ]

    @staticmethod
    def _failed_build_result(marker: str = "1") -> tuple[list[CommandResult], bool]:
        return (
            [CommandResult(
                command="npm run build", cwd="web", exit_code=1, stdout="",
                stderr=f"类型错误 {marker}", duration_seconds=1.0, timed_out=False,
            )],
            False,
        )

    @mock.patch("automation.claude_runner.run_claude")
    @mock.patch("automation.validator.run_validation")
    @mock.patch("automation.openai_client.review_change")
    @mock.patch("automation.openai_client.plan_next_task")
    @mock.patch("automation.openai_client.create_client")
    @mock.patch("automation.context_loader.build_reviewer_context", return_value="评审上下文")
    @mock.patch("automation.context_loader.build_planner_context", return_value="上下文")
    def test_low_risk_validation_fail_then_pass_retries_and_commits(
        self, _ctx1, _ctx2, _create_client, mock_plan, mock_review, mock_validate, mock_run_claude,
    ):
        # Attempt 1：Claude 生成的改动导致 npm run build FAIL；
        # Attempt 2：Claude 根据 Validation Fix Prompt 修复后 Validation PASS + Review PASS。
        mock_plan.side_effect = [
            _fake_plan_result(risk_level="LOW"),
            _fake_plan_result(risk_level="DONE"),
        ]
        mock_run_claude.return_value = _fake_claude_result()
        mock_validate.side_effect = [self._failed_build_result(), ([], True)]
        mock_review.return_value = _fake_review_result(verdict="PASS", safe_to_commit=True)
        self.mock_git.get_diff.side_effect = (f"diff-{i}" for i in itertools.count(1))

        exit_code = orchestrator.main([])

        self.assertEqual(exit_code, orchestrator.EXIT_SUCCESS)
        self.assertEqual(mock_run_claude.call_count, 2)
        # Validation FAIL 的第一轮不调用 Review，只有 Validation PASS 之后才调用一次。
        self.assertEqual(mock_review.call_count, 1)
        self.mock_git.commit.assert_called_once()

    @mock.patch("automation.claude_runner.run_claude")
    @mock.patch("automation.validator.run_validation")
    @mock.patch("automation.openai_client.review_change")
    @mock.patch("automation.openai_client.plan_next_task")
    @mock.patch("automation.openai_client.create_client")
    @mock.patch("automation.context_loader.build_reviewer_context", return_value="评审上下文")
    @mock.patch("automation.context_loader.build_planner_context", return_value="上下文")
    def test_low_risk_validation_fail_then_validation_pass_review_fail_then_pass(
        self, _ctx1, _ctx2, _create_client, mock_plan, mock_review, mock_validate, mock_run_claude,
    ):
        # Attempt 1：Validation FAIL（Validation Fix）；
        # Attempt 2：Validation PASS 但 Review FAIL（Review Fix）；
        # Attempt 3：Validation PASS 且 Review PASS → Commit。三者共享同一个 3 次上限。
        mock_plan.side_effect = [
            _fake_plan_result(risk_level="LOW"),
            _fake_plan_result(risk_level="DONE"),
        ]
        mock_run_claude.return_value = _fake_claude_result()
        mock_validate.side_effect = [self._failed_build_result(), ([], True), ([], True)]
        mock_review.side_effect = [
            _fake_review_result(verdict="FAIL", safe_to_commit=False),
            _fake_review_result(verdict="PASS", safe_to_commit=True),
        ]
        self.mock_git.get_diff.side_effect = (f"diff-{i}" for i in itertools.count(1))

        exit_code = orchestrator.main([])

        self.assertEqual(exit_code, orchestrator.EXIT_SUCCESS)
        self.assertEqual(mock_run_claude.call_count, orchestrator.MAX_ATTEMPTS)
        self.assertEqual(mock_review.call_count, 2)
        self.mock_git.commit.assert_called_once()

    @mock.patch("automation.claude_runner.run_claude")
    @mock.patch("automation.validator.run_validation")
    @mock.patch("automation.openai_client.review_change")
    @mock.patch("automation.openai_client.plan_next_task")
    @mock.patch("automation.openai_client.create_client")
    @mock.patch("automation.context_loader.build_reviewer_context", return_value="评审上下文")
    @mock.patch("automation.context_loader.build_planner_context", return_value="上下文")
    def test_low_risk_validation_fails_three_times_then_stops(
        self, _ctx1, _ctx2, _create_client, mock_plan, mock_review, mock_validate, mock_run_claude,
    ):
        mock_plan.return_value = _fake_plan_result(risk_level="LOW")
        mock_run_claude.return_value = _fake_claude_result()
        mock_validate.side_effect = [
            self._failed_build_result(marker=str(i)) for i in range(1, orchestrator.MAX_ATTEMPTS + 1)
        ]
        mock_review.return_value = _fake_review_result(verdict="PASS", safe_to_commit=True)
        self.mock_git.get_diff.side_effect = (f"diff-{i}" for i in itertools.count(1))

        exit_code = orchestrator.main([])

        self.assertEqual(exit_code, orchestrator.EXIT_VALIDATION_FAILURE)
        self.assertEqual(mock_run_claude.call_count, orchestrator.MAX_ATTEMPTS)
        mock_review.assert_not_called()
        self.mock_git.commit.assert_not_called()

    @mock.patch("automation.claude_runner.run_claude")
    @mock.patch("automation.validator.run_validation")
    @mock.patch("automation.openai_client.review_change")
    @mock.patch("automation.openai_client.plan_next_task")
    @mock.patch("automation.openai_client.create_client")
    @mock.patch("automation.context_loader.build_reviewer_context", return_value="评审上下文")
    @mock.patch("automation.context_loader.build_planner_context", return_value="上下文")
    def test_medium_risk_validation_fail_does_not_retry(
        self, _ctx1, _ctx2, _create_client, mock_plan, mock_review, mock_validate, mock_run_claude,
    ):
        mock_plan.return_value = _fake_plan_result(risk_level="MEDIUM")
        mock_run_claude.return_value = _fake_claude_result()
        mock_validate.return_value = self._failed_build_result()
        mock_review.return_value = _fake_review_result(verdict="PASS", safe_to_commit=True)

        exit_code = orchestrator.main([])

        self.assertEqual(exit_code, orchestrator.EXIT_VALIDATION_FAILURE)
        self.assertEqual(mock_run_claude.call_count, 1)
        mock_review.assert_not_called()
        self.mock_git.commit.assert_not_called()


class TestReviewRetryLowRisk(_OrchestratorTestBase):
    """Review Retry 回归测试：模拟真实 Task #4（QuickNavCard aria-label，LOW Risk）曾经出现的
    "Review FAIL → 自动 Retry → 重新 Build → 重新 Review → PASS → Commit → 自动进入下一任务"
    完整链路，验证全程无需人工介入。"""

    def setUp(self):
        super().setUp()
        self.mock_git.get_changed_files.return_value = [
            "web/src/components/QuickNavCard.vue",
            "docs/project/AUTODEV_PROGRESS.md",
        ]

    @mock.patch("automation.claude_runner.run_claude")
    @mock.patch("automation.validator.run_validation")
    @mock.patch("automation.openai_client.review_change")
    @mock.patch("automation.openai_client.plan_next_task")
    @mock.patch("automation.openai_client.create_client")
    @mock.patch("automation.context_loader.build_reviewer_context", return_value="评审上下文")
    @mock.patch("automation.context_loader.build_planner_context", return_value="上下文")
    def test_low_risk_fail_then_pass_retries_and_commits(
        self, _ctx1, _ctx2, _create_client, mock_plan, mock_review, mock_validate, mock_run_claude,
    ):
        # 第 1 轮 Review FAIL（对应真实 Task #4：aria-label 未严格等于卡片标题），
        # 第 2 轮（Retry Attempt 2）修复后 Review PASS；随后 Planner 返回 DONE 结束循环。
        mock_plan.side_effect = [
            _fake_plan_result(risk_level="LOW"),
            _fake_plan_result(risk_level="DONE"),
        ]
        mock_run_claude.return_value = _fake_claude_result()
        mock_validate.return_value = ([], True)
        mock_review.side_effect = [
            _fake_review_result(verdict="FAIL", safe_to_commit=False),
            _fake_review_result(verdict="PASS", safe_to_commit=True),
        ]

        exit_code = orchestrator.main([])

        self.assertEqual(exit_code, orchestrator.EXIT_SUCCESS)
        # 自动 Retry 一次：Claude 被调用两次（初次执行 + 1 次修复），评审被调用两次。
        self.assertEqual(mock_run_claude.call_count, 2)
        self.assertEqual(mock_review.call_count, 2)
        # 最终 Review PASS 后正常提交，且只产生一次 Commit（不会为 Retry 额外提交）。
        self.mock_git.commit.assert_called_once()

    @mock.patch("automation.claude_runner.run_claude")
    @mock.patch("automation.validator.run_validation")
    @mock.patch("automation.openai_client.review_change")
    @mock.patch("automation.openai_client.plan_next_task")
    @mock.patch("automation.openai_client.create_client")
    @mock.patch("automation.context_loader.build_reviewer_context", return_value="评审上下文")
    @mock.patch("automation.context_loader.build_planner_context", return_value="上下文")
    def test_medium_risk_fail_stops_immediately_without_retry(
        self, _ctx1, _ctx2, _create_client, mock_plan, mock_review, mock_validate, mock_run_claude,
    ):
        mock_plan.return_value = _fake_plan_result(risk_level="MEDIUM")
        mock_run_claude.return_value = _fake_claude_result()
        mock_validate.return_value = ([], True)
        mock_review.return_value = _fake_review_result(verdict="FAIL", safe_to_commit=False)

        exit_code = orchestrator.main([])

        self.assertEqual(exit_code, orchestrator.EXIT_REVIEW_FAILED)
        self.assertEqual(mock_run_claude.call_count, 1)
        self.assertEqual(mock_review.call_count, 1)
        self.mock_git.commit.assert_not_called()

    @mock.patch("automation.claude_runner.run_claude")
    @mock.patch("automation.validator.run_validation")
    @mock.patch("automation.openai_client.review_change")
    @mock.patch("automation.openai_client.plan_next_task")
    @mock.patch("automation.openai_client.create_client")
    @mock.patch("automation.context_loader.build_reviewer_context", return_value="评审上下文")
    @mock.patch("automation.context_loader.build_planner_context", return_value="上下文")
    def test_low_risk_exhausts_three_attempts_then_stops(
        self, _ctx1, _ctx2, _create_client, mock_plan, mock_review, mock_validate, mock_run_claude,
    ):
        # 每次 Review 结论的 blocking_issues 都不同，且每次 Git Diff 也不同，确保不会
        # 触发"无进展保护"提前停止，真正跑满 3 个 Attempt 后再因用尽次数而停止。
        mock_plan.return_value = _fake_plan_result(risk_level="LOW")
        mock_run_claude.return_value = _fake_claude_result()
        mock_validate.return_value = ([], True)
        mock_review.side_effect = [
            (
                ReviewResult(
                    verdict="FAIL", summary=f"第 {i} 次仍未通过", blocking_issues=[f"问题 {i}"],
                    non_blocking_suggestions=[], evidence=[], safe_to_commit=False, commit_message="",
                ),
                _fake_usage("reviewer"),
            )
            for i in range(1, orchestrator.MAX_ATTEMPTS + 1)
        ]
        self.mock_git.get_diff.side_effect = (f"diff-{i}" for i in itertools.count(1))

        exit_code = orchestrator.main([])

        self.assertEqual(exit_code, orchestrator.EXIT_REVIEW_FAILED)
        self.assertEqual(mock_run_claude.call_count, orchestrator.MAX_ATTEMPTS)
        self.assertEqual(mock_review.call_count, orchestrator.MAX_ATTEMPTS)
        self.mock_git.commit.assert_not_called()

    @mock.patch("automation.claude_runner.run_claude")
    @mock.patch("automation.validator.run_validation")
    @mock.patch("automation.openai_client.review_change")
    @mock.patch("automation.openai_client.plan_next_task")
    @mock.patch("automation.openai_client.create_client")
    @mock.patch("automation.context_loader.build_reviewer_context", return_value="评审上下文")
    @mock.patch("automation.context_loader.build_planner_context", return_value="上下文")
    def test_low_risk_no_progress_guard_stops_before_max_attempts(
        self, _ctx1, _ctx2, _create_client, mock_plan, mock_review, mock_validate, mock_run_claude,
    ):
        # Git Diff 与 Review 结论（verdict + blocking_issues）连续两次完全相同，
        # 说明修复没有产生实质效果，应在用尽 3 个 Attempt 之前提前停止。
        mock_plan.return_value = _fake_plan_result(risk_level="LOW")
        mock_run_claude.return_value = _fake_claude_result()
        mock_validate.return_value = ([], True)
        mock_review.return_value = _fake_review_result(verdict="FAIL", safe_to_commit=False)
        self.mock_git.get_diff.return_value = "同一份 diff"

        exit_code = orchestrator.main([])

        self.assertEqual(exit_code, orchestrator.EXIT_REVIEW_FAILED)
        self.assertLess(mock_run_claude.call_count, orchestrator.MAX_ATTEMPTS)
        self.mock_git.commit.assert_not_called()

    @mock.patch("automation.claude_runner.run_claude")
    @mock.patch("automation.validator.run_validation")
    @mock.patch("automation.openai_client.review_change")
    @mock.patch("automation.openai_client.plan_next_task")
    @mock.patch("automation.openai_client.create_client")
    @mock.patch("automation.context_loader.build_reviewer_context", return_value="评审上下文")
    @mock.patch("automation.context_loader.build_planner_context", return_value="上下文")
    def test_low_risk_blocked_verdict_does_not_retry(
        self, _ctx1, _ctx2, _create_client, mock_plan, mock_review, mock_validate, mock_run_claude,
    ):
        # verdict=BLOCKED 代表评审要求人工决策，即便任务是 LOW Risk 也不允许自动 Retry。
        mock_plan.return_value = _fake_plan_result(risk_level="LOW")
        mock_run_claude.return_value = _fake_claude_result()
        mock_validate.return_value = ([], True)
        mock_review.return_value = _fake_review_result(verdict="BLOCKED", safe_to_commit=False)

        exit_code = orchestrator.main([])

        self.assertEqual(exit_code, orchestrator.EXIT_SECURITY_FAILURE)
        self.assertEqual(mock_run_claude.call_count, 1)
        self.assertEqual(mock_review.call_count, 1)
        self.mock_git.commit.assert_not_called()

    @mock.patch("automation.claude_runner.run_claude")
    @mock.patch("automation.validator.run_validation")
    @mock.patch("automation.openai_client.review_change")
    @mock.patch("automation.openai_client.plan_next_task")
    @mock.patch("automation.openai_client.create_client")
    @mock.patch("automation.context_loader.build_reviewer_context", return_value="评审上下文")
    @mock.patch("automation.context_loader.build_planner_context", return_value="上下文")
    def test_review_api_failure_is_not_treated_as_code_fail_and_does_not_retry(
        self, _ctx1, _ctx2, _create_client, mock_plan, mock_review, mock_validate, mock_run_claude,
    ):
        # Review API 调用失败（这里模拟网络类异常）与代码 Review FAIL 是两类不同的
        # 失败：前者没有结构化的修复依据，不应被当作可自动修复的 LOW Risk 问题重试。
        mock_plan.return_value = _fake_plan_result(risk_level="LOW")
        mock_run_claude.return_value = _fake_claude_result()
        mock_validate.return_value = ([], True)
        mock_review.side_effect = ConnectionError("网络暂时不可用")

        exit_code = orchestrator.main([])

        self.assertEqual(exit_code, orchestrator.EXIT_GENERAL_FAILURE)
        self.assertEqual(mock_run_claude.call_count, 1)
        self.mock_git.commit.assert_not_called()

    @mock.patch("automation.claude_runner.build_review_fix_prompt")
    @mock.patch("automation.claude_runner.run_claude")
    @mock.patch("automation.validator.run_validation")
    @mock.patch("automation.openai_client.review_change")
    @mock.patch("automation.openai_client.plan_next_task")
    @mock.patch("automation.openai_client.create_client")
    @mock.patch("automation.context_loader.build_reviewer_context", return_value="评审上下文")
    @mock.patch("automation.context_loader.build_planner_context", return_value="上下文")
    def test_review_fix_prompt_includes_blocking_issues_and_git_diff(
        self, _ctx1, _ctx2, _create_client, mock_plan, mock_review, mock_validate, mock_run_claude,
        mock_build_review_fix_prompt,
    ):
        mock_plan.side_effect = [
            _fake_plan_result(risk_level="LOW"),
            _fake_plan_result(risk_level="DONE"),
        ]
        mock_run_claude.return_value = _fake_claude_result()
        mock_validate.return_value = ([], True)
        mock_review.side_effect = [
            _fake_review_result(verdict="FAIL", safe_to_commit=False),
            _fake_review_result(verdict="PASS", safe_to_commit=True),
        ]
        self.mock_git.get_diff.return_value = "diff --git a/x b/x\n+ 修复内容"
        mock_build_review_fix_prompt.return_value = "fix prompt"

        orchestrator.main([])

        mock_build_review_fix_prompt.assert_called_once()
        _, kwargs = mock_build_review_fix_prompt.call_args
        self.assertEqual(kwargs["blocking_issues"], [])
        self.assertIn("diff --git a/x b/x", kwargs["git_diff_text"])

    @mock.patch("automation.claude_runner.build_validation_fix_prompt")
    @mock.patch("automation.claude_runner.run_claude")
    @mock.patch("automation.validator.run_validation")
    @mock.patch("automation.openai_client.review_change")
    @mock.patch("automation.openai_client.plan_next_task")
    @mock.patch("automation.openai_client.create_client")
    @mock.patch("automation.context_loader.build_reviewer_context", return_value="评审上下文")
    @mock.patch("automation.context_loader.build_planner_context", return_value="上下文")
    def test_validation_fix_prompt_includes_failure_output_and_git_diff(
        self, _ctx1, _ctx2, _create_client, mock_plan, mock_review, mock_validate, mock_run_claude,
        mock_build_validation_fix_prompt,
    ):
        mock_plan.side_effect = [
            _fake_plan_result(risk_level="LOW"),
            _fake_plan_result(risk_level="DONE"),
        ]
        mock_run_claude.return_value = _fake_claude_result()
        failed_result = CommandResult(
            command="npm run build", cwd="web", exit_code=1, stdout="编译输出",
            stderr="类型错误：Type 'string' is not assignable", duration_seconds=1.0, timed_out=False,
        )
        mock_validate.side_effect = [([failed_result], False), ([], True)]
        mock_review.return_value = _fake_review_result(verdict="PASS", safe_to_commit=True)
        self.mock_git.get_diff.return_value = "diff --git a/x b/x\n+ 有类型错误的改动"
        mock_build_validation_fix_prompt.return_value = "fix prompt"

        orchestrator.main([])

        mock_build_validation_fix_prompt.assert_called_once()
        _, kwargs = mock_build_validation_fix_prompt.call_args
        self.assertEqual(kwargs["failed_command"], "npm run build")
        self.assertIn("类型错误", kwargs["stderr"])
        self.assertIn("diff --git a/x b/x", kwargs["git_diff_text"])
        # Validation FAIL 的这一轮不应调用 Review。
        mock_review.assert_called_once()


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


class TestPlannerCandidateLoop(_OrchestratorTestBase):
    """Planner Candidate Loop 回归测试（2026-07-26 新增）：单个候选被 Value Gate
    拒绝不应立即结束整个运行，应在 PLANNER_CANDIDATE_LIMIT 次内继续请求新候选，
    只有连续全部被拒绝才以 NO_HIGH_VALUE_TASK 结束；候选阶段全程不得调用 Claude。
    """

    def _write_history_task(
        self, run_id: str, title: str, *, risk_level: str = "LOW",
        # 默认分值给一个不会意外触发 Stop Rule（均分 < 8 即停止）的正常分数
        # （8+7=15），只有明确要模拟"低价值历史"的测试才会显式传入低分覆盖。
        value_user: int = 8, value_product: int = 7, value_legal: int = 0,
        value_tech_debt: int = 0, repetition_penalty: int = 0, maintenance_cost: int = 0,
    ) -> None:
        run_dir = self.tmp_path / "runtime" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        data = {
            "title": title, "objective": title, "risk_level": risk_level,
            "value_user": value_user, "value_product": value_product, "value_legal": value_legal,
            "value_tech_debt": value_tech_debt, "repetition_penalty": repetition_penalty,
            "maintenance_cost": maintenance_cost, "task_category": "用户体验重大提升",
        }
        (run_dir / "task.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    @mock.patch("automation.claude_runner.build_task_prompt")
    @mock.patch("automation.claude_runner.run_claude")
    @mock.patch("automation.validator.run_validation")
    @mock.patch("automation.openai_client.review_change")
    @mock.patch("automation.openai_client.plan_next_task")
    @mock.patch("automation.openai_client.create_client")
    @mock.patch("automation.context_loader.build_reviewer_context", return_value="评审上下文")
    @mock.patch("automation.context_loader.build_planner_context", return_value="上下文")
    def test_first_candidate_rejected_second_passes_develops_only_second(
        self, _ctx1, _ctx2, _create_client, mock_plan, mock_review, mock_validate, mock_run_claude,
        mock_build_task_prompt,
    ):
        low = _fake_scored_task("Privacy 页面增加打印按钮", value_user=2, value_product=2)  # score=4 < 15
        high = _fake_scored_task("新增本地全文搜索功能", value_user=9, value_product=8)  # score=17 >= 15
        mock_plan.side_effect = [
            _plan_result_for(low), _plan_result_for(high), _plan_result_for(_fake_task(risk_level="DONE")),
        ]
        mock_run_claude.return_value = _fake_claude_result()
        mock_validate.return_value = ([], True)
        mock_review.return_value = _fake_review_result(verdict="PASS", safe_to_commit=True)
        mock_build_task_prompt.return_value = "prompt"

        exit_code = orchestrator.main([])

        self.assertEqual(exit_code, orchestrator.EXIT_SUCCESS)
        self.assertEqual(mock_plan.call_count, 3)
        self.assertEqual(mock_run_claude.call_count, 1)
        self.mock_git.commit.assert_called_once()
        # 只有第二个候选（高分）进入了 Claude 开发流程，不是第一个（低分被拒绝）。
        _, kwargs = mock_build_task_prompt.call_args
        self.assertEqual(kwargs["task_title"], "新增本地全文搜索功能")

    @mock.patch("automation.claude_runner.build_task_prompt")
    @mock.patch("automation.claude_runner.run_claude")
    @mock.patch("automation.validator.run_validation")
    @mock.patch("automation.openai_client.review_change")
    @mock.patch("automation.openai_client.plan_next_task")
    @mock.patch("automation.openai_client.create_client")
    @mock.patch("automation.context_loader.build_reviewer_context", return_value="评审上下文")
    @mock.patch("automation.context_loader.build_planner_context", return_value="上下文")
    def test_first_candidate_repetition_blocked_second_passes(
        self, _ctx1, _ctx2, _create_client, mock_plan, mock_review, mock_validate, mock_run_claude,
        mock_build_task_prompt,
    ):
        # 预置 3 条历史记录，使 PrintButton 类别达到重复上限（REPETITION_LIMIT=3）。
        for i in range(3):
            self._write_history_task(f"20200101_00000{i}_hist{i}", f"页面 {i} 新增打印按钮")

        # 第一个候选即使自评分很高，也会被"重复类别达到上限"硬性拦截（未声明严重缺陷）。
        repetitive_high = _fake_scored_task(
            "Documents 页面新增打印本页入口", value_user=9, value_product=9
        )
        different = _fake_scored_task("为 Legal Sources 页面补全官方链接与发布日期", value_user=8, value_legal=9)
        mock_plan.side_effect = [
            _plan_result_for(repetitive_high), _plan_result_for(different),
            _plan_result_for(_fake_task(risk_level="DONE")),
        ]
        mock_run_claude.return_value = _fake_claude_result()
        mock_validate.return_value = ([], True)
        mock_review.return_value = _fake_review_result(verdict="PASS", safe_to_commit=True)
        mock_build_task_prompt.return_value = "prompt"

        exit_code = orchestrator.main([])

        self.assertEqual(exit_code, orchestrator.EXIT_SUCCESS)
        self.assertEqual(mock_plan.call_count, 3)
        self.mock_git.commit.assert_called_once()
        _, kwargs = mock_build_task_prompt.call_args
        self.assertEqual(kwargs["task_title"], "为 Legal Sources 页面补全官方链接与发布日期")

    @mock.patch("automation.claude_runner.run_claude")
    @mock.patch("automation.openai_client.plan_next_task")
    @mock.patch("automation.openai_client.create_client")
    @mock.patch("automation.context_loader.build_planner_context", return_value="上下文")
    def test_three_low_value_candidates_end_with_no_high_value_task(
        self, _ctx, _create_client, mock_plan, mock_run_claude
    ):
        candidates = [
            _fake_scored_task("Privacy 页面增加打印按钮", value_user=2, value_product=2),
            _fake_scored_task("Documents 页面调整间距", value_user=1, value_product=1),
            _fake_scored_task("为组件补充 aria-label", value_user=2, value_product=1),
        ]
        mock_plan.side_effect = [_plan_result_for(c) for c in candidates]

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = orchestrator.main([])
        output = stdout.getvalue()

        self.assertEqual(exit_code, orchestrator.EXIT_SUCCESS)
        self.assertEqual(mock_plan.call_count, 3)
        mock_run_claude.assert_not_called()
        self.mock_git.commit.assert_not_called()
        self.assertIn("个候选均未通过 Value Gate", output)

    @mock.patch("automation.claude_runner.run_claude")
    @mock.patch("automation.openai_client.plan_next_task")
    @mock.patch("automation.openai_client.create_client")
    @mock.patch("automation.context_loader.build_planner_context", return_value="上下文")
    def test_synonymous_print_button_rewrites_detected_as_duplicate(
        self, _ctx, _create_client, mock_plan, mock_run_claude
    ):
        # 候选 1：低分，被普通 Value Gate 拒绝；候选 2/3：即使自评分很高，也因为
        # 与候选 1 命中同一个重复类别（PrintButton）而被候选去重直接拒绝，
        # 不会因为换了页面名称/措辞就蒙混过关。
        c1 = _fake_scored_task("Privacy 页面增加 PrintPageButton", value_user=2, value_product=2)
        c2 = _fake_scored_task("Privacy 页面新增打印入口", value_user=9, value_product=9)
        c3 = _fake_scored_task("为隐私政策页补充打印入口", value_user=9, value_product=9)
        mock_plan.side_effect = [_plan_result_for(c1), _plan_result_for(c2), _plan_result_for(c3)]

        exit_code = orchestrator.main([])

        self.assertEqual(exit_code, orchestrator.EXIT_SUCCESS)
        self.assertEqual(mock_plan.call_count, 3)
        mock_run_claude.assert_not_called()
        self.mock_git.commit.assert_not_called()

    @mock.patch("automation.claude_runner.run_claude")
    @mock.patch("automation.openai_client.plan_next_task")
    @mock.patch("automation.openai_client.create_client")
    @mock.patch("automation.context_loader.build_planner_context", return_value="上下文")
    def test_stop_rule_triggers_before_any_planner_call(
        self, _ctx, _create_client, mock_plan, mock_run_claude
    ):
        # 预置 20 条低分历史记录（均分 4 < Stop Rule 阈值 8），应在调用 Planner 之前
        # 就直接以 STOPPED_LOW_VALUE 结束，Candidate Loop 完全不运行。
        for i in range(20):
            self._write_history_task(f"20200101_{i:06d}_hist", f"低价值历史任务 {i}", value_user=2, value_product=2)

        exit_code = orchestrator.main([])

        self.assertEqual(exit_code, orchestrator.EXIT_SUCCESS)
        mock_plan.assert_not_called()
        mock_run_claude.assert_not_called()
        self.mock_git.commit.assert_not_called()

    @mock.patch("automation.claude_runner.run_claude")
    @mock.patch("automation.validator.run_validation")
    @mock.patch("automation.openai_client.review_change")
    @mock.patch("automation.openai_client.plan_next_task")
    @mock.patch("automation.openai_client.create_client")
    @mock.patch("automation.context_loader.build_reviewer_context", return_value="评审上下文")
    @mock.patch("automation.context_loader.build_planner_context", return_value="上下文")
    def test_candidate_one_passes_calls_planner_once(
        self, _ctx1, _ctx2, _create_client, mock_plan, mock_review, mock_validate, mock_run_claude,
    ):
        high = _fake_scored_task("新增本地全文搜索功能", value_user=9, value_product=8)
        mock_plan.return_value = _plan_result_for(high)
        mock_run_claude.return_value = _fake_claude_result()
        mock_validate.return_value = ([], True)
        mock_review.return_value = _fake_review_result(verdict="PASS", safe_to_commit=True)

        exit_code = orchestrator.main(["--dry-run"])

        self.assertEqual(exit_code, orchestrator.EXIT_SUCCESS)
        self.assertEqual(mock_plan.call_count, 1)
        mock_run_claude.assert_not_called()

    @mock.patch("automation.claude_runner.run_claude")
    @mock.patch("automation.validator.run_validation")
    @mock.patch("automation.openai_client.review_change")
    @mock.patch("automation.openai_client.plan_next_task")
    @mock.patch("automation.openai_client.create_client")
    @mock.patch("automation.context_loader.build_reviewer_context", return_value="评审上下文")
    @mock.patch("automation.context_loader.build_planner_context", return_value="上下文")
    def test_candidates_1_and_2_rejected_candidate_3_passes(
        self, _ctx1, _ctx2, _create_client, mock_plan, mock_review, mock_validate, mock_run_claude,
    ):
        low1 = _fake_scored_task("Privacy 页面增加打印按钮", value_user=2, value_product=2)
        low2 = _fake_scored_task("Documents 页面调整间距", value_user=1, value_product=1)
        high3 = _fake_scored_task("新增本地全文搜索功能", value_user=9, value_product=8)
        mock_plan.side_effect = [
            _plan_result_for(low1), _plan_result_for(low2), _plan_result_for(high3),
            _plan_result_for(_fake_task(risk_level="DONE")),
        ]
        mock_run_claude.return_value = _fake_claude_result()
        mock_validate.return_value = ([], True)
        mock_review.return_value = _fake_review_result(verdict="PASS", safe_to_commit=True)

        exit_code = orchestrator.main([])

        self.assertEqual(exit_code, orchestrator.EXIT_SUCCESS)
        self.assertEqual(mock_plan.call_count, 4)
        self.assertEqual(mock_run_claude.call_count, 1)
        self.mock_git.commit.assert_called_once()

    @mock.patch("automation.claude_runner.run_claude")
    @mock.patch("automation.validator.run_validation")
    @mock.patch("automation.openai_client.review_change")
    @mock.patch("automation.openai_client.plan_next_task")
    @mock.patch("automation.openai_client.create_client")
    @mock.patch("automation.context_loader.build_reviewer_context", return_value="评审上下文")
    @mock.patch("automation.context_loader.build_planner_context", return_value="上下文")
    def test_candidate_loop_and_attempt_counter_are_independent(
        self, _ctx1, _ctx2, _create_client, mock_plan, mock_review, mock_validate, mock_run_claude,
    ):
        # Candidate Loop 用了 3 次 Planner 调用才选中候选（2 次拒绝 + 1 次通过），
        # 而选中后的开发阶段只需要 2 次 Attempt（Validation 先失败一次再修复通过），
        # 两个计数彼此独立、互不干扰、不会被合并或错记。
        low1 = _fake_scored_task("Privacy 页面增加打印按钮", value_user=2, value_product=2)
        low2 = _fake_scored_task("Documents 页面调整间距", value_user=1, value_product=1)
        high3 = _fake_scored_task("新增本地全文搜索功能", value_user=9, value_product=8)
        mock_plan.side_effect = [
            _plan_result_for(low1), _plan_result_for(low2), _plan_result_for(high3),
            _plan_result_for(_fake_task(risk_level="DONE")),
        ]
        mock_run_claude.return_value = _fake_claude_result()
        failed_build = (
            [CommandResult(command="npm run build", cwd="web", exit_code=1, stdout="", stderr="类型错误",
                            duration_seconds=1.0, timed_out=False)],
            False,
        )
        mock_validate.side_effect = [failed_build, ([], True)]
        mock_review.return_value = _fake_review_result(verdict="PASS", safe_to_commit=True)
        self.mock_git.get_diff.side_effect = (f"diff-{i}" for i in itertools.count(1))

        exit_code = orchestrator.main([])

        self.assertEqual(exit_code, orchestrator.EXIT_SUCCESS)
        # Candidate Loop 用了 3 次 Planner 调用选中 Task #1 的候选，第 4 次是
        # Task #2 的 Candidate 1（返回 DONE 结束循环）；开发阶段只用了 2 次
        # Attempt——两个计数不同（4 vs 2），证明彼此独立、不会被合并计数。
        self.assertEqual(mock_plan.call_count, 4)
        self.assertEqual(mock_run_claude.call_count, 2)  # 开发 Attempt：2 次
        self.mock_git.commit.assert_called_once()

    @mock.patch("automation.claude_runner.run_claude")
    @mock.patch("automation.validator.run_validation")
    @mock.patch("automation.openai_client.review_change")
    @mock.patch("automation.openai_client.plan_next_task")
    @mock.patch("automation.openai_client.create_client")
    @mock.patch("automation.context_loader.build_reviewer_context", return_value="评审上下文")
    @mock.patch("automation.context_loader.build_planner_context", return_value="上下文")
    def test_report_contains_each_candidate_score_and_reason(
        self, _ctx1, _ctx2, _create_client, mock_plan, mock_review, mock_validate, mock_run_claude,
    ):
        low = _fake_scored_task("Privacy 页面增加打印按钮", value_user=2, value_product=2)
        high = _fake_scored_task("新增本地全文搜索功能", value_user=9, value_product=8)
        mock_plan.side_effect = [_plan_result_for(low), _plan_result_for(high)]
        mock_run_claude.return_value = _fake_claude_result()
        mock_validate.return_value = ([], True)
        mock_review.return_value = _fake_review_result(verdict="PASS", safe_to_commit=True)

        orchestrator.main(["--dry-run"])

        run_dirs = list((self.tmp_path / "runtime").iterdir())
        self.assertEqual(len(run_dirs), 1)
        report_data = json.loads((run_dirs[0] / "run_report.json").read_text(encoding="utf-8"))
        evaluations = report_data["candidate_evaluations"]
        self.assertEqual(len(evaluations), 2)
        self.assertEqual(evaluations[0]["title"], "Privacy 页面增加打印按钮")
        self.assertEqual(evaluations[0]["score"], 4)
        self.assertFalse(evaluations[0]["passed"])
        self.assertTrue(evaluations[0]["reasons"])
        self.assertEqual(evaluations[1]["title"], "新增本地全文搜索功能")
        self.assertEqual(evaluations[1]["score"], 17)
        self.assertTrue(evaluations[1]["passed"])


if __name__ == "__main__":
    unittest.main()
