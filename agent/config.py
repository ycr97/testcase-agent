# -*- coding: utf-8 -*-
"""配置管理：从 config/settings.yaml 和环境变量加载配置。"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = PROJECT_ROOT / "config" / "settings.yaml"


class LLMSettings(BaseModel):
    provider: str = "anthropic"
    model: str = "claude-sonnet-4-20250514"
    api_key: str = ""
    max_tokens: int = 4096
    temperature: float = 0.0


class EnvironmentConfig(BaseModel):
    name: str = "uat"
    base_urls: dict[str, str] = Field(default_factory=dict)
    auth_token: str = ""


class OutputSettings(BaseModel):
    directory: str = "generated_tests"
    style: str = "requests_plain"


class Settings(BaseModel):
    llm: LLMSettings = Field(default_factory=LLMSettings)
    environment: EnvironmentConfig = Field(default_factory=EnvironmentConfig)
    output: OutputSettings = Field(default_factory=OutputSettings)


def _load_yaml_config() -> dict:
    """加载 YAML 配置文件。"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


@lru_cache
def get_settings() -> Settings:
    """获取配置（单例），优先读取环境变量。"""
    raw = _load_yaml_config()

    # LLM 配置
    llm_raw = raw.get("llm", {})
    llm = LLMSettings(
        provider=llm_raw.get("provider", "anthropic"),
        model=llm_raw.get("model", "claude-sonnet-4-20250514"),
        api_key=os.environ.get("ANTHROPIC_API_KEY", llm_raw.get("api_key", "")),
        max_tokens=llm_raw.get("max_tokens", 4096),
        temperature=llm_raw.get("temperature", 0.0),
    )

    # 环境配置
    env_name = os.environ.get("TEST_ENV", "uat")
    env_raw = raw.get("environments", {}).get(env_name, {})
    environment = EnvironmentConfig(
        name=env_name,
        base_urls=env_raw.get("base_urls", {}),
        auth_token=os.environ.get("AUTH_TOKEN", env_raw.get("auth_token", "")),
    )

    # 输出配置
    out_raw = raw.get("output", {})
    output = OutputSettings(
        directory=out_raw.get("directory", "generated_tests"),
        style=out_raw.get("style", "requests_plain"),
    )

    return Settings(llm=llm, environment=environment, output=output)
