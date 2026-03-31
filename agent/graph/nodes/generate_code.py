"""测试代码生成节点。"""

from __future__ import annotations

from pathlib import Path

from agent.generators.code_generator import CodeGenerator
from agent.schemas.test_case import TestSuite


def generate_code(state: dict) -> dict:
    """将当前接口的测试用例渲染为测试文件。"""
    endpoint = state.get("current_endpoint")
    cases = state.get("validated_cases", [])
    if endpoint is None or not cases:
        return {}

    suite = TestSuite(
        endpoint_path=endpoint.path,
        endpoint_summary=endpoint.summary,
        base_url=endpoint.base_url,
        auth_type=endpoint.auth_type,
        cases=cases,
    )

    output_path = _resolve_output_path(
        state.get("output_path"),
        state.get("document"),
        endpoint.path,
    )
    generated_file = CodeGenerator().generate(suite, output_path)
    return {"generated_files": [generated_file]}


def _resolve_output_path(
    output_path: str | None,
    document,
    endpoint_path: str,
) -> str | None:
    """兼容单文件输出和多接口批量输出。"""
    if not output_path:
        return None

    endpoint_count = len(document.endpoints) if document else 0
    target = Path(output_path)
    filename = CodeGenerator._path_to_filename(endpoint_path)

    if not target.suffix:
        return str(target / filename)

    if endpoint_count <= 1:
        return str(target)

    stem = target.stem
    suffix = target.suffix
    endpoint_stem = filename.removesuffix(".py")
    return str(target.with_name(f"{stem}_{endpoint_stem}{suffix}"))
