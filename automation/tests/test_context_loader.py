"""context_loader.py 单元测试：SOT 下一步计划提取、Auto Dev 进度台账接入。

不读写项目真实文件：LAWGUARD_SOT.md / AUTODEV_PROGRESS.md 相关路径均重定向到
临时目录。
"""
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from automation import context_loader, progress
from automation import config as cfg


class TestReadSotNextSteps(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.sot_path = Path(self._tmp.name) / "LAWGUARD_SOT.md"
        self._patch = mock.patch.object(cfg, "SOT_FILE", self.sot_path)
        self._patch.start()
        self.addCleanup(self._patch.stop)

    def test_extracts_bullet_items_under_next_steps_section(self):
        self.sot_path.write_text(
            "## 17. 当前开发进度\n- [x] 已完成项\n\n"
            "## 18. 下一步计划\n- 候选任务 A\n- 候选任务 B\n\n"
            "## 19. 其它章节\n- 不应被提取\n",
            encoding="utf-8",
        )
        items = context_loader.read_sot_next_steps()
        self.assertEqual(items, ["候选任务 A", "候选任务 B"])

    def test_returns_empty_list_when_file_missing(self):
        items = context_loader.read_sot_next_steps()
        self.assertEqual(items, [])


class TestBuildPlannerContextIncludesProgress(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        tmp_path = Path(self._tmp.name)
        self.progress_path = tmp_path / "AUTODEV_PROGRESS.md"
        self.sot_path = tmp_path / "LAWGUARD_SOT.md"
        self.claude_md_path = tmp_path / "CLAUDE.md"
        self.sot_path.write_text("## 18. 下一步计划\n- 候选任务\n", encoding="utf-8")
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
            self.progress_path, task_number=1, task_title="已完成任务", commit_hash="abc1234",
            now_iso="2026-07-26T00:00:00", next_candidate_tasks=["候选任务"],
        )

        context_text = context_loader.build_planner_context()

        self.assertIn("Auto Dev 进度台账", context_text)
        self.assertIn("task-001: 已完成任务", context_text)
        self.assertIn("禁止重复规划", context_text)

    def test_creates_progress_file_on_first_call_when_absent(self):
        self.assertFalse(self.progress_path.exists())
        context_loader.build_planner_context()
        self.assertTrue(self.progress_path.exists())


if __name__ == "__main__":
    unittest.main()
