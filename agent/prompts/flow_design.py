"""E2E 流程设计 Prompt。"""

from langchain_core.prompts import ChatPromptTemplate

SYSTEM_FLOW_DESIGNER = """你是一个端到端测试设计专家。你的任务是根据业务流程描述和可用的 API 接口，设计 API 调用链。

要求：
1. 确定正确的调用顺序
2. 明确步骤间的数据依赖关系（前一步的响应如何传递给下一步）
3. 每一步都需要指定断言条件
4. 用中文描述每个步骤"""

DESIGN_FLOW = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_FLOW_DESIGNER),
        (
            "human",
            """请根据以下业务流程描述和可用接口，设计 API 调用链。

业务流程描述：
{flow_description}

可用接口列表：
{endpoints_json}

输出要求：
- steps 按执行顺序排列
- step_number 从 1 开始递增
- method 使用大写 HTTP 方法
- assertions 使用中文""",
        ),
    ]
)
