"""配置加载模块：从项目根目录 .env.local 读取自动化系统运行所需配置。

不得覆盖已存在的 .env.local，不得将密钥写入日志。
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# 项目根目录（automation 目录的上一级），自动化系统只允许在此目录内工作
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env.local"
AUTOMATION_DIR = PROJECT_ROOT / "automation"
RUNTIME_DIR = AUTOMATION_DIR / "runtime"
REPORTS_DIR = AUTOMATION_DIR / "reports"
PROMPTS_DIR = AUTOMATION_DIR / "prompts"

WEB_DIR = PROJECT_ROOT / "web"
SOT_FILE = PROJECT_ROOT / "LAWGUARD_SOT.md"
CLAUDE_MD_FILE = PROJECT_ROOT / "CLAUDE.md"
# Auto Dev 全自动循环专属的进度台账，独立于 LAWGUARD_SOT.md 的"当前开发进度"章节，
# 由 orchestrator 在每个任务自动提交后维护，供 Planner 下一轮读取以避免重复开发。
PROGRESS_FILE = PROJECT_ROOT / "docs" / "project" / "AUTODEV_PROGRESS.md"

DEFAULT_AUTO_COMMIT = False
DEFAULT_CLAUDE_TIMEOUT_SECONDS = 1800
DEFAULT_OPENAI_TIMEOUT_SECONDS = 180


class ConfigError(Exception):
    """配置错误，程序应输出中文错误提示并安全退出。"""


class ModelNotConfiguredError(ConfigError):
    """OPENAI_MODEL 未配置的专用异常。

    携带已通过校验的 api_key，供调用方（orchestrator）尝试调用 OpenAI Models API
    做模型自检、向用户展示可选模型，而不必重新加载一遍配置。本异常本身不触发任何
    模型选择或文本生成，只是把已验证的 api_key 传递给上层用于只读查询。
    """

    def __init__(self, message: str, api_key: str):
        super().__init__(message)
        self.api_key = api_key


@dataclass
class Config:
    """自动化系统运行配置。"""

    openai_api_key: str
    openai_model: str
    auto_commit: bool
    claude_timeout_seconds: int
    openai_timeout_seconds: int
    project_root: Path = PROJECT_ROOT


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_int(value: str | None, default: int) -> int:
    if value is None or value.strip() == "":
        return default
    try:
        return int(value.strip())
    except ValueError:
        return default


def _load_env_file() -> None:
    """加载项目根目录 .env.local（若存在），不覆盖已有的进程环境变量。"""
    if ENV_FILE.exists():
        load_dotenv(dotenv_path=ENV_FILE, override=False)


def load_api_key_only() -> str:
    """仅加载并校验 OPENAI_API_KEY，不要求 OPENAI_MODEL。

    供 --list-models 等只需要调用 OpenAI 只读接口（不涉及选择具体文本生成模型）的
    场景使用；OPENAI_API_KEY 缺失时抛出 ConfigError。
    """
    _load_env_file()
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise ConfigError(
            "未找到 OPENAI_API_KEY，请在项目根目录 .env.local 中配置该变量后重试。"
        )
    return api_key


def load_config(model_override: str | None = None) -> Config:
    """加载运行配置。

    OPENAI_API_KEY 缺失时抛出 ConfigError；OPENAI_MODEL 缺失时抛出
    ModelNotConfiguredError（ConfigError 的子类，携带 api_key 供上层做模型自检）。
    """
    api_key = load_api_key_only()

    # 不提供任何内置默认模型：未经确认在当前 OpenAI 账户下可用的模型名不得
    # 作为静默兜底值，必须由用户通过 .env.local 或 --model 显式指定。
    model = (model_override or os.environ.get("OPENAI_MODEL", "")).strip()
    if not model:
        raise ModelNotConfiguredError(
            "未配置 OPENAI_MODEL，且未通过 --model 指定。为避免使用未经确认在你的 OpenAI 账户下"
            "可用的模型，程序不会使用任何内置默认模型。请在项目根目录 .env.local 中设置 "
            "OPENAI_MODEL=<你的账户可访问的模型名>，或运行时加上 --model <模型名> 后重试。",
            api_key=api_key,
        )

    auto_commit = _parse_bool(os.environ.get("LAWGUARD_AUTO_COMMIT"), DEFAULT_AUTO_COMMIT)
    claude_timeout = _parse_int(
        os.environ.get("LAWGUARD_CLAUDE_TIMEOUT_SECONDS"), DEFAULT_CLAUDE_TIMEOUT_SECONDS
    )
    openai_timeout = _parse_int(
        os.environ.get("LAWGUARD_OPENAI_TIMEOUT_SECONDS"), DEFAULT_OPENAI_TIMEOUT_SECONDS
    )

    return Config(
        openai_api_key=api_key,
        openai_model=model,
        auto_commit=auto_commit,
        claude_timeout_seconds=claude_timeout,
        openai_timeout_seconds=openai_timeout,
    )
