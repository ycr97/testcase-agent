# -*- coding: utf-8 -*-
"""中文自由文本解析器（LLM 辅助）"""

from __future__ import annotations

from agent.parsers.base import BaseParser
from agent.models.factory import create_llm
from agent.prompts.extraction import EXTRACT_FROM_TEXT
from agent.schemas.api_schema import APIDocument
from agent.schemas.llm_output import ExtractedEndpoints


class TextParser(BaseParser):
    """从中文文字描述中提取 API 接口信息。"""

    def __init__(self, llm=None):
        self._llm = llm

    def parse(self, source: str) -> APIDocument:
        """
        Args:
            source: 中文文字描述内容
        """
        structured_llm = (self._llm or create_llm()).with_structured_output(
            ExtractedEndpoints
        ).with_retry(stop_after_attempt=3)
        result: ExtractedEndpoints = structured_llm.invoke(
            EXTRACT_FROM_TEXT.invoke({"text": source})
        )
        return APIDocument(title="从文字描述提取", endpoints=result.endpoints)
