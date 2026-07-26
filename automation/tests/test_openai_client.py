"""openai_client.py 单元测试：不发起真实网络请求，客户端全部使用 unittest.mock 模拟。"""
import json
import unittest
from unittest import mock

from automation.config import Config
from automation.openai_client import (
    PlannerError,
    ReviewerError,
    plan_next_task,
    review_change,
    strip_code_fence,
    validate_review_payload,
    validate_task_payload,
)

VALID_TASK = {
    "task_id": "T-001",
    "title": "示例任务",
    "objective": "示例目标",
    "rationale": "示例理由",
    "scope": "示例范围",
    "acceptance_criteria": ["构建通过"],
    "files_allowed": ["web/src/data/stages.ts"],
    # LAWGUARD_SOT.md 属于全局禁止路径（见 security.py 的
    # FORBIDDEN_PATH_PREFIXES），但把它列入 files_forbidden 是合理的冗余声明，
    # 不会导致校验失败（只有 files_allowed 需要严格排除全局禁止前缀）。
    "files_forbidden": ["LAWGUARD_SOT.md"],
    "validation_commands": ["npm run build"],
    "risk_level": "LOW",
    "requires_sot_update": False,
    "developer_prompt": "示例开发说明",
    # Value Gate 字段（2026-07-26 新增）：给出足以通过 ValueScore >= 15 门槛的
    # 取值（8+8+0+2-0-0=18），DONE/BLOCKED 场景下这些字段不参与业务规则校验，
    # 但仍需类型正确，统一给同一组值。
    "task_category": "产品能力提升",
    "value_user": 8,
    "value_product": 8,
    "value_legal": 0,
    "value_tech_debt": 2,
    "repetition_penalty": 0,
    "maintenance_cost": 0,
    "why_valuable": "测试用途：模拟一个明显有价值的任务",
    "why_not_other_candidates": "测试用途：无其它候选",
    "why_not_duplicate": "测试用途：非重复类别",
    "expected_user_benefit": "测试用途：模拟用户收益",
}

VALID_REVIEW = {
    "verdict": "PASS",
    "summary": "评审通过",
    "blocking_issues": [],
    "non_blocking_suggestions": [],
    "evidence": ["npm run build 通过"],
    "safe_to_commit": True,
    "commit_message": "feat: 示例改动",
}


class TestStripCodeFence(unittest.TestCase):
    def test_strips_json_fence(self):
        raw = '```json\n{"a": 1}\n```'
        self.assertEqual(strip_code_fence(raw), '{"a": 1}')

    def test_strips_plain_fence(self):
        raw = '```\n{"a": 1}\n```'
        self.assertEqual(strip_code_fence(raw), '{"a": 1}')

    def test_no_fence_untouched(self):
        raw = '{"a": 1}'
        self.assertEqual(strip_code_fence(raw), '{"a": 1}')


class TestValidateTaskPayload(unittest.TestCase):
    def test_valid_task_passes(self):
        self.assertEqual(validate_task_payload(VALID_TASK), [])

    def test_missing_field_detected(self):
        data = dict(VALID_TASK)
        del data["title"]
        issues = validate_task_payload(data)
        self.assertTrue(any("title" in i for i in issues))

    def test_invalid_risk_level_detected(self):
        data = dict(VALID_TASK)
        data["risk_level"] = "SUPER_HIGH"
        issues = validate_task_payload(data)
        self.assertTrue(any("risk_level" in i for i in issues))

    def test_blocked_task_skips_file_checks(self):
        data = dict(VALID_TASK)
        data["risk_level"] = "BLOCKED"
        data["files_allowed"] = []
        data["files_forbidden"] = []
        data["validation_commands"] = []
        self.assertEqual(validate_task_payload(data), [])

    def test_no_high_value_task_skips_file_checks(self):
        # NO_HIGH_VALUE_TASK（2026-07-26 新增）：Planner 明确判断当前没有高价值
        # 候选，且非阻塞场景，同样不涉及实际文件改动，应跳过文件/命令校验。
        data = dict(VALID_TASK)
        data["risk_level"] = "NO_HIGH_VALUE_TASK"
        data["files_allowed"] = []
        data["files_forbidden"] = []
        data["validation_commands"] = []
        self.assertEqual(validate_task_payload(data), [])

    def test_disallowed_command_detected(self):
        data = dict(VALID_TASK)
        data["validation_commands"] = ["git push origin main"]
        issues = validate_task_payload(data)
        self.assertTrue(any("validation_commands" in i for i in issues))

    def test_files_allowed_forbidden_conflict_detected(self):
        data = dict(VALID_TASK)
        data["files_allowed"] = ["web/src/data/stages.ts"]
        data["files_forbidden"] = ["web/src/data/stages.ts"]
        issues = validate_task_payload(data)
        self.assertTrue(any("冲突" in i for i in issues))


