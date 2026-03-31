# -*- coding: utf-8 -*-
"""E2E 流程步骤间的数据依赖解析"""

from __future__ import annotations

import re


def resolve_reference(ref: str, step_results: dict[int, dict]) -> str | None:
    """
    解析步骤间引用，如 $.steps[0].response.data.id

    Args:
        ref: 引用表达式
        step_results: {步骤序号: 响应 JSON}

    Returns:
        解析后的值，或 None
    """
    match = re.match(r"\$\.steps\[(\d+)\]\.response\.(.+)", ref)
    if not match:
        return None

    step_num = int(match.group(1))
    field_path = match.group(2)

    response = step_results.get(step_num)
    if response is None:
        return None

    # 按点号逐层取值
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
    request_data: dict, input_mapping: dict[str, str], step_results: dict[int, dict]
) -> dict:
    """
    将引用表达式替换为实际值。

    Args:
        request_data: 请求数据模板
        input_mapping: {字段名: 引用表达式}
        step_results: 已执行步骤的响应结果
    """
    resolved = dict(request_data)
    for field, ref in input_mapping.items():
        value = resolve_reference(ref, step_results)
        if value is not None:
            resolved[field] = value
    return resolved
