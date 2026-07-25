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

DEFAULT_AUTO_COMMIT = False
DEFAULT_CLAUDE_TIMEOUT_SECONDS = 1800
DEFAULT_OPENAI_TIMEOUT_SECONDS = 180


class ConfigError(Exception):
    """配置错误，程序应输出中文错误提示并安全退出。"""


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


def load_config(model_override: str | None = None) -> Config:
    """加载运行配置。

    从项目根目录 .env.local 读取环境变量；OPENAI_API_KEY 缺失时抛出 ConfigError。
    """
    if ENV_FILE.exists():
        load_dotenv(dotenv_path=ENV_FILE, override=False)

    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise ConfigError(
            "未找到 OPENAI_API_KEY，请在项目根目录 .env.local 中配置该变量后重试。"
        )

    # 不提供任何内置默认模型：未经确认在当前 OpenAI 账户下可用的模型名不得
    # 作为静默兜底值，必须由用户通过 .env.local 或 --model 显式指定。
    model = (model_override or os.environ.get("OPENAI_MODEL", "")).strip()
    if not model:
        raise ConfigError(
            "未配置 OPENAI_MODEL，且未通过 --model 指定。为避免使用未经确认在你的 OpenAI 账户下"
            "可用的模型，程序不会使用任何内置默认模型。请在项目根目录 .env.local 中设置 "
            "OPENAI_MODEL=<你的账户可访问的模型名>，或运行时加上 --model <模型名> 后重试。"
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
