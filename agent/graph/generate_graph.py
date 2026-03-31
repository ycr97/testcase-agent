"""generate 命令对应的 LangGraph。"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from agent.graph.edges import has_next_endpoint, should_retry
from agent.graph.nodes import (
    generate_cases,
    generate_code,
    next_endpoint,
    parse_input,
    validate_cases,
)
from agent.graph.state import GenerateState


def build_generate_graph():
    """构建生成测试用例的状态图。"""
    graph = StateGraph(GenerateState)

    graph.add_node("parse_input", parse_input)
    graph.add_node("next_endpoint", next_endpoint)
    graph.add_node("generate_cases", generate_cases)
    graph.add_node("validate_cases", validate_cases)
    graph.add_node("generate_code", generate_code)

    graph.set_entry_point("parse_input")
    graph.add_edge("parse_input", "next_endpoint")
    graph.add_conditional_edges(
        "next_endpoint",
        has_next_endpoint,
        {
            "continue": "generate_cases",
            "done": END,
        },
    )
    graph.add_edge("generate_cases", "validate_cases")
    graph.add_conditional_edges(
        "validate_cases",
        should_retry,
        {
            "retry": "generate_cases",
            "accept": "generate_code",
        },
    )
    graph.add_edge("generate_code", "next_endpoint")

    return graph.compile()
