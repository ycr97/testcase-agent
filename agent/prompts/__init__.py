"""Prompt 模板集合。"""

from agent.prompts.extraction import EXTRACT_FROM_TEXT
from agent.prompts.flow_design import DESIGN_FLOW
from agent.prompts.gap_analysis import ANALYZE_GAPS
from agent.prompts.generation import (
    GENERATE_ABNORMAL_CASES,
    GENERATE_BOUNDARY_CASES,
    GENERATE_NORMAL_CASES,
)

__all__ = [
    "ANALYZE_GAPS",
    "DESIGN_FLOW",
    "EXTRACT_FROM_TEXT",
    "GENERATE_ABNORMAL_CASES",
    "GENERATE_BOUNDARY_CASES",
    "GENERATE_NORMAL_CASES",
]
