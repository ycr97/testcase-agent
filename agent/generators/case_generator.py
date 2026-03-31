# -*- coding: utf-8 -*-
"""LLM 驱动的测试用例生成器（三轮生成策略）"""

from __future__ import annotations

import logging

from agent.models.factory import create_llm
from agent.prompts.gap_analysis import ANALYZE_GAPS
from agent.prompts.generation import (
    GENERATE_ABNORMAL_CASES,
    GENERATE_BOUNDARY_CASES,
    GENERATE_NORMAL_CASES,
)
from agent.schemas.api_schema import APIEndpoint
from agent.schemas.llm_output import GeneratedCases
from agent.schemas.test_case import TestCase, TestSuite

logger = logging.getLogger(__name__)


class CaseGenerator:
    """三轮生成策略：正常 → 异常 → 边界，每轮独立调用 LLM。"""

    def __init__(self, llm=None):
        self._llm = llm

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
            "normal": GENERATE_NORMAL_CASES,
            "abnormal": GENERATE_ABNORMAL_CASES,
            "boundary": GENERATE_BOUNDARY_CASES,
        }
        structured_llm = (self._llm or create_llm()).with_structured_output(
            GeneratedCases
        ).with_retry(stop_after_attempt=3)

        for category in categories:
            prompt_template = prompt_map.get(category)
            if not prompt_template:
                continue

            logger.info(f"生成 {category} 场景用例...")
            cases = self._generate_round(
                structured_llm,
                prompt_template.invoke({"endpoint_json": endpoint_json}),
                endpoint,
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
        logger.info("分析已有代码，查找缺失用例...")
        structured_llm = (self._llm or create_llm()).with_structured_output(
            GeneratedCases
        ).with_retry(stop_after_attempt=3)
        cases = self._generate_round(
            structured_llm,
            ANALYZE_GAPS.invoke(
                {
                    "existing_code": existing_code,
                    "endpoint_json": endpoint_json,
                }
            ),
            endpoint,
        )
        logger.info(f"  -> 发现 {len(cases)} 个缺失用例")
        return cases

    def _generate_round(
        self,
        structured_llm,
        prompt,
        endpoint: APIEndpoint,
    ) -> list[TestCase]:
        """单轮生成。"""
        result: GeneratedCases = structured_llm.invoke(prompt)

        cases = []
        for case in result.cases:
            try:
                case.endpoint_path = endpoint.path
                case.method = endpoint.method
                cases.append(case)
            except Exception as e:
                logger.warning(
                    "用例解析失败: %s, name=%s",
                    e,
                    getattr(case, "name", "<unknown>"),
                )

        return cases
