# -*- coding: utf-8 -*-
"""Claude tool_use 工具定义，强制 LLM 输出结构化 JSON。"""

# 提取 API 接口信息的工具
TOOL_EXTRACT_API_ENDPOINTS = {
    "name": "extract_api_endpoints",
    "description": "从文档或文字描述中提取 API 接口信息，输出标准化的接口定义。",
    "input_schema": {
        "type": "object",
        "properties": {
            "endpoints": {
                "type": "array",
                "description": "提取到的接口列表",
                "items": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "接口路径"},
                        "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"]},
                        "summary": {"type": "string", "description": "接口摘要（中文）"},
                        "description": {"type": "string", "description": "接口详细描述"},
                        "base_url": {"type": "string", "description": "基础地址"},
                        "auth_type": {"type": "string", "enum": ["bearer", "none"]},
                        "request_body_type": {"type": "string", "enum": ["json", "form-data", "file"]},
                        "request_body_is_array": {"type": "boolean", "description": "请求体是否为数组"},
                        "request_body": {
                            "type": "array",
                            "description": "请求体参数",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "type": {"type": "string"},
                                    "required": {"type": "boolean"},
                                    "description": {"type": "string"},
                                    "enum": {"type": "array", "items": {"type": "string"}},
                                    "example": {},
                                    "uncertain": {"type": "boolean"},
                                },
                                "required": ["name", "type"],
                            },
                        },
                        "query_params": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "type": {"type": "string"},
                                    "required": {"type": "boolean"},
                                    "description": {"type": "string"},
                                },
                                "required": ["name", "type"],
                            },
                        },
                        "tags": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["path", "method", "summary"],
                },
            },
        },
        "required": ["endpoints"],
    },
}

# 生成测试用例的工具
TOOL_GENERATE_TEST_CASES = {
    "name": "generate_test_cases",
    "description": "生成 API 接口的测试用例列表。",
    "input_schema": {
        "type": "object",
        "properties": {
            "cases": {
                "type": "array",
                "description": "测试用例列表",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "测试函数名，如 test_add_quota"},
                        "description": {"type": "string", "description": "测试描述（中文）"},
                        "category": {"type": "string", "enum": ["normal", "abnormal", "boundary"]},
                        "priority": {"type": "string", "enum": ["P0", "P1", "P2", "P3"]},
                        "endpoint_path": {"type": "string"},
                        "method": {"type": "string"},
                        "request_data": {"description": "请求数据，可以是 object 或 array"},
                        "expected_status": {"type": "integer"},
                        "expected_response": {"type": "object", "description": "期望响应中的键值对"},
                        "setup_description": {"type": "string"},
                        "uncertain": {"type": "boolean"},
                    },
                    "required": ["name", "description", "category", "request_data", "expected_status"],
                },
            },
        },
        "required": ["cases"],
    },
}

# 构建 E2E 流程的工具
TOOL_BUILD_FLOW_DEFINITION = {
    "name": "build_flow_definition",
    "description": "根据业务流程描述，设计 API 调用链。",
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "流程名称"},
            "description": {"type": "string", "description": "流程描述（中文）"},
            "base_url": {"type": "string"},
            "steps": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "step_number": {"type": "integer"},
                        "endpoint_path": {"type": "string"},
                        "method": {"type": "string"},
                        "description": {"type": "string"},
                        "request_data": {"description": "请求数据模板"},
                        "input_mapping": {
                            "type": "object",
                            "description": "字段映射: {字段名: '$.steps[N].response.字段路径'}",
                        },
                        "extract_fields": {
                            "type": "object",
                            "description": "提取字段: {变量名: 'jsonpath'}",
                        },
                        "expected_status": {"type": "integer"},
                        "assertions": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["step_number", "endpoint_path", "method", "description"],
                },
            },
        },
        "required": ["name", "description", "steps"],
    },
}
