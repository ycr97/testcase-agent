"""flow 命令专用的 Swagger 解析节点。"""

from __future__ import annotations

from agent.parsers.swagger_parser import SwaggerParser


def parse_swagger(state: dict) -> dict:
    """解析 flow 命令输入的 Swagger 文件。"""
    document = SwaggerParser().parse(state.get("input_path", ""))
    return {"document": document, "error": None}
