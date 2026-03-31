"""Graph 条件边逻辑。"""

from __future__ import annotations

from agent.graph.state import GenerateState


def has_next_endpoint(state: GenerateState) -> str:
    """判断当前是否还有接口要处理。"""
    return "continue" if state.get("current_endpoint") is not None else "done"


def should_retry(state: GenerateState) -> str:
    """当校验结果不理想时决定是否重试生成。"""
    error = state.get("error")
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 0)
    return "retry" if error and retry_count <= max_retries else "accept"
