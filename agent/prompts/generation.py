"""测试用例生成 Prompt。"""

from langchain_core.prompts import ChatPromptTemplate

SYSTEM_CASE_GENERATOR = """你是一个资深测试工程师，专注于 API 接口测试用例设计。

你需要根据 API 接口定义生成测试用例，要求：
1. 每个测试用例必须有明确的测试目标和期望结果
2. 测试数据要贴近真实业务场景（中文数据）
3. 函数名使用 test_ 前缀 + 英文下划线命名
4. 描述使用中文
5. 测试用例要具有可执行性
6. 每个用例都要带上 endpoint_path 和 method 字段"""

GENERATE_NORMAL_CASES = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_CASE_GENERATOR),
        (
            "human",
            """请为以下 API 接口生成【正常场景】测试用例。

API 接口信息：
{endpoint_json}

要求：
- 覆盖所有正常业务操作
- 使用贴近真实的中文测试数据
- 每个用例的 category 为 "normal"
- 优先级为 P0 或 P1
- endpoint_path 必须与接口 path 一致
- method 必须与接口 method 一致""",
        ),
    ]
)

GENERATE_ABNORMAL_CASES = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_CASE_GENERATOR),
        (
            "human",
            """请为以下 API 接口生成【异常场景】测试用例。

API 接口信息：
{endpoint_json}

要求生成以下类型的异常用例：
- 缺失必填字段（逐个字段缺失）
- 字段类型错误（如字符串传数字、数字传字符串）
- 无效枚举值
- 空请求体
- 未授权访问（无 token 或无效 token）
- 每个用例的 category 为 "abnormal"
- 优先级为 P1 或 P2
- endpoint_path 必须与接口 path 一致
- method 必须与接口 method 一致""",
        ),
    ]
)

GENERATE_BOUNDARY_CASES = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_CASE_GENERATOR),
        (
            "human",
            """请为以下 API 接口生成【边界场景】测试用例。

API 接口信息：
{endpoint_json}

要求生成以下类型的边界用例：
- 空字符串 ""
- 超长字符串（如 1000 个字符）
- 数值字段：0、负数、极大值
- 特殊字符：SQL 注入片段、XSS 片段、中文特殊字符
- 数组场景：空数组、单元素、大量元素
- 每个用例的 category 为 "boundary"
- 优先级为 P2 或 P3
- endpoint_path 必须与接口 path 一致
- method 必须与接口 method 一致""",
        ),
    ]
)
