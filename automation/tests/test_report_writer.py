"""report_writer.py 单元测试：OpenAI Token 用量小节的展示逻辑。"""
import unittest

from automation.models import TokenUsage
from automation.report_writer import _format_token_usages


class TestFormatTokenUsages(unittest.TestCase):
    def test_empty_list_shows_no_call_message(self):
        text = _format_token_usages([])
        self.assertIn("未发生 OpenAI 调用", text)

    def test_known_usage_aggregates_totals(self):
        usages = [
            TokenUsage(call_label="planner (第 1 次)", model="gpt-5-nano", prompt_tokens=100, completion_tokens=20, total_tokens=120),
            TokenUsage(call_label="reviewer", model="gpt-5-nano", prompt_tokens=200, completion_tokens=30, total_tokens=230),
        ]
        text = _format_token_usages(usages)
        self.assertIn("Prompt Tokens 300", text)
        self.assertIn("Completion Tokens 50", text)
        self.assertIn("Total Tokens 350", text)

    def test_unknown_fields_display_unknown_and_skip_aggregation(self):
        usages = [
            TokenUsage(call_label="planner (第 1 次)", model="gpt-5-nano", prompt_tokens=None, completion_tokens=None, total_tokens=None),
        ]
        text = _format_token_usages(usages)
        self.assertIn("Unknown", text)
        self.assertNotIn("Prompt Tokens 0", text)

    def test_estimated_cost_is_always_unknown(self):
        """项目内没有内置价格表，Estimated Cost 必须固定显示 Unknown，不做任何估算。"""
        usages = [
            TokenUsage(call_label="planner (第 1 次)", model="gpt-5-nano", prompt_tokens=100, completion_tokens=20, total_tokens=120),
        ]
        text_known = _format_token_usages(usages)
        text_empty = _format_token_usages([])
        self.assertIn("Estimated Cost：Unknown", text_known)
        self.assertNotIn("Estimated Cost", text_empty)

    def test_includes_model_name_per_call(self):
        usages = [
            TokenUsage(call_label="planner (第 1 次)", model="gpt-5-nano", prompt_tokens=1, completion_tokens=1, total_tokens=2),
        ]
        text = _format_token_usages(usages)
        self.assertIn("gpt-5-nano", text)
        self.assertIn("planner (第 1 次)", text)


if __name__ == "__main__":
    unittest.main()
