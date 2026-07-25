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
    TokenUsage,
)
from automation.security import check_files_lists, normalize_command

logger = logging.getLogger("automation.openai_client")


class PlannerError(Exception):
    """规划器未能生成合法任务。携带已发生调用的 Token 用量，便于失败时仍能统计消耗。"""

    def __init__(self, message: str, usages: list[TokenUsage] | None = None):
        super().__init__(message)
        self.usages = usages or []


class ReviewerError(Exception):
    """评审器未能生成合法评审结果。携带本次调用的 Token 用量，便于失败时仍能统计消耗。"""

    def __init__(self, message: str, usage: TokenUsage | None = None):
        super().__init__(message)
        self.usage = usage


class ModelListError(Exception):
    """调用 OpenAI Models API 获取模型列表失败（网络异常、鉴权失败、无权限等）。"""


# 依据模型 ID 中的关键词排除明显不适合"普通文本规划/评审"场景的模型：
# 音频、实时语音、转录、图像/绘图、Sora 视频、Web 搜索专用、embedding、审核、
# 语音合成、旧版 instruct 补全模型、以及 babbage/davinci 等旧世代模型。
# 仅用于展示排序参考，不用于自动选择模型；过滤后为空时调用方应展示完整列表。
_NON_TEXT_MODEL_HINTS = (
    "audio", "realtime", "transcribe", "sora", "search",
    "embedding", "moderation", "image", "whisper", "tts",
    "instruct", "babbage", "davinci", "dall-e",
)

# Models API 返回的是"当前 API Key 可见的模型"，并不保证该模型一定支持
# Responses API 或当前请求参数；必须在 README 与控制台中明确提示，避免用户
# 误以为出现在列表里就等同于可以直接使用。
MODELS_API_DISCLAIMER = (
    "Models API 仅表示当前 API Key 可以看到该模型，不保证该模型一定支持当前请求参数"
    "和 Responses API；最终以首次实际请求结果为准。"
)

# 供 --list-models 展示的中文选型建议；纯提示文本，程序不会据此自动选择或
# 修改用户的 OPENAI_MODEL 配置，是否采用仍需用户显式写入 .env.local 或 --model。
# 遵循 Cost First 原则：默认推荐成本最低、足以完成 Planner JSON 规划与基础 Review 的
# gpt-5-nano（真正的编码工作由 Claude Code 承担，Validator + Tests + Review Gate 兜底安全）；
# 仅在正式发布前的最终评审等更看重质量的场景才建议临时切换到 gpt-5.5。
MODEL_RECOMMENDATION_NOTES = (
    ("gpt-5-nano", "推荐默认使用（成本最低，足够完成 Planner/Review 的 JSON 输出）"),
    ("gpt-5.5", "高质量，建议仅在正式发布前的最终评审临时使用"),
)


def list_available_models(api_key: str, timeout: int = 30) -> list[str]:
    """调用 OpenAI Models API 获取当前账户可访问的模型 ID 列表（按字母排序）。

    仅做只读查询，不进行任何文本生成调用；不打印、不记录 api_key。
    失败时统一转换为 ModelListError 并附带中文可读信息。
    """
    client = OpenAI(api_key=api_key)
    try:
        response = client.models.list(timeout=timeout)
    except Exception as exc:  # noqa: BLE001 - OpenAI SDK 网络/鉴权异常种类繁多，统一转换
        raise ModelListError(f"调用 OpenAI Models API 失败：{exc}") from exc
    try:
        model_ids = sorted({item.id for item in response.data})
    except AttributeError as exc:
        raise ModelListError(f"OpenAI Models API 返回内容格式异常：{exc}") from exc
    return model_ids


def filter_likely_text_models(model_ids: list[str]) -> list[str]:
    """从模型列表中过滤出适合 Responses API 普通文本规划/评审场景的模型，仅用于展示参考。

    这是启发式关键词过滤（见 _NON_TEXT_MODEL_HINTS），不用于自动选择模型；
    过滤后为空则原样返回完整列表，避免因关键词误判而向用户隐藏实际可用的模型。
    """
    filtered = [m for m in model_ids if not any(hint in m.lower() for hint in _NON_TEXT_MODEL_HINTS)]
    return filtered or list(model_ids)


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


def _extract_token_usage(response, model: str, call_label: str) -> TokenUsage:
    """从 Responses API 返回对象中提取 Token 用量，取不到时对应字段为 None（显示为 Unknown）。

    不同 SDK/API 版本字段命名可能有差异，这里做防御性提取，不因取不到用量而报错。
    """
    usage = getattr(response, "usage", None)
    if usage is None:
        return TokenUsage(call_label=call_label, model=model, prompt_tokens=None, completion_tokens=None, total_tokens=None)
    prompt_tokens = getattr(usage, "input_tokens", None)
    if prompt_tokens is None:
        prompt_tokens = getattr(usage, "prompt_tokens", None)
    completion_tokens = getattr(usage, "output_tokens", None)
    if completion_tokens is None:
        completion_tokens = getattr(usage, "completion_tokens", None)
    total_tokens = getattr(usage, "total_tokens", None)
    return TokenUsage(
        call_label=call_label, model=model,
        prompt_tokens=prompt_tokens, completion_tokens=completion_tokens, total_tokens=total_tokens,
    )


def _call_responses_api(
    client: OpenAI, config: Config, system_prompt: str, user_content: str, call_label: str
) -> tuple[str, TokenUsage]:
    response = client.responses.create(
        model=config.openai_model,
        instructions=system_prompt,
        input=user_content,
        timeout=config.openai_timeout_seconds,
    )
    usage = _extract_token_usage(response, config.openai_model, call_label)
    return response.output_text, usage


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

    # DONE（无更多开发任务）与 BLOCKED（存在方向但无法安全继续）均不涉及实际文件改动，
    # 跳过文件与命令校验。
    if data["risk_level"] not in ("BLOCKED", "DONE"):
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


def plan_next_task(
    client: OpenAI, config: Config, project_context: str
) -> tuple[DevelopmentTask, list[TokenUsage]]:
    """调用 OpenAI 规划下一项开发任务；输出不合法时最多重试一次，仍失败则安全停止。

    返回任务本身与本次调用（含重试）产生的全部 Token 用量记录。
    """
    system_prompt = _load_prompt("planner_system.txt")
    last_error = ""
    usages: list[TokenUsage] = []
    for attempt in range(2):
        label = f"planner (第 {attempt + 1} 次)"
        raw, usage = _call_responses_api(client, config, system_prompt, project_context, label)
        usages.append(usage)
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
        task = DevelopmentTask(**{f.name: data[f.name] for f in fields(DevelopmentTask)})
        return task, usages

    raise PlannerError(f"规划器连续两次输出不合法，已安全停止。最后一次错误：{last_error}", usages=usages)


def review_change(client: OpenAI, config: Config, review_context: str) -> tuple[ReviewResult, TokenUsage]:
    """调用 OpenAI 对本次改动进行代码评审，返回评审结论与本次调用的 Token 用量。"""
    system_prompt = _load_prompt("reviewer_system.txt")
    raw, usage = _call_responses_api(client, config, system_prompt, review_context, "reviewer")
    try:
        data = _parse_json_object(raw)
    except json.JSONDecodeError as exc:
        raise ReviewerError(f"评审器输出 JSON 解析失败：{exc}", usage=usage) from exc
    issues = validate_review_payload(data)
    if issues:
        raise ReviewerError("评审器输出校验失败：" + "；".join(issues), usage=usage)
    review = ReviewResult(**{f.name: data[f.name] for f in fields(ReviewResult)})
    return review, usage
