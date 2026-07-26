"""automation/backlog.py 单元测试：Product Backlog 结构、优先级排序、ID 校验。"""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from automation import backlog


class TestBacklogStructure(unittest.TestCase):
    def test_all_backlog_ids_unique(self):
        ids = [item.backlog_id for item in backlog.BACKLOG]
        self.assertEqual(len(ids), len(set(ids)))

    def test_all_statuses_are_known(self):
        for item in backlog.BACKLOG:
            self.assertIn(item.status, backlog.BACKLOG_STATUSES, item.backlog_id)

    def test_blocked_items_do_not_allow_auto_dev(self):
        # BL-006/BL-007 因缺少可核验法律来源被标记 BLOCKED，不得允许 Auto Dev 自动推进。
        for item in backlog.BACKLOG:
            if item.status == "BLOCKED":
                self.assertFalse(item.allow_auto_dev, item.backlog_id)


class _IsolatedRuntimeDirTestCase(unittest.TestCase):
    """使用隔离的空临时 runtime 目录，不触碰真实 automation/runtime/。

    真实仓库的 automation/runtime/ 目前包含 Task #14/#15 完成 BL-001 的真实
    执行证据（见 get_completed_backlog_ids），如果测试省略 runtime_dir 参数、
    依赖模块默认值，就会读到这份真实数据，导致测试结果随仓库实际执行历史
    浮动——这正是本次要修复的"已完成条目判定"要读真实证据，但测试本身必须
    在隔离环境下保持确定性，两者不矛盾。
    """

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp(prefix="backlog-test-"))
        self.addCleanup(shutil.rmtree, self.tmp_dir, ignore_errors=True)


class TestGetReadyItems(_IsolatedRuntimeDirTestCase):
    def test_ready_items_sorted_by_priority_then_id(self):
        ready = backlog.get_ready_items(self.tmp_dir)
        priorities = [backlog.PRIORITY_ORDER[item.priority] for item in ready]
        self.assertEqual(priorities, sorted(priorities))

    def test_ready_items_all_allow_auto_dev(self):
        for item in backlog.get_ready_items(self.tmp_dir):
            self.assertTrue(item.allow_auto_dev)
            self.assertEqual(item.status, "READY")

    def test_has_ready_item_true_for_real_backlog(self):
        # 空 runtime 目录（无任何完成证据）时，真实 Backlog（BL-001~BL-005）
        # 应全部保持 READY，这是本次修复的前提：Backlog 不能是空的。
        self.assertTrue(backlog.has_ready_item(self.tmp_dir))

    def test_deferred_and_blocked_items_excluded_from_ready(self):
        ready_ids = {item.backlog_id for item in backlog.get_ready_items(self.tmp_dir)}
        self.assertNotIn("BL-006", ready_ids)  # BLOCKED
        self.assertNotIn("BL-007", ready_ids)  # BLOCKED
        self.assertNotIn("BL-008", ready_ids)  # DEFERRED

    def test_all_ready_items_present_when_nothing_completed(self):
        ready_ids = {item.backlog_id for item in backlog.get_ready_items(self.tmp_dir)}
        self.assertEqual(ready_ids, {"BL-001", "BL-002", "BL-003", "BL-004", "BL-005"})


class TestCompletedBacklogFiltering(_IsolatedRuntimeDirTestCase):
    """本次修复核心：已通过真实执行记录证明完成的 Backlog 条目，不应再出现
    在 get_ready_items() 返回的 READY 列表中（对应真实复现的 Task #16 问题：
    BL-001 已由 Task #14/#15 完成并提交，却仍被 Planner 当作 READY 候选）。
    """

    def _write_committed_run(self, run_id: str, backlog_id: str) -> None:
        run_dir = self.tmp_dir / run_id
        run_dir.mkdir(parents=True)
        report = {
            "final_status": "COMMITTED",
            "task": {"backlog_id": backlog_id, "title": "测试任务"},
        }
        (run_dir / "run_report.json").write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")

    def test_completed_top_level_item_excluded_from_ready(self):
        # 对应真实场景：BL-001 没有拆分切片，Task #14/#15 都直接引用
        # backlog_id="BL-001" 且 final_status=COMMITTED。
        self._write_committed_run("20260726_141118_a", "BL-001")
        self._write_committed_run("20260726_141742_b", "BL-001")

        ready_ids = {item.backlog_id for item in backlog.get_ready_items(self.tmp_dir)}
        self.assertNotIn("BL-001", ready_ids)
        self.assertEqual(ready_ids, {"BL-002", "BL-003", "BL-004", "BL-005"})

    def test_non_committed_run_does_not_count_as_completed(self):
        # final_status 不是 COMMITTED（如 VALIDATION_FAILED）不构成完成证据，
        # 不能仅凭"任务提到过这个 backlog_id"就当作已完成——不允许猜测。
        run_dir = self.tmp_dir / "20260726_150000_x"
        run_dir.mkdir(parents=True)
        report = {"final_status": "VALIDATION_FAILED", "task": {"backlog_id": "BL-001"}}
        (run_dir / "run_report.json").write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")

        ready_ids = {item.backlog_id for item in backlog.get_ready_items(self.tmp_dir)}
        self.assertIn("BL-001", ready_ids)

    def test_partially_completed_sliced_item_stays_in_ready(self):
        # BL-003 拆分为 4 个切片，只完成 BL-003-1 时，条目本身仍应留在 READY
        # 列表里，供 Planner 挑选下一个尚未完成的切片。
        self._write_committed_run("20260726_150100_a", "BL-003-1")

        ready_ids = {item.backlog_id for item in backlog.get_ready_items(self.tmp_dir)}
        self.assertIn("BL-003", ready_ids)

    def test_fully_completed_sliced_item_excluded_from_ready(self):
        for i, slice_id in enumerate(["BL-003-1", "BL-003-2", "BL-003-3", "BL-003-4"]):
            self._write_committed_run(f"20260726_15020{i}_x", slice_id)

        ready_ids = {item.backlog_id for item in backlog.get_ready_items(self.tmp_dir)}
        self.assertNotIn("BL-003", ready_ids)

    def test_missing_runtime_dir_does_not_guess_keeps_items_ready(self):
        # 目录不存在时（例如全新仓库、从未跑过 Auto Dev）不允许猜测任何条目已
        # 完成，必须保守地保持全部 READY 条目可见。
        missing_dir = self.tmp_dir / "does-not-exist"
        ready_ids = {item.backlog_id for item in backlog.get_ready_items(missing_dir)}
        self.assertEqual(ready_ids, {"BL-001", "BL-002", "BL-003", "BL-004", "BL-005"})

    def test_malformed_run_report_is_skipped_not_crashing(self):
        run_dir = self.tmp_dir / "20260726_150300_bad"
        run_dir.mkdir(parents=True)
        (run_dir / "run_report.json").write_text("{not valid json", encoding="utf-8")

        ready_ids = {item.backlog_id for item in backlog.get_ready_items(self.tmp_dir)}
        self.assertIn("BL-001", ready_ids)

    def test_get_completed_backlog_ids_returns_evidence_set(self):
        self._write_committed_run("20260726_150400_a", "BL-001")
        self._write_committed_run("20260726_150401_b", "BL-002")

        completed = backlog.get_completed_backlog_ids(self.tmp_dir)
        self.assertEqual(completed, {"BL-001", "BL-002"})


