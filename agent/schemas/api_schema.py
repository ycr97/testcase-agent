# -*- coding: utf-8 -*-
"""API 接口的标准化数据模型，所有解析器输出此格式，所有生成器消费此格式。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class APIParameter(BaseModel):
    """接口参数定义"""
    name: str = Field(..., description="参数名称")
    type: str = Field("string", description="参数类型: string/integer/number/boolean/array/object")
    required: bool = Field(True, description="是否必填")
    description: str = Field("", description="参数描述（中文）")
    enum: list[str] | None = Field(None, description="枚举值列表")
    example: str | int | float | bool | None = Field(None, description="示例值")
    constraints: dict = Field(default_factory=dict, description="约束: min, max, minLength, maxLength, pattern 等")
    children: list[APIParameter] = Field(default_factory=list, description="嵌套子参数（type=object/array 时）")
    uncertain: bool = Field(False, description="是否为不确定字段，需人工确认")


class APIEndpoint(BaseModel):
    """标准化的 API 接口定义"""
    path: str = Field(..., description="接口路径，如 /FulfillmentOrderContext/SubMerchantQuota/adjustQuota/v1")
    method: str = Field("POST", description="HTTP 方法: GET/POST/PUT/DELETE")
    summary: str = Field("", description="接口摘要（中文）")
    description: str = Field("", description="接口详细描述")
    base_url: str = Field("", description="基础地址，如 https://rsp-uat.yuhong.com.cn/api/middle-promotion-center")
    headers: dict[str, str] = Field(default_factory=dict, description="额外请求头")
    auth_type: str = Field("bearer", description="认证方式: bearer/none")
    request_body: list[APIParameter] = Field(default_factory=list, description="请求体参数列表")
    request_body_type: str = Field("json", description="请求体类型: json/form-data/file")
    request_body_is_array: bool = Field(False, description="请求体是否为数组（如 adjustQuota 接口）")
    query_params: list[APIParameter] = Field(default_factory=list, description="查询参数列表")
    path_params: list[APIParameter] = Field(default_factory=list, description="路径参数列表")
    response_schema: dict = Field(default_factory=dict, description="响应体结构")
    tags: list[str] = Field(default_factory=list, description="业务标签")

    @property
    def full_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/{self.path.lstrip('/')}" if self.base_url else self.path


class APIDocument(BaseModel):
    """一组 API 接口的集合"""
    title: str = Field("", description="文档标题")
    description: str = Field("", description="文档描述")
    endpoints: list[APIEndpoint] = Field(default_factory=list, description="接口列表")
