# -*- coding: utf-8 -*-
"""中文自由文本解析器（LLM 辅助）"""

from __future__ import annotations

from agent.parsers.base import BaseParser
from agent.schemas.api_schema import APIDocument, APIEndpoint, APIParameter
from agent.llm.client import LLMClient
from agent.llm.prompts import SYSTEM_API_EXTRACTOR, PROMPT_EXTRACT_FROM_TEXT
from agent.llm.tools import TOOL_EXTRACT_API_ENDPOINTS


class TextParser(BaseParser):
    """从中文文字描述中提取 API 接口信息。"""

    def __init__(self, llm_client: LLMClient | None = None):
        self._llm = llm_client or LLMClient()

    def parse(self, source: str) -> APIDocument:
        """
        Args:
            source: 中文文字描述内容
        """
        result = self._llm.chat_with_tools(
            messages=[{"role": "user", "content": PROMPT_EXTRACT_FROM_TEXT.format(text=source)}],
            tools=[TOOL_EXTRACT_API_ENDPOINTS],
            system=SYSTEM_API_EXTRACTOR,
            tool_choice={"type": "tool", "name": "extract_api_endpoints"},
        )

        if not result:
            return APIDocument(title="", endpoints=[])

        endpoints = []
        for ep_data in result.get("endpoints", []):
            request_body = [
                APIParameter(**p) for p in ep_data.get("request_body", [])
            ]
            query_params = [
                APIParameter(**p) for p in ep_data.get("query_params", [])
            ]
            endpoint = APIEndpoint(
                path=ep_data.get("path", ""),
                method=ep_data.get("method", "POST"),
                summary=ep_data.get("summary", ""),
                description=ep_data.get("description", ""),
                base_url=ep_data.get("base_url", ""),
                auth_type=ep_data.get("auth_type", "bearer"),
                request_body_type=ep_data.get("request_body_type", "json"),
                request_body_is_array=ep_data.get("request_body_is_array", False),
                request_body=request_body,
                query_params=query_params,
                tags=ep_data.get("tags", []),
            )
            endpoints.append(endpoint)

        return APIDocument(title="从文字描述提取", endpoints=endpoints)
