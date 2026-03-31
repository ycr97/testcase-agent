"""已有测试代码分析节点。"""

from __future__ import annotations

from agent.parsers.code_analyzer import CodeAnalyzer


def analyze_code(state: dict) -> dict:
    """提取已有代码、测试名和接口信息。"""
    code_path = state["code_path"]
    analyzer = CodeAnalyzer()
    existing_code = analyzer.get_source_code(code_path)
    existing_names = analyzer.get_existing_test_names(code_path)
    document = analyzer.parse(code_path)
    endpoint = document.endpoints[0] if document.endpoints else None

    return {
        "existing_code": existing_code,
        "existing_names": existing_names,
        "document": document,
        "endpoint": endpoint,
        "gap_cases": [],
        "deduplicated_cases": [],
        "error": None,
    }
