"""orchestrator.py 单元测试：命令行参数解析与自动提交判定逻辑。"""
import unittest

from automation.git_service import GitService
from automation.orchestrator import build_autodev_commit_message, parse_args, should_auto_commit


class TestParseArgs(unittest.TestCase):
    def test_default_flags_are_false(self):
        args = parse_args([])
        self.assertFalse(args.dry_run)
        self.assertFalse(args.no_commit)
        self.assertFalse(args.allow_dirty)
        self.assertIsNone(args.model)

    def test_allow_dirty_flag_parsed(self):
        args = parse_args(["--allow-dirty"])
        self.assertTrue(args.allow_dirty)

    def test_model_override_parsed(self):
        args = parse_args(["--model", "gpt-test"])
        self.assertEqual(args.model, "gpt-test")


class TestShouldAutoCommit(unittest.TestCase):
    def test_commits_when_all_conditions_met(self):
        result = should_auto_commit(
            safe_to_commit=True, auto_commit_enabled=True, no_commit_flag=False, allow_dirty_flag=False
        )
        self.assertTrue(result)

    def test_allow_dirty_always_blocks_commit(self):
        result = should_auto_commit(
            safe_to_commit=True, auto_commit_enabled=True, no_commit_flag=False, allow_dirty_flag=True
        )
        self.assertFalse(result)

    def test_no_commit_flag_blocks_commit(self):
        result = should_auto_commit(
            safe_to_commit=True, auto_commit_enabled=True, no_commit_flag=True, allow_dirty_flag=False
        )
        self.assertFalse(result)

    def test_auto_commit_disabled_blocks_commit(self):
        result = should_auto_commit(
            safe_to_commit=True, auto_commit_enabled=False, no_commit_flag=False, allow_dirty_flag=False
        )
        self.assertFalse(result)

    def test_review_not_safe_blocks_commit(self):
        result = should_auto_commit(
            safe_to_commit=False, auto_commit_enabled=True, no_commit_flag=False, allow_dirty_flag=False
        )
        self.assertFalse(result)


class TestBuildAutodevCommitMessage(unittest.TestCase):
    def test_formats_task_number_with_zero_padding(self):
        message = build_autodev_commit_message(1, "feat: 增加阶段权利详情页")
        self.assertEqual(message, "AutoDev(task-001): feat: 增加阶段权利详情页")

    def test_task_number_increments_across_calls(self):
        self.assertTrue(build_autodev_commit_message(2, "说明").startswith("AutoDev(task-002): "))
        self.assertTrue(build_autodev_commit_message(42, "说明").startswith("AutoDev(task-042): "))

    def test_falls_back_when_base_message_empty(self):
        message = build_autodev_commit_message(1, "")
        self.assertEqual(message, "AutoDev(task-001): 自动开发任务已完成")

    def test_truncates_overlong_description_to_stay_valid(self):
        message = build_autodev_commit_message(1, "很长的描述" * 30)
        self.assertLessEqual(len(message.splitlines()[0]), 80)
        self.assertTrue(GitService.validate_commit_message(message))

    def test_output_passes_git_service_validation(self):
        message = build_autodev_commit_message(3, "fix: 修复移动端导航显示问题")
        self.assertTrue(GitService.validate_commit_message(message))


if __name__ == "__main__":
    unittest.main()
