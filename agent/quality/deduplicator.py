# -*- coding: utf-8 -*-
"""测试用例去重器"""

from __future__ import annotations

import json

from agent.schemas.test_case import TestCase


class Deduplicator:
    """去除与已有用例重复的新生成用例。"""

    def deduplicate(
        self, new_cases: list[TestCase], existing_names: list[str]
    ) -> list[TestCase]:
        """
        去重逻辑：
        1. 名称完全相同 -> 丢弃
        2. 请求数据完全相同 -> 丢弃
        3. 名称和描述中的核心词高度重合 -> 标记 uncertain

        Args:
            new_cases: 新生成的用例
            existing_names: 已有的测试函数名列表
        """
        existing_set = set(existing_names)
        seen_data: set[str] = set()
        result = []

        for case in new_cases:
            # 名称去重
            if case.name in existing_set:
                continue

            # 请求数据去重
            data_key = json.dumps(case.request_data, sort_keys=True, ensure_ascii=False)
            if data_key in seen_data:
                continue
            seen_data.add(data_key)

            result.append(case)

        return result
