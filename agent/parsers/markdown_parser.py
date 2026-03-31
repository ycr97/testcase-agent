# -*- coding: utf-8 -*-
"""Markdown 文档解析器（LLM 辅助）"""

from __future__ import annotations

from pathlib import Path

from agent.parsers.text_parser import TextParser
from agent.parsers.base import BaseParser
from agent.schemas.api_schema import APIDocument


class MarkdownParser(BaseParser):
    """解析 Markdown 格式的接口文档，复用 TextParser 的 LLM 提取能力。"""

    def __init__(self):
        self._text_parser = TextParser()

    def parse(self, source: str) -> APIDocument:
        """
        Args:
            source: Markdown 文件路径
        """
        path = Path(source)
        content = path.read_text(encoding="utf-8")
        doc = self._text_parser.parse(content)
        doc.title = doc.title or path.stem
        return doc
