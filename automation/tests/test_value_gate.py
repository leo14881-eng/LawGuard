"""automation/value_gate.py 单元测试：ValueScore 计算、重复任务检测、Stop Rule。"""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from automation import value_gate
from automation.models import DevelopmentTask


def _make_task(**overrides) -> DevelopmentTask:
    defaults = dict(
        task_id="T-001", title="示例任务", objective="示例目标", rationale="示例理由",
        scope="", acceptance_criteria=[], files_allowed=["web/src/x.ts"],
        files_forbidden=["LAWGUARD_SOT.md"], validation_commands=["npm run build"],
        risk_level="LOW", requires_sot_update=False, developer_prompt="",
        task_category="产品能力提升",
        value_user=0, value_product=0, value_legal=0, value_tech_debt=0,
        repetition_penalty=0, maintenance_cost=0,
        why_valuable="", why_not_other_candidates="", why_not_duplicate="", expected_user_benefit="",
    )
    defaults.update(overrides)
    return DevelopmentTask(**defaults)


def _history_entry(title: str, objective: str = "", risk_level: str = "LOW", **value_fields) -> dict:
    entry = {"title": title, "objective": objective, "risk_level": risk_level}
    entry.update(value_fields)
    return entry


class TestComputeValueScore(unittest.TestCase):
    def test_formula(self):
        task = _make_task(value_user=10, value_product=10, value_legal=5, value_tech_debt=5, repetition_penalty=3, maintenance_cost=2)
        self.assertEqual(value_gate.compute_value_score(task), 10 + 10 + 5 + 5 - 3 - 2)

    def test_negative_score_allowed(self):
        task = _make_task(value_user=0, value_product=0, value_legal=0, value_tech_debt=0, repetition_penalty=10, maintenance_cost=5)
        self.assertEqual(value_gate.compute_value_score(task), -15)


class TestClassifyRepetitiveCategory(unittest.TestCase):
    def test_print_button_detected_chinese(self):
        self.assertEqual(value_gate.classify_repetitive_category("Privacy 页面新增打印本页入口"), "PrintButton")

    def test_print_button_detected_english(self):
        self.assertEqual(value_gate.classify_repetitive_category("Add PrintPageButton to Privacy page"), "PrintButton")

    def test_aria_label_detected(self):
        self.assertEqual(value_gate.classify_repetitive_category("为组件增加 aria-label 属性"), "aria-label")

    def test_unrelated_task_not_classified(self):
        self.assertIsNone(value_gate.classify_repetitive_category("新增案件阶段时间线交互工具"))


class TestGateDecisionScoreThreshold(unittest.TestCase):
    def test_high_score_passes(self):
        task = _make_task(
            title="新增案件阶段时间线工具", objective="家属输入关键日期，本地计算大致所处阶段",
            value_user=8, value_product=8, value_legal=0, value_tech_debt=0,
            repetition_penalty=0, maintenance_cost=1,
        )
        decision = value_gate.evaluate_task(task, history=[])
        self.assertEqual(decision.score, 15)  # 8+8+0+0-0-1=15，恰好达到门槛
        self.assertTrue(decision.passed)

    def test_score_below_threshold_rejected(self):
        task = _make_task(value_user=3, value_product=3, value_legal=0, value_tech_debt=0, repetition_penalty=0, maintenance_cost=0)
        decision = value_gate.evaluate_task(task, history=[])
        self.assertEqual(decision.score, 6)
        self.assertFalse(decision.passed)

    def test_score_exactly_at_threshold_passes(self):
        task = _make_task(value_user=10, value_product=5, value_legal=0, value_tech_debt=0, repetition_penalty=0, maintenance_cost=0)
        decision = value_gate.evaluate_task(task, history=[])
        self.assertEqual(decision.score, 15)
        self.assertTrue(decision.passed)

    def test_done_task_bypasses_gate(self):
        task = _make_task(risk_level="DONE")
        decision = value_gate.evaluate_task(task, history=[])
        self.assertTrue(decision.passed)

    def test_blocked_task_bypasses_gate(self):
        task = _make_task(risk_level="BLOCKED")
        decision = value_gate.evaluate_task(task, history=[])
        self.assertTrue(decision.passed)


