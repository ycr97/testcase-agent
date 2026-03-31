# -*- coding: utf-8 -*-
"""所有提示词模板"""

# ========== 系统提示词 ==========

SYSTEM_API_EXTRACTOR = """你是一个 API 文档分析专家。你的任务是从用户提供的文档或文字描述中，精确提取 API 接口信息。

要求：
1. 提取所有能识别的接口信息：路径、方法、参数、类型、是否必填、描述等
2. 如果某个信息不确定或缺失，将该字段的 uncertain 标记为 true，不要猜测
3. 保留中文描述原文
4. 参数类型使用: string, integer, number, boolean, array, object
5. 如果请求体是数组格式（如 [{}]），将 request_body_is_array 设为 true"""

SYSTEM_CASE_GENERATOR = """你是一个资深测试工程师，专注于 API 接口测试用例设计。

你需要根据 API 接口定义生成测试用例，要求：
1. 每个测试用例必须有明确的测试目标和期望结果
2. 测试数据要贴近真实业务场景（中文数据）
3. 函数名使用 test_ 前缀 + 英文下划线命名
4. 描述使用中文
5. 测试用例要具有可执行性"""

SYSTEM_GAP_ANALYZER = """你是一个测试覆盖率分析专家。你的任务是分析已有的测试代码，找出未覆盖的测试场景。

分析维度：
1. 正常场景：是否覆盖了所有业务操作类型
2. 异常场景：无效参数、缺失必填字段、越权访问、无效枚举值
3. 边界场景：空值、零值、最大/最小值、特殊字符、超长字符串
4. 并发/批量场景：批量操作的边界

输出时只列出【缺失的】场景，不要重复已有的测试用例。"""

SYSTEM_FLOW_DESIGNER = """你是一个端到端测试设计专家。你的任务是根据业务流程描述和可用的 API 接口，设计 API 调用链。

要求：
1. 确定正确的调用顺序
2. 明确步骤间的数据依赖关系（前一步的响应如何传递给下一步）
3. 每一步都需要指定断言条件
4. 用中文描述每个步骤"""

# ========== 用户提示词模板 ==========

PROMPT_EXTRACT_FROM_TEXT = """请从以下文字描述中提取 API 接口信息，调用 extract_api_endpoints 工具输出结果。

文字描述：
{text}"""

PROMPT_GENERATE_NORMAL_CASES = """请为以下 API 接口生成【正常场景】测试用例，调用 generate_test_cases 工具输出。

API 接口信息：
{endpoint_json}

要求：
- 覆盖所有正常业务操作
- 使用贴近真实的中文测试数据
- 每个用例的 category 为 "normal"
- 优先级为 P0 或 P1"""

PROMPT_GENERATE_ABNORMAL_CASES = """请为以下 API 接口生成【异常场景】测试用例，调用 generate_test_cases 工具输出。

API 接口信息：
{endpoint_json}

要求生成以下类型的异常用例：
- 缺失必填字段（逐个字段缺失）
- 字段类型错误（如字符串传数字、数字传字符串）
- 无效枚举值（如 operationType 传 "INVALID"）
- 空请求体
- 未授权访问（无 token 或无效 token）
- 每个用例的 category 为 "abnormal"
- 优先级为 P1 或 P2"""

PROMPT_GENERATE_BOUNDARY_CASES = """请为以下 API 接口生成【边界场景】测试用例，调用 generate_test_cases 工具输出。

API 接口信息：
{endpoint_json}

要求生成以下类型的边界用例：
- 空字符串 ""
- 超长字符串（如 1000 个字符）
- 数值字段：0、负数、极大值
- 特殊字符：SQL注入片段、XSS片段、中文特殊字符
- 数组场景：空数组、单元素、大量元素
- 每个用例的 category 为 "boundary"
- 优先级为 P2 或 P3"""

PROMPT_ANALYZE_GAPS = """请分析以下已有的测试代码，找出未覆盖的测试场景，调用 generate_test_cases 工具输出缺失的用例。

已有测试代码：
```python
{existing_code}
```

API 接口信息：
{endpoint_json}

注意：只输出【缺失的】测试用例，不要重复已有的。"""

PROMPT_DESIGN_FLOW = """请根据以下业务流程描述和可用接口，设计 API 调用链，调用 build_flow_definition 工具输出。

业务流程描述：
{flow_description}

可用接口列表：
{endpoints_json}"""
