# -*- coding: utf-8 -*-
"""E2E 流程编排器"""

from __future__ import annotations

import json
import logging

from agent.schemas.api_schema import APIEndpoint
from agent.schemas.flow import FlowDefinition, FlowStep
from agent.llm.client import LLMClient
from agent.llm.prompts import SYSTEM_FLOW_DESIGNER, PROMPT_DESIGN_FLOW
from agent.llm.tools import TOOL_BUILD_FLOW_DEFINITION

logger = logging.getLogger(__name__)


class FlowBuilder:
    """根据业务描述和可用接口，构建 E2E 测试流程。"""

    def __init__(self, llm_client: LLMClient | None = None):
        self._llm = llm_client or LLMClient()

    def build(
        self, endpoints: list[APIEndpoint], flow_description: str, base_url: str = ""
    ) -> FlowDefinition:
        """
        构建 E2E 测试流程。

        Args:
            endpoints: 可用的接口列表
            flow_description: 中文业务流程描述
            base_url: 基础地址
        """
        endpoints_json = json.dumps(
            [ep.model_dump(exclude_none=True) for ep in endpoints],
            ensure_ascii=False,
            indent=2,
        )

        prompt = PROMPT_DESIGN_FLOW.format(
            flow_description=flow_description,
            endpoints_json=endpoints_json,
        )

        logger.info(f"设计 E2E 流程: {flow_description[:50]}...")
        result = self._llm.chat_with_tools(
            messages=[{"role": "user", "content": prompt}],
            tools=[TOOL_BUILD_FLOW_DEFINITION],
            system=SYSTEM_FLOW_DESIGNER,
            tool_choice={"type": "tool", "name": "build_flow_definition"},
        )

        if not result:
            raise ValueError("LLM 未能生成流程定义")

        steps = []
        for step_data in result.get("steps", []):
            steps.append(FlowStep(**step_data))

        flow = FlowDefinition(
            name=result.get("name", "test_flow"),
            description=result.get("description", flow_description),
            base_url=base_url or result.get("base_url", ""),
            steps=steps,
        )

        logger.info(f"  -> 生成 {len(steps)} 步流程")
        return flow
