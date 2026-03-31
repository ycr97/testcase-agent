"""切换到下一个接口。"""

from __future__ import annotations


def next_endpoint(state: dict) -> dict:
    """从队列中取出下一个待处理接口。"""
    pending = list(state.get("pending_endpoints", []))
    if not pending:
        return {
            "current_endpoint": None,
            "cases": [],
            "validated_cases": [],
            "error": None,
        }

    current_endpoint = pending.pop(0)
    return {
        "current_endpoint": current_endpoint,
        "pending_endpoints": pending,
        "cases": [],
        "validated_cases": [],
        "retry_count": 0,
        "error": None,
    }
