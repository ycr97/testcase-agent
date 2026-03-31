"""流程定义输出节点。"""

from __future__ import annotations

from pathlib import Path


def output_flow(state: dict) -> dict:
    """将流程定义写出为 JSON 文件。"""
    flow_definition = state.get("flow_definition")
    if flow_definition is None:
        return {}

    output_path = Path(state.get("output_path") or "generated_tests/flow_definition.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        flow_definition.model_dump_json(indent=2, exclude_none=True),
        encoding="utf-8",
    )
    return {"generated_file": str(output_path)}
