"""输入解析节点。"""

from __future__ import annotations

from agent.parsers.markdown_parser import MarkdownParser
from agent.parsers.swagger_parser import SwaggerParser
from agent.parsers.text_parser import TextParser
from agent.parsers.word_parser import WordParser


def parse_input(state: dict) -> dict:
    """按输入源类型解析文档。"""
    input_source = state.get("input_source")
    input_path = state.get("input_path", "")

    if input_source == "swagger":
        document = SwaggerParser().parse(input_path)
    elif input_source == "text":
        document = TextParser().parse(input_path)
    elif input_source == "doc":
        document = WordParser().parse(input_path)
    elif input_source == "markdown":
        document = MarkdownParser().parse(input_path)
    else:
        raise ValueError(f"不支持的输入源: {input_source}")

    return {
        "document": document,
        "pending_endpoints": list(document.endpoints),
        "current_endpoint": None,
        "cases": [],
        "validated_cases": [],
        "retry_count": 0,
        "error": None,
    }
