# -*- coding: utf-8 -*-
"""LLM 驱动的测试用例生成器（三轮生成策略）"""

from __future__ import annotations

import json
import logging

from agent.schemas.api_schema import APIEndpoint
from agent.schemas.test_case import TestCase, TestSuite
from agent.llm.client import LLMClient
from agent.llm.prompts import (
    SYSTEM_CASE_GENERATOR,
    SYSTEM_GAP_ANALYZER,
    PROMPT_GENERATE_NORMAL_CASES,
    PROMPT_GENERATE_ABNORMAL_CASES,
    PROMPT_GENERATE_BOUNDARY_CASES,
    PROMPT_ANALYZE_GAPS,
)
from agent.llm.tools import TOOL_GENERATE_TEST_CASES

logger = logging.getLogger(__name__)


class CaseGenerator:
    """三轮生成策略：正常 → 异常 → 边界，每轮独立调用 LLM。"""

    def __init__(self, llm_client: LLMClient | None = None):
        self._llm = llm_client or LLMClient()

    def generate(self, endpoint: APIEndpoint, categories: list[str] | None = None) -> TestSuite:
        """
        为单个接口生成测试用例。

        Args:
            endpoint: 标准化的接口定义
            categories: 要生成的类别列表，默认全部 ["normal", "abnormal", "boundary"]
        """
        if categories is None:
            categories = ["normal", "abnormal", "boundary"]

        endpoint_json = endpoint.model_dump_json(indent=2, exclude_none=True)
        all_cases: list[TestCase] = []

        prompt_map = {
            "normal": PROMPT_GENERATE_NORMAL_CASES,
            "abnormal": PROMPT_GENERATE_ABNORMAL_CASES,
            "boundary": PROMPT_GENERATE_BOUNDARY_CASES,
        }

        for category in categories:
            prompt_template = prompt_map.get(category)
            if not prompt_template:
                continue

            logger.info(f"生成 {category} 场景用例...")
            cases = self._generate_round(
                prompt_template.format(endpoint_json=endpoint_json),
                endpoint.path,
                endpoint.method,
            )
            all_cases.extend(cases)
            logger.info(f"  -> 生成 {len(cases)} 个 {category} 用例")

        return TestSuite(
            endpoint_path=endpoint.path,
            endpoint_summary=endpoint.summary,
            base_url=endpoint.base_url,
            cases=all_cases,
        )

    def analyze_gaps(
        self, endpoint: APIEndpoint, existing_code: str
    ) -> list[TestCase]:
        """
        分析已有代码，生成缺失的测试用例。

        Args:
            endpoint: 接口定义
            existing_code: 已有的测试代码
        """
        endpoint_json = endpoint.model_dump_json(indent=2, exclude_none=True)
        prompt = PROMPT_ANALYZE_GAPS.format(
            existing_code=existing_code,
            endpoint_json=endpoint_json,
        )

        logger.info("分析已有代码，查找缺失用例...")
        cases = self._generate_round(prompt, endpoint.path, endpoint.method, system=SYSTEM_GAP_ANALYZER)
        logger.info(f"  -> 发现 {len(cases)} 个缺失用例")
        return cases

    def _generate_round(
        self,
        prompt: str,
        endpoint_path: str,
        method: str,
        system: str = SYSTEM_CASE_GENERATOR,
    ) -> list[TestCase]:
        """单轮生成。"""
        result = self._llm.chat_with_tools(
            messages=[{"role": "user", "content": prompt}],
            tools=[TOOL_GENERATE_TEST_CASES],
            system=system,
            tool_choice={"type": "tool", "name": "generate_test_cases"},
        )

        if not result:
            return []

        cases = []
        for case_data in result.get("cases", []):
            # 补全缺失字段
            case_data.setdefault("endpoint_path", endpoint_path)
            case_data.setdefault("method", method)
            case_data.setdefault("priority", "P1")
            try:
                cases.append(TestCase(**case_data))
            except Exception as e:
                logger.warning(f"用例解析失败: {e}, data={json.dumps(case_data, ensure_ascii=False)[:200]}")

        return cases
