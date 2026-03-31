"""LLM 结构化输出中间模型。"""

from __future__ import annotations

from pydantic import BaseModel, Field

from agent.schemas.api_schema import APIEndpoint
from agent.schemas.flow import FlowStep
from agent.schemas.test_case import TestCase


class ExtractedEndpoints(BaseModel):
    """LLM 提取的接口列表。"""

    endpoints: list[APIEndpoint] = Field(default_factory=list)


class GeneratedCases(BaseModel):
    """LLM 生成的测试用例列表。"""

    cases: list[TestCase] = Field(default_factory=list)


class DesignedFlow(BaseModel):
    """LLM 设计的流程定义。"""

    name: str
    description: str
    base_url: str = ""
    steps: list[FlowStep] = Field(default_factory=list)
