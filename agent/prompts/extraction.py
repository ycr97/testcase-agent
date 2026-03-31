"""API 提取相关 Prompt。"""

from langchain_core.prompts import ChatPromptTemplate

SYSTEM_API_EXTRACTOR = """你是一个 API 文档分析专家。你的任务是从用户提供的文档或文字描述中，精确提取 API 接口信息。

要求：
1. 提取所有能识别的接口信息：路径、方法、参数、类型、是否必填、描述等
2. 如果某个信息不确定或缺失，将该字段的 uncertain 标记为 true，不要猜测
3. 保留中文描述原文
4. 参数类型使用: string, integer, number, boolean, array, object
5. 如果请求体是数组格式（如 [{}]），将 request_body_is_array 设为 true"""

EXTRACT_FROM_TEXT = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_API_EXTRACTOR),
        (
            "human",
            """请从以下文字描述中提取 API 接口信息。

文字描述：
{text}

输出要求：
- 返回 endpoints 列表
- method 使用大写 HTTP 方法
- summary 使用中文
- 若无法确认，使用 uncertain 标记字段""",
        ),
    ]
)
