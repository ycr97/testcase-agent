# -*- coding: utf-8 -*-
"""测试用例的数据模型"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class TestCategory(str, Enum):
    NORMAL = "normal"
    ABNORMAL = "abnormal"
    BOUNDARY = "boundary"


class TestPriority(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class TestCase(BaseModel):
    """单个测试用例规格"""
    name: str = Field(..., description="测试函数名，如 test_add_quota")
    description: str = Field(..., description="测试描述（中文）")
    category: TestCategory = Field(..., description="用例类别: normal/abnormal/boundary")
    priority: TestPriority = Field(TestPriority.P1, description="优先级 P0-P3")
    endpoint_path: str = Field(..., description="接口路径")
    method: str = Field("POST", description="HTTP 方法")
    request_data: dict | list = Field(..., description="请求数据")
    expected_status: int = Field(200, description="期望 HTTP 状态码")
    expected_response: dict = Field(default_factory=dict, description="期望响应中包含的键值对")
    setup_description: str = Field("", description="前置条件描述")
    teardown_description: str = Field("", description="后置操作描述")
    uncertain: bool = Field(False, description="是否需要人工确认")


class TestSuite(BaseModel):
    """测试套件：一个接口的所有测试用例"""
    endpoint_path: str = Field(..., description="接口路径")
    endpoint_summary: str = Field("", description="接口摘要")
    base_url: str = Field("", description="基础地址")
    auth_type: str = Field("bearer", description="认证方式")
    cases: list[TestCase] = Field(default_factory=list, description="测试用例列表")

    @property
    def normal_cases(self) -> list[TestCase]:
        return [c for c in self.cases if c.category == TestCategory.NORMAL]

    @property
    def abnormal_cases(self) -> list[TestCase]:
        return [c for c in self.cases if c.category == TestCategory.ABNORMAL]

    @property
    def boundary_cases(self) -> list[TestCase]:
        return [c for c in self.cases if c.category == TestCategory.BOUNDARY]