class TestBacklogReferenceValidation(unittest.TestCase):
    def test_top_level_id_is_valid_reference(self):
        self.assertTrue(backlog.is_valid_reference("BL-003"))

    def test_slice_id_is_valid_reference(self):
        self.assertTrue(backlog.is_valid_reference("BL-003-1"))

    def test_unknown_id_is_invalid_reference(self):
        self.assertFalse(backlog.is_valid_reference("BL-999"))

    def test_empty_string_is_invalid_reference(self):
        self.assertFalse(backlog.is_valid_reference(""))

    def test_get_item_returns_none_for_unknown_id(self):
        self.assertIsNone(backlog.get_item("BL-999"))

    def test_get_item_returns_item_for_known_id(self):
        item = backlog.get_item("BL-001")
        self.assertIsNotNone(item)
        self.assertEqual(item.title, "交互式个人处境导航工具")


class TestLargeBacklogItemsHaveMeaningfulSlices(unittest.TestCase):
    """高优先级大功能必须拆成有独立业务意义的垂直切片，而不是无意义的按钮/图标/间距。"""

    def test_search_item_has_multiple_vertical_slices(self):
        item = backlog.get_item("BL-003")
        self.assertGreaterEqual(len(item.slices), 3)
        slice_titles = [s.title for s in item.slices]
        for forbidden in ("按钮", "图标", "间距", "aria-label"):
            for title in slice_titles:
                self.assertNotIn(forbidden, title)

    def test_offline_item_has_multiple_vertical_slices(self):
        item = backlog.get_item("BL-005")
        self.assertGreaterEqual(len(item.slices), 3)


class TestBuildPlannerBacklogContext(_IsolatedRuntimeDirTestCase):
    def _write_committed_run(self, run_id: str, backlog_id: str) -> None:
        run_dir = self.tmp_dir / run_id
        run_dir.mkdir(parents=True)
        report = {"final_status": "COMMITTED", "task": {"backlog_id": backlog_id, "title": "测试任务"}}
        (run_dir / "run_report.json").write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")

    def test_context_lists_ready_items_first(self):
        text = backlog.build_planner_backlog_context(self.tmp_dir)
        self.assertIn("READY", text)
        self.assertIn("BL-001", text)
        self.assertIn("不得返回 risk_level=NO_HIGH_VALUE_TASK", text)

    def test_context_marks_blocked_items_as_reference_only(self):
        text = backlog.build_planner_backlog_context(self.tmp_dir)
        self.assertIn("非 READY，仅供参考，不得选择", text)
        self.assertIn("BL-006", text)

    def test_completed_item_moves_to_reference_only_section_with_clear_label(self):
        # 对应真实场景：BL-001 已完成后，Planner 上下文里不应再把它列在 READY，
        # 而应在"其它条目"里明确标注"已完成"，不能让原始 READY 标签误导 Planner。
        self._write_committed_run("20260726_141118_a", "BL-001")
        self._write_committed_run("20260726_141742_b", "BL-001")

        text = backlog.build_planner_backlog_context(self.tmp_dir)
        self.assertIn("当前 READY（按优先级排序，必须优先从此列表选择）", text)
        ready_section = text.split("其它条目")[0]
        self.assertNotIn("BL-001", ready_section)
        self.assertIn("BL-001", text)
        self.assertIn("已完成（有真实执行记录，不得再次选择）", text)


if __name__ == "__main__":
    unittest.main()
