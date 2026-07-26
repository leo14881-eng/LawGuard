"""automation/backlog.py 单元测试：Product Backlog 结构、优先级排序、ID 校验。"""
from __future__ import annotations

import unittest

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


class TestGetReadyItems(unittest.TestCase):
    def test_ready_items_sorted_by_priority_then_id(self):
        ready = backlog.get_ready_items()
        priorities = [backlog.PRIORITY_ORDER[item.priority] for item in ready]
        self.assertEqual(priorities, sorted(priorities))

    def test_ready_items_all_allow_auto_dev(self):
        for item in backlog.get_ready_items():
            self.assertTrue(item.allow_auto_dev)
            self.assertEqual(item.status, "READY")

    def test_has_ready_item_true_for_real_backlog(self):
        # 真实 Backlog（BL-001~BL-005）当前应存在 READY 条目，这是本次修复
        # Task #14 问题的前提：Backlog 不能是空的。
        self.assertTrue(backlog.has_ready_item())

    def test_deferred_and_blocked_items_excluded_from_ready(self):
        ready_ids = {item.backlog_id for item in backlog.get_ready_items()}
        self.assertNotIn("BL-006", ready_ids)  # BLOCKED
        self.assertNotIn("BL-007", ready_ids)  # BLOCKED
        self.assertNotIn("BL-008", ready_ids)  # DEFERRED


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


class TestBuildPlannerBacklogContext(unittest.TestCase):
    def test_context_lists_ready_items_first(self):
        text = backlog.build_planner_backlog_context()
        self.assertIn("READY", text)
        self.assertIn("BL-001", text)
        self.assertIn("不得返回 risk_level=NO_HIGH_VALUE_TASK", text)

    def test_context_marks_blocked_items_as_reference_only(self):
        text = backlog.build_planner_backlog_context()
        self.assertIn("非 READY，仅供参考，不得选择", text)
        self.assertIn("BL-006", text)


if __name__ == "__main__":
    unittest.main()
