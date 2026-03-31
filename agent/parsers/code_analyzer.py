# -*- coding: utf-8 -*-
"""已有测试代码分析器（AST + LLM）"""

from __future__ import annotations

import ast
import json
from pathlib import Path

from agent.parsers.base import BaseParser
from agent.schemas.api_schema import APIDocument


class CodeAnalyzer(BaseParser):
    """分析已有测试代码，提取接口信息和已覆盖的测试场景。"""

    def __init__(self, llm=None):
        self._llm = llm

    def parse(self, source: str) -> APIDocument:
        """
        Args:
            source: Python 测试文件路径
        """
        path = Path(source)
        code = path.read_text(encoding="utf-8")
        analysis = self.analyze_code(code)

        # 用 LLM 从分析结果中提取标准化的接口信息
        from agent.parsers.text_parser import TextParser

        text_parser = TextParser(self._llm)
        return text_parser.parse(analysis["summary"])

    def analyze_code(self, code: str) -> dict:
        """用 AST 分析测试代码，提取结构化信息。"""
        tree = ast.parse(code)
        result = {
            "constants": {},
            "functions": [],
            "summary": "",
        }

        for node in ast.walk(tree):
            # 提取全局常量 (BASE_URL, HEADERS 等)
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        try:
                            value = ast.literal_eval(node.value)
                            result["constants"][target.id] = value
                        except (ValueError, TypeError):
                            # f-string 等无法 literal_eval 的值
                            pass

            # 提取测试函数
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                func_info = {
                    "name": node.name,
                    "docstring": ast.get_docstring(node) or "",
                    "body_source": ast.get_source_segment(code, node) or "",
                }
                result["functions"].append(func_info)

        # 生成文本摘要供 LLM 使用
        lines = []
        if "BASE_URL" in result["constants"]:
            lines.append(f"基础地址: {result['constants']['BASE_URL']}")
        if "HEADERS" in result["constants"]:
            lines.append(f"请求头: {json.dumps(result['constants']['HEADERS'], ensure_ascii=False)}")
        lines.append(f"已有 {len(result['functions'])} 个测试函数:")
        for func in result["functions"]:
            lines.append(f"  - {func['name']}: {func['docstring']}")
        lines.append("\n完整代码:\n" + code)
        result["summary"] = "\n".join(lines)

        return result

    def get_existing_test_names(self, source: str) -> list[str]:
        """获取已有测试函数名列表，用于去重。"""
        path = Path(source)
        code = path.read_text(encoding="utf-8")
        tree = ast.parse(code)
        return [
            node.name
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
        ]

    def get_source_code(self, source: str) -> str:
        """读取源文件内容。"""
        return Path(source).read_text(encoding="utf-8")