class TestRepetitionHardBlock(unittest.TestCase):
    def test_third_repetition_rejected_even_with_high_score(self):
        history = [
            _history_entry("Official Channels 新增打印按钮"),
            _history_entry("Stages 新增打印按钮"),
            _history_entry("Privacy 新增打印按钮"),
        ]
        task = _make_task(
            title="Documents 页面新增打印本页入口",
            value_user=10, value_product=10, value_legal=0, value_tech_debt=0,
            repetition_penalty=0, maintenance_cost=0,  # 故意让 Planner"漏报"重复惩罚
        )
        decision = value_gate.evaluate_task(task, history)
        self.assertFalse(decision.passed)
        self.assertEqual(decision.repetitive_category, "PrintButton")
        self.assertGreaterEqual(decision.repetitive_count, 3)

    def test_first_and_second_occurrence_not_hard_blocked(self):
        history = [_history_entry("Official Channels 新增打印按钮")]
        task = _make_task(
            title="Stages 新增打印按钮",
            value_user=10, value_product=10, value_legal=0, value_tech_debt=0,
            repetition_penalty=0, maintenance_cost=0,
        )
        decision = value_gate.evaluate_task(task, history)
        # 尚未达到 3 次上限，不触发硬性拦截；分数本身足够高，应该放行
        self.assertTrue(decision.passed)

    def test_severe_defect_overrides_repetition_block(self):
        history = [
            _history_entry("Official Channels 新增打印按钮"),
            _history_entry("Stages 新增打印按钮"),
            _history_entry("Privacy 新增打印按钮"),
        ]
        task = _make_task(
            title="修复 Documents 页面打印按钮的严重缺陷",
            rationale="打印按钮点击后页面完全失效，属于严重缺陷，需要立即修复",
            value_user=8, value_product=7, value_legal=0, value_tech_debt=0,
            repetition_penalty=0, maintenance_cost=0,
        )
        decision = value_gate.evaluate_task(task, history)
        self.assertTrue(decision.passed)


class TestLoadRecentTasksAndHistoryScan(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="value-gate-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def _write_run(self, run_id: str, task_dict: dict) -> None:
        run_dir = self.tmp / run_id
        run_dir.mkdir(parents=True)
        (run_dir / "task.json").write_text(json.dumps(task_dict, ensure_ascii=False), encoding="utf-8")

    def test_load_recent_tasks_sorted_and_limited(self):
        self._write_run("20260101_000000_aaa", {"title": "老任务"})
        self._write_run("20260102_000000_bbb", {"title": "中任务"})
        self._write_run("20260103_000000_ccc", {"title": "新任务"})
        history = value_gate.load_recent_tasks(self.tmp, limit=2)
        self.assertEqual([h["title"] for h in history], ["新任务", "中任务"])

    def test_load_recent_tasks_skips_corrupted_entries(self):
        run_dir = self.tmp / "20260101_000000_bad"
        run_dir.mkdir(parents=True)
        (run_dir / "task.json").write_text("{not valid json", encoding="utf-8")
        self._write_run("20260102_000000_ok", {"title": "正常任务"})
        history = value_gate.load_recent_tasks(self.tmp, limit=10)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["title"], "正常任务")

    def test_load_recent_tasks_empty_dir(self):
        self.assertEqual(value_gate.load_recent_tasks(self.tmp), [])

    def test_load_recent_tasks_missing_dir(self):
        self.assertEqual(value_gate.load_recent_tasks(self.tmp / "does-not-exist"), [])


