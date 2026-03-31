"""flow 命令对应的 LangGraph。"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from agent.graph.nodes import design_flow, output_flow, parse_swagger
from agent.graph.state import FlowState


def build_flow_graph():
    """构建 E2E 流程图。"""
    graph = StateGraph(FlowState)

    graph.add_node("parse_swagger", parse_swagger)
    graph.add_node("design_flow", design_flow)
    graph.add_node("output_flow", output_flow)

    graph.set_entry_point("parse_swagger")
    graph.add_edge("parse_swagger", "design_flow")
    graph.add_edge("design_flow", "output_flow")
    graph.add_edge("output_flow", END)

    return graph.compile()
