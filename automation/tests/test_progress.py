"""progress.py 单元测试：AUTODEV_PROGRESS.md 的读写、自动创建与自动修复。"""
import tempfile
import unittest
from pathlib import Path

from automation import progress


class TestDefaultStateAndRender(unittest.TestCase):
    def test_render_then_parse_round_trip(self):
        state = progress.default_state()
        text = progress.render(state)
        parsed = progress.parse(text)
        self.assertEqual(parsed, state)

    def test_render_contains_all_required_sections(self):
        text = progress.render(progress.default_state())
        for heading in (
            "Project Stage", "Last Update", "Last Commit", "Completed Tasks",
            "Current Task", "Next Candidate Tasks", "Known Issues",
        ):
            self.assertIn(f"## {heading}", text)


class TestParseMalformedContent(unittest.TestCase):
    def test_missing_header_is_malformed(self):
        self.assertIsNone(progress.parse("## Project Stage\n内容\n"))

    def test_missing_required_section_is_malformed(self):
        text = "# Auto Dev Progress\n\n## Project Stage\n开发中\n"
        self.assertIsNone(progress.parse(text))

    def test_empty_text_is_malformed(self):
        self.assertIsNone(progress.parse(""))


class TestLoadOrRepair(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name) / "docs" / "project" / "AUTODEV_PROGRESS.md"

    def test_creates_default_file_when_missing(self):
        state, was_missing, was_repaired = progress.load_or_repair(self.path)
        self.assertTrue(was_missing)
        self.assertFalse(was_repaired)
        self.assertTrue(self.path.exists())
        self.assertEqual(state.completed_tasks, [])

    def test_repairs_malformed_file(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("随便写的内容，不是合法的进度文件", encoding="utf-8")

        state, was_missing, was_repaired = progress.load_or_repair(self.path)

        self.assertFalse(was_missing)
        self.assertTrue(was_repaired)
        self.assertEqual(state.completed_tasks, [])
        # 修复后应把默认模板写回磁盘，而不是仅在内存中返回默认值。
        reloaded, was_missing2, was_repaired2 = progress.load_or_repair(self.path)
        self.assertFalse(was_missing2)
        self.assertFalse(was_repaired2)
        self.assertEqual(reloaded, state)

    def test_restores_existing_valid_state(self):
        progress.write(self.path, progress.default_state())
        state, was_missing, was_repaired = progress.load_or_repair(self.path)
        self.assertFalse(was_missing)
        self.assertFalse(was_repaired)


class TestRecordCompletedTask(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name) / "AUTODEV_PROGRESS.md"

    def test_appends_task_and_updates_last_commit(self):
        state = progress.record_completed_task(
            self.path, task_number=1, task_title="示例任务",
            commit_message="AutoDev(task-001): 示例任务",
            now_iso="2026-07-26T00:00:00", next_candidate_tasks=["候选任务 A"],
        )
        self.assertEqual(state.completed_tasks, ["task-001: 示例任务"])
        self.assertEqual(state.last_commit, "AutoDev(task-001): 示例任务")
        self.assertEqual(state.next_candidate_tasks, ["候选任务 A"])
        self.assertEqual(state.current_task, "（无，等待 Planner 规划下一任务）")

    def test_last_commit_stores_message_known_before_the_commit_exists(self):
        # commit_message 在真正执行 git commit 之前就已经确定（用于组装本次要
        # 提交的内容），因此可以在提交发生前写入进度文件；无需（也无法）预先
        # 获得提交后才产生的 Git Commit Hash。
        state = progress.record_completed_task(
            self.path, task_number=7, task_title="任意任务",
            commit_message="AutoDev(task-007): 任意任务",
            now_iso="t",
        )
        self.assertEqual(state.last_commit, "AutoDev(task-007): 任意任务")

    def test_second_call_appends_without_losing_first_entry(self):
        progress.record_completed_task(
            self.path, task_number=1, task_title="任务一", commit_message="c1",
            now_iso="t1",
        )
        state = progress.record_completed_task(
            self.path, task_number=2, task_title="任务二", commit_message="c2",
            now_iso="t2",
        )
        self.assertEqual(state.completed_tasks, ["task-001: 任务一", "task-002: 任务二"])
        self.assertEqual(state.last_commit, "c2")

    def test_next_candidate_tasks_preserved_when_not_provided(self):
        progress.record_completed_task(
            self.path, task_number=1, task_title="任务一", commit_message="c1",
            now_iso="t1", next_candidate_tasks=["候选 A"],
        )
        state = progress.record_completed_task(
            self.path, task_number=2, task_title="任务二", commit_message="c2",
            now_iso="t2",
        )
        # 未显式传入 next_candidate_tasks 时应保留原有值，而不是被清空；
        # 该字段现在完全由 AUTODEV_PROGRESS.md 自行维护，不再从
        # LAWGUARD_SOT.md 同步。
        self.assertEqual(state.next_candidate_tasks, ["候选 A"])

    def test_does_not_duplicate_completed_tasks_when_replayed(self):
        # record_completed_task 本身只负责追加，不做去重判断；
        # 由 orchestrator 保证每个任务只在成功提交后调用一次。
        progress.record_completed_task(
            self.path, task_number=1, task_title="任务一", commit_message="c1",
            now_iso="t1",
        )
        state, _, _ = progress.load_or_repair(self.path)
        self.assertEqual(state.completed_tasks, ["task-001: 任务一"])


class TestBuildPlannerContextSection(unittest.TestCase):
    def test_mentions_completed_tasks_and_forbids_duplication(self):
        state = progress.ProgressState(
            project_stage="阶段", last_update="今天", last_commit="abc123",
            completed_tasks=["task-001: 已完成的任务"], current_task="（无）",
            next_candidate_tasks=["候选 A"], known_issues=[],
        )
        section = progress.build_planner_context_section(state)
        self.assertIn("禁止重复规划", section)
        self.assertIn("task-001: 已完成的任务", section)
        self.assertIn("候选 A", section)


if __name__ == "__main__":
    unittest.main()
