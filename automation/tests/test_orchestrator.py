"""orchestrator.py 单元测试：命令行参数解析与自动提交判定逻辑。"""
import unittest

from automation.orchestrator import parse_args, should_auto_commit


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


if __name__ == "__main__":
    unittest.main()
