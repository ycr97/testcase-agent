"""缺失用例生成节点。"""

from __future__ import annotations

from agent.models.factory import create_llm
from agent.prompts.gap_analysis import ANALYZE_GAPS
from agent.schemas.llm_output import GeneratedCases


def generate_gap_cases(state: dict) -> dict:
    """根据已有代码分析缺失用例。"""
    endpoint = state.get("endpoint")
    if endpoint is None:
        return {"gap_cases": [], "error": "未能从代码中识别接口"}

    structured_llm = create_llm().with_structured_output(
        GeneratedCases
    ).with_retry(stop_after_attempt=3)
    result: GeneratedCases = structured_llm.invoke(
        ANALYZE_GAPS.invoke(
            {
                "existing_code": state.get("existing_code", ""),
                "endpoint_json": endpoint.model_dump_json(indent=2, exclude_none=True),
            }
        )
    )

    for case in result.cases:
        case.endpoint_path = endpoint.path
        case.method = endpoint.method

    return {"gap_cases": result.cases, "error": None}
