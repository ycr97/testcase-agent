# -*- coding: utf-8 -*-
"""端到端测试流程的数据模型"""

from __future__ import annotations

from pydantic import BaseModel, Field


class FlowStep(BaseModel):
    """E2E 流程中的一个步骤"""
    step_number: int = Field(..., description="步骤序号")
    endpoint_path: str = Field(..., description="接口路径")
    method: str = Field("POST", description="HTTP 方法")
    description: str = Field(..., description="步骤描述（中文）")
    request_data: dict | list = Field(default_factory=dict, description="请求数据模板")
    input_mapping: dict[str, str] = Field(
        default_factory=dict,
        description="字段映射：{本步骤字段: '$.steps[N].response.字段路径'}",
    )
    extract_fields: dict[str, str] = Field(
        default_factory=dict,
        description="从响应中提取的字段：{变量名: 'jsonpath 表达式'}",
    )
    expected_status: int = Field(200, description="期望状态码")
    assertions: list[str] = Field(default_factory=list, description="断言描述列表")


class FlowDefinition(BaseModel):
    """E2E 流程定义"""
    name: str = Field(..., description="流程名称，如 test_flow_create_and_adjust_quota")
    description: str = Field(..., description="流程描述（中文）")
    base_url: str = Field("", description="基础地址")
    steps: list[FlowStep] = Field(default_factory=list, description="步骤列表")
