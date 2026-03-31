"""根据配置创建 LangChain ChatModel 实例。"""

from __future__ import annotations

import os

from langchain_core.language_models import BaseChatModel

from agent.config import get_settings


def create_llm() -> BaseChatModel:
    """根据 provider 配置创建统一的 ChatModel。"""
    settings = get_settings()
    provider = settings.llm.provider.strip().lower()

    if os.environ.get("LANGSMITH_API_KEY"):
        os.environ.setdefault("LANGSMITH_TRACING", "true")
        os.environ.setdefault("LANGSMITH_PROJECT", "testcase-agent")

    common_kwargs = {
        "temperature": settings.llm.temperature,
        "max_tokens": settings.llm.max_tokens,
    }

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        model: BaseChatModel = ChatAnthropic(
            model=settings.llm.model,
            api_key=settings.llm.api_key,
            **common_kwargs,
        )
    elif provider == "openai":
        from langchain_openai import ChatOpenAI

        model = ChatOpenAI(
            model=settings.llm.model,
            api_key=settings.llm.api_key,
            **common_kwargs,
        )
    else:
        raise ValueError(f"不支持的 LLM provider: {settings.llm.provider}")

    return model
