"""context_loader.py 单元测试：Auto Dev 进度台账接入 Planner 上下文。

不读写项目真实文件：LAWGUARD_SOT.md / AUTODEV_PROGRESS.md 相关路径均重定向到
临时目录。
"""
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from automation import context_loader, progress
from automation import config as cfg


class TestBuildPlannerContextIncludesProgress(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        tmp_path = Path(self._tmp.name)
        self.progress_path = tmp_path / "AUTODEV_PROGRESS.md"
        self.sot_path = tmp_path / "LAWGUARD_SOT.md"
        self.claude_md_path = tmp_path / "CLAUDE.md"
        # LAWGUARD_SOT.md 只保存长期稳定事实，不再包含开发进度/下一步计划章节。
        self.sot_path.write_text("## V1 功能范围\n示例\n", encoding="utf-8")
        self.claude_md_path.write_text("## 项目状态\n示例\n", encoding="utf-8")

        patches = [
            mock.patch.object(cfg, "PROGRESS_FILE", self.progress_path),
            mock.patch.object(cfg, "SOT_FILE", self.sot_path),
            mock.patch.object(cfg, "CLAUDE_MD_FILE", self.claude_md_path),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def test_includes_progress_section_and_creates_file_when_missing(self):
        progress.record_completed_task(
            self.progress_path, task_number=1, task_title="已完成任务",
            commit_message="AutoDev(task-001): 已完成任务",
            now_iso="2026-07-26T00:00:00",
        )

        context_text = context_loader.build_planner_context()

        self.assertIn("Auto Dev 进度台账", context_text)
        self.assertIn("task-001: 已完成任务", context_text)
        self.assertIn("禁止重复规划", context_text)
        # LAWGUARD_SOT.md 本身不应出现开发进度关键词，两者职责不重叠。
        self.assertNotIn("下一步计划", self.sot_path.read_text(encoding="utf-8"))

    def test_creates_progress_file_on_first_call_when_absent(self):
        self.assertFalse(self.progress_path.exists())
        context_loader.build_planner_context()
        self.assertTrue(self.progress_path.exists())


if __name__ == "__main__":
    unittest.main()
