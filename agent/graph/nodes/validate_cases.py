"""测试用例校验节点。"""

from __future__ import annotations

from agent.quality.validator import Validator


def validate_cases(state: dict) -> dict:
    """校验当前接口的用例，并在需要时触发重试。"""
    endpoint = state.get("current_endpoint")
    cases = state.get("cases", [])
    retry_count = state.get("retry_count", 0)

    if endpoint is None:
        return {"validated_cases": [], "error": "未找到当前接口"}

    validated_cases = Validator().validate(cases, endpoint)

    if not validated_cases:
        return {
            "validated_cases": [],
            "error": "LLM 未生成任何测试用例",
            "retry_count": retry_count + 1,
        }

    uncertain_cases = [case.name for case in validated_cases if case.uncertain]
    if uncertain_cases:
        return {
            "validated_cases": validated_cases,
            "error": f"存在 {len(uncertain_cases)} 个待确认用例",
            "retry_count": retry_count + 1,
        }

    return {"validated_cases": validated_cases, "error": None}
