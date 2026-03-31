"""analyze 命令对应的 LangGraph。"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from agent.graph.nodes import analyze_code, deduplicate_cases, generate_code, generate_gap_cases
from agent.graph.state import AnalyzeState


def build_analyze_graph():
    """构建缺失用例分析图。"""
    graph = StateGraph(AnalyzeState)

    graph.add_node("analyze_code", analyze_code)
    graph.add_node("generate_gap_cases", generate_gap_cases)
    graph.add_node("deduplicate_cases", deduplicate_cases)
    graph.add_node("generate_code", _generate_gap_code)

    graph.set_entry_point("analyze_code")
    graph.add_edge("analyze_code", "generate_gap_cases")
    graph.add_edge("generate_gap_cases", "deduplicate_cases")
    graph.add_edge("deduplicate_cases", "generate_code")
    graph.add_edge("generate_code", END)

    return graph.compile()


def _generate_gap_code(state: dict) -> dict:
    """复用代码生成节点输出补充用例。"""
    return generate_code(
        {
            "current_endpoint": state.get("endpoint"),
            "validated_cases": state.get("deduplicated_cases", []),
            "output_path": state.get("output_path"),
            "document": state.get("document"),
        }
    )
