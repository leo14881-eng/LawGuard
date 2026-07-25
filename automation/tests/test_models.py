"""models.py 单元测试：数据结构序列化与报告脱敏。"""
import json
import unittest

from automation.models import CommandResult, DevelopmentTask, ReviewResult, RunReport


class TestModelSerialization(unittest.TestCase):
    def test_development_task_to_dict(self):
        task = DevelopmentTask(
            task_id="T-1", title="标题", objective="目标", rationale="理由", scope="范围",
            acceptance_criteria=["a"], files_allowed=["web/src/data/stages.ts"],
            files_forbidden=["LAWGUARD_SOT.md"], validation_commands=["npm run build"],
            risk_level="LOW", requires_sot_update=False, developer_prompt="说明",
        )
        data = task.to_dict()
        self.assertEqual(data["task_id"], "T-1")
        self.assertEqual(data["files_allowed"], ["web/src/data/stages.ts"])

    def test_run_report_redacts_secret_in_json(self):
        claude_result = CommandResult(
            command="claude -p x", cwd=".", exit_code=0,
            stdout="OPENAI_API_KEY=sk-thisisasecretkey1234567890", stderr="",
            duration_seconds=1.0, timed_out=False,
        )
        review = ReviewResult(
            verdict="PASS", summary="ok", blocking_issues=[], non_blocking_suggestions=[],
            evidence=[], safe_to_commit=True, commit_message="feat: 测试",
        )
        report = RunReport(
            run_id="run-1", started_at="2026-07-26T00:00:00", finished_at="2026-07-26T00:01:00",
            task=None, claude_result=claude_result, validation_results=[], review=review,
            git_commit=None, final_status="COMMITTED", error_message=None,
        )
        safe_json = report.to_safe_json()
        self.assertNotIn("sk-thisisasecretkey1234567890", safe_json)
        parsed = json.loads(safe_json)
        self.assertEqual(parsed["run_id"], "run-1")


if __name__ == "__main__":
    unittest.main()
