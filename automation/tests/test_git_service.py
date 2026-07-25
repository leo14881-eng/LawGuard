"""git_service.py 单元测试：提交信息格式校验、禁止文件冲突检测、受限提交流程。"""
import unittest
from unittest import mock

from automation.git_service import GitError, GitService


class TestCommitMessageValidation(unittest.TestCase):
    def test_valid_conventional_commit(self):
        self.assertTrue(GitService.validate_commit_message("feat: 增加阶段权利详情页"))
        self.assertTrue(GitService.validate_commit_message("fix: 修复移动端导航显示问题"))

    def test_accepts_autodev_prefix(self):
        self.assertTrue(GitService.validate_commit_message("AutoDev(task-001): 增加阶段权利详情页"))
        self.assertTrue(GitService.validate_commit_message("AutoDev(task-042): 修复移动端导航显示问题"))

    def test_rejects_empty_message(self):
        self.assertFalse(GitService.validate_commit_message(""))
        self.assertFalse(GitService.validate_commit_message("   "))

    def test_rejects_non_conventional_format(self):
        self.assertFalse(GitService.validate_commit_message("随便改了一些东西"))
        self.assertFalse(GitService.validate_commit_message("update stuff"))

    def test_rejects_unknown_type(self):
        self.assertFalse(GitService.validate_commit_message("hack: 破坏系统"))

    def test_rejects_overlong_first_line(self):
        long_msg = "feat: " + "很长的描述" * 20
        self.assertFalse(GitService.validate_commit_message(long_msg))


class TestForbiddenFileDetection(unittest.TestCase):
    def test_detects_violation_in_changed_files(self):
        service = GitService.__new__(GitService)
        service.get_changed_files = lambda: ["LAWGUARD_SOT.md", "web/src/data/stages.ts"]
        violations = service.find_forbidden_violations(["LAWGUARD_SOT.md"])
        self.assertEqual(violations, ["LAWGUARD_SOT.md"])

    def test_no_violation_when_files_outside_forbidden_scope(self):
        service = GitService.__new__(GitService)
        service.get_changed_files = lambda: ["web/src/data/stages.ts"]
        violations = service.find_forbidden_violations(["LAWGUARD_SOT.md"])
        self.assertEqual(violations, [])


class TestSafeCommit(unittest.TestCase):
    def _service_with_mocked_run(self):
        service = GitService.__new__(GitService)
        service.project_root = "D:/SOFT/LawGuard"
        return service

    def test_commit_rejects_runtime_and_reports_paths(self):
        service = self._service_with_mocked_run()
        service._run = mock.Mock(side_effect=AssertionError("不应调用真实 git 命令"))
        with self.assertRaises(GitError):
            service.commit(["automation/runtime/leak.json"], "feat: 测试")
        with self.assertRaises(GitError):
            service.commit(["automation/reports/leak.md"], "feat: 测试")
        service._run.assert_not_called()

    def test_commit_rejects_env_local(self):
        service = self._service_with_mocked_run()
        service._run = mock.Mock(side_effect=AssertionError("不应调用真实 git 命令"))
        with self.assertRaises(GitError):
            service.commit([".env.local"], "feat: 测试")
        service._run.assert_not_called()

    def test_commit_rejects_lawguard_sot(self):
        # 双重保险：即便 Planner/Claude 出于任何原因把 LAWGUARD_SOT.md 放进了
        # 待提交文件列表，Auto Commit 也必须在这一层拒绝，保证该文件在自动开发
        # 过程中始终不被修改。
        service = self._service_with_mocked_run()
        service._run = mock.Mock(side_effect=AssertionError("不应调用真实 git 命令"))
        with self.assertRaises(GitError):
            service.commit(["LAWGUARD_SOT.md"], "feat: 测试")
        service._run.assert_not_called()

    def test_commit_rejects_invalid_message_without_running_git(self):
        service = self._service_with_mocked_run()
        service._run = mock.Mock(side_effect=AssertionError("不应调用真实 git 命令"))
        with self.assertRaises(GitError):
            service.commit(["web/src/data/stages.ts"], "随便写的提交信息")
        service._run.assert_not_called()

    def test_commit_uses_explicit_file_list_not_add_all(self):
        service = self._service_with_mocked_run()
        calls = []

        def fake_run(args, timeout=60):
            calls.append(args)
            result = mock.Mock()
            result.returncode = 0
            result.stdout = "abc1234\n"
            result.stderr = ""
            return result

        service._run = fake_run
        service.commit(["web/src/data/stages.ts"], "feat: 测试提交")

        add_call = next(c for c in calls if c[0] == "add")
        self.assertEqual(add_call, ["add", "--", "web/src/data/stages.ts"])
        self.assertNotIn(".", add_call)
        self.assertNotIn("-A", add_call)


if __name__ == "__main__":
    unittest.main()
