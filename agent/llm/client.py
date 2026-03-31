# -*- coding: utf-8 -*-
"""Anthropic Claude API 客户端封装"""

from __future__ import annotations

import time
import logging
from typing import Any

import anthropic

from agent.config import get_settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Claude API 客户端，支持普通对话和 tool_use 结构化输出。"""

    def __init__(self, model: str | None = None, max_retries: int = 3):
        settings = get_settings()
        self._client = anthropic.Anthropic(api_key=settings.llm.api_key)
        self._model = model or settings.llm.model
        self._max_retries = max_retries
        self._temperature = settings.llm.temperature
        self._max_tokens = settings.llm.max_tokens

    def chat(
        self,
        messages: list[dict[str, str]],
        system: str = "",
    ) -> str:
        """普通对话，返回文本响应。"""
        kwargs: dict[str, Any] = {
            "model": self._model,
            "max_tokens": self._max_tokens,
            "temperature": self._temperature,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system

        response = self._call_with_retry(**kwargs)
        return response.content[0].text

    def chat_with_tools(
        self,
        messages: list[dict[str, str]],
        tools: list[dict],
        system: str = "",
        tool_choice: dict | None = None,
    ) -> dict | None:
        """使用 tool_use 强制结构化输出，返回工具调用的 input（dict）。"""
        kwargs: dict[str, Any] = {
            "model": self._model,
            "max_tokens": self._max_tokens,
            "temperature": self._temperature,
            "messages": messages,
            "tools": tools,
        }
        if system:
            kwargs["system"] = system
        if tool_choice:
            kwargs["tool_choice"] = tool_choice

        response = self._call_with_retry(**kwargs)

        # 提取 tool_use block
        for block in response.content:
            if block.type == "tool_use":
                return block.input
        return None

    def _call_with_retry(self, **kwargs) -> anthropic.types.Message:
        """带重试的 API 调用。"""
        last_error = None
        for attempt in range(1, self._max_retries + 1):
            try:
                return self._client.messages.create(**kwargs)
            except anthropic.RateLimitError as e:
                last_error = e
                wait = 2 ** attempt
                logger.warning(f"Rate limited, retrying in {wait}s (attempt {attempt}/{self._max_retries})")
                time.sleep(wait)
            except anthropic.APIError as e:
                last_error = e
                if attempt == self._max_retries:
                    break
                wait = 2 ** attempt
                logger.warning(f"API error: {e}, retrying in {wait}s (attempt {attempt}/{self._max_retries})")
                time.sleep(wait)
        raise last_error
