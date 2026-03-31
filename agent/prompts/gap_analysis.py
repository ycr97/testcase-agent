"""缺失用例分析 Prompt。"""

from langchain_core.prompts import ChatPromptTemplate

SYSTEM_GAP_ANALYZER = """你是一个测试覆盖率分析专家。你的任务是分析已有的测试代码，找出未覆盖的测试场景。

分析维度：
1. 正常场景：是否覆盖了所有业务操作类型
2. 异常场景：无效参数、缺失必填字段、越权访问、无效枚举值
3. 边界场景：空值、零值、最大/最小值、特殊字符、超长字符串
4. 并发/批量场景：批量操作的边界

输出时只列出【缺失的】场景，不要重复已有的测试用例。
每个用例都必须包含 endpoint_path 和 method 字段。"""

ANALYZE_GAPS = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_GAP_ANALYZER),
        (
            "human",
            """请分析以下已有的测试代码，找出未覆盖的测试场景。

已有测试代码：
```python
{existing_code}
```

API 接口信息：
{endpoint_json}

注意：
- 只输出【缺失的】测试用例
- 不要重复已有的测试名称或场景
- endpoint_path 必须与接口 path 一致
- method 必须与接口 method 一致""",
        ),
    ]
)
