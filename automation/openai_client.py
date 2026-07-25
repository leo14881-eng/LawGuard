"""OpenAI 客户端模块：调用 Responses API 完成任务规划与代码评审。

使用官方 OpenAI Python SDK 的 client.responses.create(...)，
通过 response.output_text 获取纯文本结果。
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import fields

from openai import OpenAI

from automation.config import PROMPTS_DIR, Config
from automation.models import (
    REVIEW_VERDICTS,
    RISK_LEVELS,
    DevelopmentTask,
    ReviewResult,
)
from automation.security import check_files_lists, normalize_command

logger = logging.getLogger("automation.openai_client")


class PlannerError(Exception):
    """规划器未能生成合法任务。"""


class ReviewerError(Exception):
    """评审器未能生成合法评审结果。"""


def strip_code_fence(text: str) -> str:
    """去除模型输出中可能存在的 Markdown 代码围栏（```json ... ``` 或 ``` ... ```）。"""
    if text is None:
        return ""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
    return cleaned.strip()


def _load_prompt(filename: str) -> str:
    path = PROMPTS_DIR / filename
    return path.read_text(encoding="utf-8")


def create_client(config: Config) -> OpenAI:
    """创建 OpenAI 客户端。不打印、不记录 API Key。"""
    return OpenAI(api_key=config.openai_api_key)


def _call_responses_api(client: OpenAI, config: Config, system_prompt: str, user_content: str) -> str:
    response = client.responses.create(
        model=config.openai_model,
        instructions=system_prompt,
        input=user_content,
        timeout=config.openai_timeout_seconds,
    )
    return response.output_text


def _parse_json_object(raw_text: str) -> dict:
    cleaned = strip_code_fence(raw_text)
    return json.loads(cleaned)


def validate_task_payload(data: dict) -> list[str]:
    """校验规划器返回的任务 JSON，返回问题列表（空表示通过）。"""
    issues: list[str] = []
    if not isinstance(data, dict):
        return ["规划器返回内容不是 JSON 对象"]

    required_fields = [f.name for f in fields(DevelopmentTask)]
    for name in required_fields:
        if name not in data:
            issues.append(f"缺少必填字段：{name}")
    if issues:
        return issues

    if not isinstance(data["task_id"], str) or not data["task_id"].strip():
        issues.append("task_id 必须是非空字符串")
    if not isinstance(data["title"], str) or not data["title"].strip():
        issues.append("title 必须是非空字符串")
    for text_field in ("objective", "rationale", "scope", "developer_prompt"):
        if not isinstance(data[text_field], str) or not data[text_field].strip():
            issues.append(f"{text_field} 必须是非空字符串")

    for list_field in ("acceptance_criteria", "files_allowed", "files_forbidden", "validation_commands"):
        if not isinstance(data[list_field], list):
            issues.append(f"{list_field} 必须是数组")

    if data.get("risk_level") not in RISK_LEVELS:
        issues.append(f"risk_level 取值非法：{data.get('risk_level')}")

    if not isinstance(data.get("requires_sot_update"), bool):
        issues.append("requires_sot_update 必须是布尔值")

    if issues:
        return issues

    # BLOCKED 任务代表规划器判断当前无法安全生成任务，不涉及实际文件改动，跳过文件与命令校验
    if data["risk_level"] != "BLOCKED":
        issues.extend(check_files_lists(data["files_allowed"], data["files_forbidden"]))
        for command in data["validation_commands"]:
            if normalize_command(command) is None:
                issues.append(f"validation_commands 中存在不在白名单内的命令：{command}")

    return issues


def validate_review_payload(data: dict) -> list[str]:
    """校验评审器返回的评审 JSON，返回问题列表（空表示通过）。"""
    issues: list[str] = []
    if not isinstance(data, dict):
        return ["评审器返回内容不是 JSON 对象"]

    required_fields = [f.name for f in fields(ReviewResult)]
    for name in required_fields:
        if name not in data:
            issues.append(f"缺少必填字段：{name}")
    if issues:
        return issues

    if data.get("verdict") not in REVIEW_VERDICTS:
        issues.append(f"verdict 取值非法：{data.get('verdict')}")
    if not isinstance(data.get("summary"), str) or not data["summary"].strip():
        issues.append("summary 必须是非空字符串")
    for list_field in ("blocking_issues", "non_blocking_suggestions", "evidence"):
        if not isinstance(data.get(list_field), list):
            issues.append(f"{list_field} 必须是数组")
    if not isinstance(data.get("safe_to_commit"), bool):
        issues.append("safe_to_commit 必须是布尔值")
    if not isinstance(data.get("commit_message"), str):
        issues.append("commit_message 必须是字符串")

    if not issues:
        if data["verdict"] != "PASS" and data["safe_to_commit"]:
            issues.append("verdict 不是 PASS 时 safe_to_commit 必须为 false")
        if data["verdict"] == "PASS" and data["safe_to_commit"] and not data["commit_message"].strip():
            issues.append("verdict=PASS 且 safe_to_commit=true 时 commit_message 不能为空")

    return issues


def plan_next_task(client: OpenAI, config: Config, project_context: str) -> DevelopmentTask:
    """调用 OpenAI 规划下一项开发任务；输出不合法时最多重试一次，仍失败则安全停止。"""
    system_prompt = _load_prompt("planner_system.txt")
    last_error = ""
    for attempt in range(2):
        raw = _call_responses_api(client, config, system_prompt, project_context)
        try:
            data = _parse_json_object(raw)
        except json.JSONDecodeError as exc:
            last_error = f"JSON 解析失败：{exc}"
            logger.warning("规划器输出 JSON 解析失败（第 %d 次）：%s", attempt + 1, exc)
            continue
        issues = validate_task_payload(data)
        if issues:
            last_error = "；".join(issues)
            logger.warning("规划器输出校验失败（第 %d 次）：%s", attempt + 1, last_error)
            continue
        return DevelopmentTask(**{f.name: data[f.name] for f in fields(DevelopmentTask)})

    raise PlannerError(f"规划器连续两次输出不合法，已安全停止。最后一次错误：{last_error}")


def review_change(client: OpenAI, config: Config, review_context: str) -> ReviewResult:
    """调用 OpenAI 对本次改动进行代码评审。"""
    system_prompt = _load_prompt("reviewer_system.txt")
    raw = _call_responses_api(client, config, system_prompt, review_context)
    try:
        data = _parse_json_object(raw)
    except json.JSONDecodeError as exc:
        raise ReviewerError(f"评审器输出 JSON 解析失败：{exc}") from exc
    issues = validate_review_payload(data)
    if issues:
        raise ReviewerError("评审器输出校验失败：" + "；".join(issues))
    return ReviewResult(**{f.name: data[f.name] for f in fields(ReviewResult)})
