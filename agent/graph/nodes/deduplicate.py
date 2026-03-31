"""缺失用例去重节点。"""

from __future__ import annotations

from agent.quality.deduplicator import Deduplicator


def deduplicate_cases(state: dict) -> dict:
    """去除与现有测试重复的缺失用例。"""
    deduplicated = Deduplicator().deduplicate(
        state.get("gap_cases", []),
        state.get("existing_names", []),
    )
    return {"deduplicated_cases": deduplicated}
