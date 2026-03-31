# -*- coding: utf-8 -*-
"""测试用例质量校验器"""

from __future__ import annotations

import logging

from agent.schemas.api_schema import APIEndpoint
from agent.schemas.test_case import TestCase

logger = logging.getLogger(__name__)


class Validator:
    """校验生成的测试用例是否符合 API schema。"""

    def validate(self, cases: list[TestCase], endpoint: APIEndpoint) -> list[TestCase]:
        """
        校验并过滤无效用例。

        Returns:
            通过校验的用例列表
        """
        valid_fields = {p.name for p in endpoint.request_body}
        valid_cases = []

        for case in cases:
            issues = self._check_case(case, valid_fields, endpoint)
            if issues:
                logger.warning(f"用例 {case.name} 校验问题: {issues}")
                # 标记为需确认但不丢弃
                case.uncertain = True
            valid_cases.append(case)

        return valid_cases

    def _check_case(
        self, case: TestCase, valid_fields: set[str], endpoint: APIEndpoint
    ) -> list[str]:
        issues = []

        # 检查正常用例的请求字段
        if case.category == "normal":
            if isinstance(case.request_data, dict):
                unknown = set(case.request_data.keys()) - valid_fields
                if unknown and valid_fields:  # 只在有已知字段时检查
                    issues.append(f"未知字段: {unknown}")

            # 检查必填字段
            required = {p.name for p in endpoint.request_body if p.required}
            if isinstance(case.request_data, dict):
                missing = required - set(case.request_data.keys())
                if missing:
                    issues.append(f"缺少必填字段: {missing}")
            elif isinstance(case.request_data, list) and case.request_data:
                first = case.request_data[0] if isinstance(case.request_data[0], dict) else {}
                missing = required - set(first.keys())
                if missing:
                    issues.append(f"缺少必填字段: {missing}")

        return issues