class TestValidateReviewPayload(unittest.TestCase):
    def test_valid_review_passes(self):
        self.assertEqual(validate_review_payload(VALID_REVIEW), [])

    def test_invalid_verdict_detected(self):
        data = dict(VALID_REVIEW)
        data["verdict"] = "MAYBE"
        issues = validate_review_payload(data)
        self.assertTrue(any("verdict" in i for i in issues))

    def test_fail_verdict_cannot_be_safe_to_commit(self):
        data = dict(VALID_REVIEW)
        data["verdict"] = "FAIL"
        data["safe_to_commit"] = True
        issues = validate_review_payload(data)
        self.assertTrue(any("safe_to_commit" in i for i in issues))

    def test_pass_without_commit_message_detected(self):
        data = dict(VALID_REVIEW)
        data["commit_message"] = ""
        issues = validate_review_payload(data)
        self.assertTrue(any("commit_message" in i for i in issues))


def _fake_config() -> Config:
    return Config(
        openai_api_key="sk-test-not-real",
        openai_model="gpt-test",
        auto_commit=False,
        claude_timeout_seconds=10,
        openai_timeout_seconds=10,
    )


def _fake_response(text: str, prompt_tokens: int | None = 100, completion_tokens: int | None = 20):
    response = mock.Mock()
    response.output_text = text
    if prompt_tokens is None and completion_tokens is None:
        response.usage = None
    else:
        response.usage = mock.Mock()
        response.usage.input_tokens = prompt_tokens
        response.usage.output_tokens = completion_tokens
        response.usage.total_tokens = (
            None if prompt_tokens is None or completion_tokens is None else prompt_tokens + completion_tokens
        )
    return response


class TestPlanNextTaskRetry(unittest.TestCase):
    """全部使用 mock.Mock 客户端，不发起任何真实 OpenAI 网络请求。"""

    def test_retries_once_on_invalid_json_then_succeeds(self):
        client = mock.Mock()
        client.responses.create.side_effect = [
            _fake_response("这不是合法 JSON"),
            _fake_response(json.dumps(VALID_TASK, ensure_ascii=False)),
        ]
        task, usages = plan_next_task(client, _fake_config(), "上下文")
        self.assertEqual(task.task_id, "T-001")
        self.assertEqual(client.responses.create.call_count, 2)
        self.assertEqual(len(usages), 2)

    def test_raises_after_two_invalid_attempts(self):
        client = mock.Mock()
        client.responses.create.side_effect = [
            _fake_response("不合法"),
            _fake_response("依然不合法"),
        ]
        with self.assertRaises(PlannerError) as ctx:
            plan_next_task(client, _fake_config(), "上下文")
        self.assertEqual(client.responses.create.call_count, 2)
        self.assertEqual(len(ctx.exception.usages), 2)

    def test_accepts_blocked_task_without_reliable_legal_source(self):
        client = mock.Mock()
        blocked_task = dict(VALID_TASK)
        blocked_task.update(
            risk_level="BLOCKED",
            files_allowed=[],
            files_forbidden=[],
            validation_commands=[],
            rationale="需要新增法律条文，但项目内没有可核验的官方来源",
        )
        client.responses.create.return_value = _fake_response(
            json.dumps(blocked_task, ensure_ascii=False)
        )
        task, usages = plan_next_task(client, _fake_config(), "上下文")
        self.assertEqual(task.risk_level, "BLOCKED")
        self.assertEqual(client.responses.create.call_count, 1)
        self.assertEqual(len(usages), 1)

    def test_usage_unknown_when_api_omits_it(self):
        client = mock.Mock()
        client.responses.create.return_value = _fake_response(
            json.dumps(VALID_TASK, ensure_ascii=False), prompt_tokens=None, completion_tokens=None
        )
        _task, usages = plan_next_task(client, _fake_config(), "上下文")
        self.assertIsNone(usages[0].prompt_tokens)
        self.assertIsNone(usages[0].completion_tokens)
        self.assertIsNone(usages[0].total_tokens)


class TestReviewChange(unittest.TestCase):
    def test_accepts_fail_verdict_for_missing_legal_source(self):
        client = mock.Mock()
        fail_review = dict(VALID_REVIEW)
        fail_review.update(
            verdict="FAIL",
            safe_to_commit=False,
            commit_message="",
            blocking_issues=["新增法律条文缺少可核验来源"],
        )
        client.responses.create.return_value = _fake_response(
            json.dumps(fail_review, ensure_ascii=False)
        )
        review, usage = review_change(client, _fake_config(), "评审上下文")
        self.assertEqual(review.verdict, "FAIL")
        self.assertFalse(review.safe_to_commit)
        self.assertEqual(usage.prompt_tokens, 100)

    def test_rejects_incomplete_schema(self):
        client = mock.Mock()
        client.responses.create.return_value = _fake_response('{"verdict": "PASS"}')
        with self.assertRaises(ReviewerError) as ctx:
            review_change(client, _fake_config(), "评审上下文")
        self.assertIsNotNone(ctx.exception.usage)


if __name__ == "__main__":
    unittest.main()
