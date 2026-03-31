"""E2E 流程设计节点。"""

from __future__ import annotations

import json
import re

from agent.models.factory import create_llm
from agent.prompts.flow_design import DESIGN_FLOW
from agent.schemas.flow import FlowDefinition
from agent.schemas.llm_output import DesignedFlow


def design_flow(state: dict) -> dict:
    """根据接口集合和业务描述设计流程定义。"""
    document = state.get("document")
    endpoints = document.endpoints if document else []
    endpoints_json = json.dumps(
        [endpoint.model_dump(exclude_none=True) for endpoint in endpoints],
        ensure_ascii=False,
        indent=2,
    )

    structured_llm = create_llm().with_structured_output(
        DesignedFlow
    ).with_retry(stop_after_attempt=3)
    result: DesignedFlow = structured_llm.invoke(
        DESIGN_FLOW.invoke(
            {
                "flow_description": state.get("flow_description", ""),
                "endpoints_json": endpoints_json,
            }
        )
    )

    flow_definition = FlowDefinition(
        name=result.name,
        description=result.description,
        base_url=state.get("base_url") or result.base_url,
        steps=result.steps,
    )
    return {"flow_definition": flow_definition}


def resolve_reference(ref: str, step_results: dict[int, dict]) -> str | None:
    """解析 $.steps[N].response.xxx 形式的步骤间引用。"""
    match = re.match(r"\$\.steps\[(\d+)\]\.response\.(.+)", ref)
    if not match:
        return None

    step_num = int(match.group(1))
    field_path = match.group(2)
    response = step_results.get(step_num)
    if response is None:
        return None

    value = response
    for key in field_path.split("."):
        if isinstance(value, dict):
            value = value.get(key)
        elif isinstance(value, list) and key.isdigit():
            idx = int(key)
            value = value[idx] if idx < len(value) else None
        else:
            return None

        if value is None:
            return None

    return value


def apply_input_mapping(
    request_data: dict,
    input_mapping: dict[str, str],
    step_results: dict[int, dict],
) -> dict:
    """将引用表达式替换为实际值。"""
    resolved = dict(request_data)
    for field, ref in input_mapping.items():
        value = resolve_reference(ref, step_results)
        if value is not None:
            resolved[field] = value
    return resolved