class TestStopRule(unittest.TestCase):
    def _scored_entry(self, score_total_inputs: tuple[int, int, int, int, int, int]) -> dict:
        user, product, legal, tech_debt, rep_penalty, maint = score_total_inputs
        return {
            "risk_level": "LOW",
            "value_user": user, "value_product": product, "value_legal": legal,
            "value_tech_debt": tech_debt, "repetition_penalty": rep_penalty, "maintenance_cost": maint,
            "task_category": "产品能力提升", "title": "t", "objective": "o", "rationale": "r",
            "scope": "", "acceptance_criteria": [], "files_allowed": [], "files_forbidden": [],
            "validation_commands": [], "requires_sot_update": False, "developer_prompt": "",
            "task_id": "t", "why_valuable": "", "why_not_other_candidates": "",
            "why_not_duplicate": "", "expected_user_benefit": "",
        }

    def test_low_average_triggers_stop(self):
        # 20 个任务，每个 ValueScore 都是 2 + 2 + 0 + 0 - 0 - 0 = 4，平均远低于 8
        history = [self._scored_entry((2, 2, 0, 0, 0, 0)) for _ in range(20)]
        should_stop, avg, count = value_gate.should_stop_auto_dev(history)
        self.assertTrue(should_stop)
        self.assertEqual(count, 20)
        self.assertAlmostEqual(avg, 4.0)

    def test_high_average_does_not_stop(self):
        history = [self._scored_entry((10, 10, 0, 5, 0, 0)) for _ in range(20)]
        should_stop, avg, count = value_gate.should_stop_auto_dev(history)
        self.assertFalse(should_stop)
        self.assertAlmostEqual(avg, 25.0)

    def test_legacy_entries_without_value_fields_are_excluded(self):
        # 升级前生成的旧 task.json 没有 value_user 等字段，不应被计入平均分统计
        legacy = [{"title": "旧任务", "risk_level": "LOW"} for _ in range(20)]
        should_stop, avg, count = value_gate.should_stop_auto_dev(legacy)
        self.assertFalse(should_stop)
        self.assertIsNone(avg)
        self.assertEqual(count, 0)

    def test_done_and_blocked_entries_excluded_from_average(self):
        scored = [self._scored_entry((10, 10, 0, 5, 0, 0)) for _ in range(5)]
        done_entries = [{"title": "done", "risk_level": "DONE"} for _ in range(15)]
        should_stop, avg, count = value_gate.should_stop_auto_dev(scored + done_entries)
        self.assertEqual(count, 5)
        self.assertAlmostEqual(avg, 25.0)
        self.assertFalse(should_stop)

    def test_fewer_than_window_tasks_still_computes_average(self):
        history = [self._scored_entry((1, 1, 0, 0, 0, 0)) for _ in range(3)]
        should_stop, avg, count = value_gate.should_stop_auto_dev(history)
        self.assertEqual(count, 3)
        self.assertAlmostEqual(avg, 2.0)
        self.assertTrue(should_stop)


class TestValidateValueFields(unittest.TestCase):
    def test_valid_low_risk_task_passes(self):
        task = _make_task(
            value_user=8, value_product=8, value_legal=0, value_tech_debt=0,
            repetition_penalty=0, maintenance_cost=0,
            why_valuable="有价值", why_not_other_candidates="无其它候选",
            why_not_duplicate="非重复", expected_user_benefit="明显收益",
        )
        self.assertEqual(value_gate.validate_value_fields(task), [])

    def test_invalid_category_detected(self):
        task = _make_task(task_category="不存在的分类", why_valuable="x", why_not_other_candidates="x", why_not_duplicate="x", expected_user_benefit="x")
        issues = value_gate.validate_value_fields(task)
        self.assertTrue(any("task_category" in i for i in issues))

    def test_out_of_range_value_detected(self):
        task = _make_task(value_user=99, why_valuable="x", why_not_other_candidates="x", why_not_duplicate="x", expected_user_benefit="x")
        issues = value_gate.validate_value_fields(task)
        self.assertTrue(any("value_user" in i for i in issues))

    def test_empty_reasoning_field_detected(self):
        task = _make_task(why_valuable="", why_not_other_candidates="x", why_not_duplicate="x", expected_user_benefit="x")
        issues = value_gate.validate_value_fields(task)
        self.assertTrue(any("why_valuable" in i for i in issues))

    def test_done_task_skips_business_validation(self):
        task = _make_task(risk_level="DONE", value_user=999, task_category="乱写")
        self.assertEqual(value_gate.validate_value_fields(task), [])


if __name__ == "__main__":
    unittest.main()
