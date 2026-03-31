"""测试用例生成节点。"""

from __future__ import annotations

from agent.models.factory import create_llm
from agent.prompts.generation import (
    GENERATE_ABNORMAL_CASES,
    GENERATE_BOUNDARY_CASES,
    GENERATE_NORMAL_CASES,
)
from agent.schemas.llm_output import GeneratedCases
from agent.schemas.test_case import TestCategory


def generate_cases(state: dict) -> dict:
    """为当前接口生成测试用例。"""
    endpoint = state.get("current_endpoint")
    if endpoint is None:
        return {"cases": []}

    categories = state.get("categories") or ["normal", "abnormal", "boundary"]
    prompt_map = {
        "normal": GENERATE_NORMAL_CASES,
        "abnormal": GENERATE_ABNORMAL_CASES,
        "boundary": GENERATE_BOUNDARY_CASES,
    }

    structured_llm = create_llm().with_structured_output(
        GeneratedCases
    ).with_retry(stop_after_attempt=3)
    endpoint_json = endpoint.model_dump_json(indent=2, exclude_none=True)
    all_cases = []

    for category in categories:
        prompt = prompt_map.get(category)
        if prompt is None:
            continue

        result: GeneratedCases = structured_llm.invoke(
            prompt.invoke({"endpoint_json": endpoint_json})
        )
        for case in result.cases:
            case.endpoint_path = endpoint.path
            case.method = endpoint.method
            case.category = TestCategory(category)
        all_cases.extend(result.cases)

    return {"cases": all_cases, "error": None}
