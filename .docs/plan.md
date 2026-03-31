# testcase-agent 迁移重构方案：Anthropic SDK → LangChain/LangGraph

## 一、迁移目标

1. **多模型支持** — 从 Claude 单一绑定扩展为支持 OpenAI / Claude / 本地模型可切换
2. **图编排引擎** — 用 LangGraph 状态图替代硬编码线性流程，支持条件分支、循环重试
3. **结构化输出简化** — 用 Pydantic + `with_structured_output()` 替代手写 JSON Schema
4. **可观测性** — 集成 LangSmith 实现全链路 trace / eval
5. **保持轻量** — 只引入 `langgraph` + `langchain-core` + 模型 provider 包，不引入 LangChain 全家桶

## 二、技术选型

| 组件 | 当前 | 迁移后 |
|------|------|--------|
| LLM 调用 | `anthropic` SDK 直调 | `langchain-anthropic` / `langchain-openai`（通过 `ChatModel` 统一接口） |
| 结构化输出 | 手写 JSON Schema（`llm/tools.py` 136 行） | `model.with_structured_output(PydanticModel)` |
| 重试/容错 | `LLMClient._call_with_retry` 手动实现 | `model.with_retry()` + LangGraph 内置 retry |
| 流程编排 | `cli.py` 线性串联 | LangGraph `StateGraph` 有向图 |
| Prompt 管理 | Python 字符串模板（`llm/prompts.py`） | `ChatPromptTemplate` |
| 配置管理 | `config.py` + `settings.yaml` | 保持不变，新增 provider 切换逻辑 |
| 可观测性 | logging | LangSmith tracing + logging |

### 核心依赖

```toml
dependencies = [
    "langgraph>=0.4",
    "langchain-core>=0.3",
    "langchain-anthropic>=0.3",
    "langchain-openai>=0.3",       # 可选，按需启用
    "pydantic>=2.0",
    "pyyaml>=6.0",
    "python-docx>=1.0",
    "jinja2>=3.1",
    "click>=8.1",
    "requests>=2.31",
]
```

## 三、迁移后项目结构

```
testcase-agent/
├── agent/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py                          # CLI 入口（保持 click）
│   ├── config.py                       # 配置管理（扩展 provider 支持）
│   │
│   ├── models/                         # [新] LLM 工厂
│   │   ├── __init__.py
│   │   └── factory.py                  # 根据 config 创建 ChatModel 实例
│   │
│   ├── schemas/                        # [保留] Pydantic 数据模型
│   │   ├── api_schema.py               # APIEndpoint, APIDocument（不变）
│   │   ├── test_case.py                # TestCase, TestSuite（不变）
│   │   └── flow.py                     # FlowDefinition, FlowStep（不变）
│   │
│   ├── parsers/                        # [保留] 文档解析器
│   │   ├── base.py
│   │   ├── swagger_parser.py
│   │   ├── text_parser.py
│   │   ├── markdown_parser.py
│   │   ├── word_parser.py
│   │   └── code_analyzer.py
│   │
│   ├── prompts/                        # [重构] Prompt 模板
│   │   ├── __init__.py
│   │   ├── extraction.py               # API 提取 prompt
│   │   ├── generation.py               # 用例生成 prompt（normal/abnormal/boundary）
│   │   ├── gap_analysis.py             # 缺失用例分析 prompt
│   │   └── flow_design.py              # E2E 流程设计 prompt
│   │
│   ├── graph/                          # [新] LangGraph 核心
│   │   ├── __init__.py
│   │   ├── state.py                    # 状态定义（TypedDict）
│   │   ├── nodes/                      # 图节点
│   │   │   ├── __init__.py
│   │   │   ├── parse_input.py          # 解析输入文档
│   │   │   ├── generate_cases.py       # LLM 生成测试用例
│   │   │   ├── validate_cases.py       # 质量校验
│   │   │   ├── deduplicate.py          # 去重
│   │   │   ├── generate_code.py        # 代码生成
│   │   │   └── design_flow.py          # E2E 流程设计
│   │   ├── edges.py                    # 条件边（路由逻辑）
│   │   ├── generate_graph.py           # generate 命令的图
│   │   ├── analyze_graph.py            # analyze 命令的图
│   │   └── flow_graph.py               # flow 命令的图
│   │
│   ├── generators/                     # [保留] 代码生成
│   │   ├── code_generator.py           # Jinja2 渲染（不变）
│   │   └── templates/
│   │       └── test_file.py.j2
│   │
│   ├── quality/                        # [保留] 质量模块
│   │   ├── validator.py                # 校验逻辑（不变）
│   │   └── deduplicator.py             # 去重逻辑（不变）
│   │
│   └── runner/                         # [保留] 测试执行
│       ├── executor.py
│       └── reporter.py
│
├── config/
│   └── settings.yaml                   # 扩展 provider 配置
├── generated_tests/
└── pyproject.toml
```

### 变更总结

| 模块 | 操作 | 说明 |
|------|------|------|
| `llm/` | **删除** | `client.py` → `models/factory.py`，`tools.py` → 删除（Pydantic 替代），`prompts.py` → `prompts/` |
| `models/` | **新增** | LLM 工厂，统一创建 ChatModel |
| `prompts/` | **重构** | 从单文件拆分为模块，使用 `ChatPromptTemplate` |
| `graph/` | **新增** | LangGraph 状态图，替代 `cli.py` 中的线性编排和 `orchestrator/` |
| `orchestrator/` | **删除** | `flow_builder.py` → `graph/nodes/design_flow.py`，`dependency_resolver.py` → 合并到图节点 |
| `schemas/` | **保留** | 数据模型完全不变，同时复用为结构化输出的 schema |
| `parsers/` | **保留** | 解析器不变 |
| `generators/` | **保留** | 代码生成不变 |
| `quality/` | **保留** | 校验和去重不变 |
| `runner/` | **保留** | 执行和报告不变 |
| `config.py` | **扩展** | 新增 `provider` 字段支持多模型 |
| `cli.py` | **简化** | 从业务编排逻辑简化为：解析参数 → 调用 graph → 输出结果 |

## 四、分阶段迁移计划

### Phase 1：基础层替换（LLM 调用统一）

**目标**：用 LangChain ChatModel 替换 Anthropic SDK 直调，跑通现有功能

**改动文件**：

#### 1.1 新增 `agent/models/factory.py`

```python
"""LLM 工厂：根据配置创建 ChatModel 实例"""
from langchain_core.language_models import BaseChatModel
from agent.config import get_settings

def create_llm() -> BaseChatModel:
    settings = get_settings()
    provider = settings.llm.provider

    common_kwargs = {
        "temperature": settings.llm.temperature,
        "max_tokens": settings.llm.max_tokens,
    }

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=settings.llm.model,
            api_key=settings.llm.api_key,
            **common_kwargs,
        )
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=settings.llm.model,
            api_key=settings.llm.api_key,
            **common_kwargs,
        )
    else:
        raise ValueError(f"不支持的 LLM provider: {provider}")
```

#### 1.2 扩展 `config/settings.yaml`

```yaml
llm:
  provider: anthropic          # anthropic / openai
  model: claude-sonnet-4-20250514
  max_tokens: 4096
  temperature: 0.0
  # 如果 provider: openai，配置：
  # model: gpt-4o
  # api_key 通过 OPENAI_API_KEY 或 ANTHROPIC_API_KEY 环境变量设置
```

#### 1.3 扩展 `agent/config.py`

```python
# get_settings() 中 api_key 读取逻辑改为：
api_key = os.environ.get(
    "ANTHROPIC_API_KEY" if provider == "anthropic" else "OPENAI_API_KEY",
    llm_raw.get("api_key", ""),
)
```

#### 1.4 验证

- 用 `create_llm()` 创建模型，调用 `model.invoke("hello")` 验证连通性
- 分别测试 `provider: anthropic` 和 `provider: openai`

---

### Phase 2：结构化输出迁移

**目标**：删除 `llm/tools.py` 手写 JSON Schema，用 Pydantic + `with_structured_output()` 替代

**改动文件**：

#### 2.1 复用现有 Pydantic 模型作为输出 Schema

当前 `schemas/` 中的模型已经定义完善，可直接复用。额外需要定义一些 LLM 输出专用模型：

```python
# agent/schemas/llm_output.py（新增）
"""LLM 结构化输出的中间模型"""
from pydantic import BaseModel, Field
from agent.schemas.api_schema import APIEndpoint
from agent.schemas.test_case import TestCase
from agent.schemas.flow import FlowStep

class ExtractedEndpoints(BaseModel):
    """LLM 提取的接口列表"""
    endpoints: list[APIEndpoint]

class GeneratedCases(BaseModel):
    """LLM 生成的测试用例列表"""
    cases: list[TestCase]

class DesignedFlow(BaseModel):
    """LLM 设计的测试流程"""
    name: str
    description: str
    base_url: str = ""
    steps: list[FlowStep]
```

#### 2.2 调用方式变化

```python
# 旧：手写 JSON Schema + tool_use
result = self._llm.chat_with_tools(
    messages=[{"role": "user", "content": prompt}],
    tools=[TOOL_GENERATE_TEST_CASES],
    tool_choice={"type": "tool", "name": "generate_test_cases"},
)
cases = [TestCase(**c) for c in result.get("cases", [])]

# 新：Pydantic 直接绑定
structured_llm = llm.with_structured_output(GeneratedCases)
result: GeneratedCases = structured_llm.invoke(messages)
cases = result.cases  # 已经是 TestCase 列表
```

#### 2.3 删除文件

- 删除 `agent/llm/tools.py`（136 行 JSON Schema 全部由 Pydantic 模型自动生成）
- 删除 `agent/llm/client.py`（由 `models/factory.py` + LangChain 内置重试替代）

---

### Phase 3：Prompt 模板重构

**目标**：从单文件字符串迁移到 `ChatPromptTemplate`，支持多轮消息

#### 3.1 重构 `agent/prompts/generation.py`（示例）

```python
from langchain_core.prompts import ChatPromptTemplate

GENERATE_NORMAL_CASES = ChatPromptTemplate.from_messages([
    ("system", """你是一个资深测试工程师，专注于 API 接口测试用例设计。
你需要根据 API 接口定义生成测试用例，要求：
1. 每个测试用例必须有明确的测试目标和期望结果
2. 测试数据要贴近真实业务场景（中文数据）
3. 函数名使用 test_ 前缀 + 英文下划线命名
4. 描述使用中文
5. 测试用例要具有可执行性"""),
    ("human", """请为以下 API 接口生成【正常场景】测试用例。

API 接口信息：
{endpoint_json}

要求：
- 覆盖所有正常业务操作
- 使用贴近真实的中文测试数据
- 每个用例的 category 为 "normal"
- 优先级为 P0 或 P1"""),
])
```

#### 3.2 迁移映射

| 旧（`llm/prompts.py`） | 新（`prompts/`） |
|------------------------|-----------------|
| `SYSTEM_API_EXTRACTOR` + `PROMPT_EXTRACT_FROM_TEXT` | `prompts/extraction.py` |
| `SYSTEM_CASE_GENERATOR` + `PROMPT_GENERATE_*_CASES` | `prompts/generation.py` |
| `SYSTEM_GAP_ANALYZER` + `PROMPT_ANALYZE_GAPS` | `prompts/gap_analysis.py` |
| `SYSTEM_FLOW_DESIGNER` + `PROMPT_DESIGN_FLOW` | `prompts/flow_design.py` |

#### 3.3 删除文件

- 删除 `agent/llm/prompts.py`
- 删除整个 `agent/llm/` 目录

---

### Phase 4：LangGraph 图编排（核心）

**目标**：用 StateGraph 替代 `cli.py` 中的线性编排逻辑

#### 4.1 定义状态 — `agent/graph/state.py`

```python
from typing import TypedDict, Annotated
from operator import add
from agent.schemas.api_schema import APIDocument, APIEndpoint
from agent.schemas.test_case import TestCase, TestSuite
from agent.schemas.flow import FlowDefinition

class GenerateState(TypedDict):
    """generate 命令的状态"""
    # 输入
    input_source: str                     # 输入源类型
    input_path: str                       # 输入路径或文本
    categories: list[str]                 # 要生成的类别
    output_path: str | None               # 输出路径

    # 中间状态
    document: APIDocument | None          # 解析后的文档
    current_endpoint: APIEndpoint | None  # 当前处理的接口
    pending_endpoints: list[APIEndpoint]  # 待处理的接口队列

    # 累积结果
    cases: Annotated[list[TestCase], add] # 生成的用例（支持追加）
    validated_cases: list[TestCase]       # 校验后的用例
    generated_files: list[str]            # 生成的文件路径列表

    # 控制
    retry_count: int                      # 当前重试次数
    max_retries: int                      # 最大重试次数
    error: str | None                     # 错误信息
```

#### 4.2 定义图节点 — `agent/graph/nodes/`

每个节点是一个纯函数，接收 state，返回 state patch：

```python
# agent/graph/nodes/generate_cases.py
from agent.graph.state import GenerateState
from agent.models.factory import create_llm
from agent.schemas.llm_output import GeneratedCases
from agent.prompts.generation import GENERATE_NORMAL_CASES, ...

def generate_cases(state: GenerateState) -> dict:
    """为当前接口生成测试用例"""
    llm = create_llm()
    structured_llm = llm.with_structured_output(GeneratedCases)
    endpoint = state["current_endpoint"]
    endpoint_json = endpoint.model_dump_json(indent=2, exclude_none=True)

    all_cases = []
    prompt_map = {
        "normal": GENERATE_NORMAL_CASES,
        "abnormal": GENERATE_ABNORMAL_CASES,
        "boundary": GENERATE_BOUNDARY_CASES,
    }

    for category in state["categories"]:
        prompt = prompt_map[category]
        messages = prompt.invoke({"endpoint_json": endpoint_json})
        result: GeneratedCases = structured_llm.invoke(messages)
        all_cases.extend(result.cases)

    return {"cases": all_cases}
```

#### 4.3 构建图 — `agent/graph/generate_graph.py`

```
          ┌──────────────┐
          │  parse_input  │
          └──────┬───────┘
                 │
                 ▼
       ┌─────────────────┐
       │  next_endpoint   │◄─────────────────┐
       └────────┬────────┘                    │
                │                             │
         has endpoint?                        │
          ╱         ╲                         │
        yes          no                       │
         │            │                       │
         ▼            ▼                       │
┌────────────┐  ┌──────────┐                  │
│  generate  │  │   END    │                  │
│   cases    │  └──────────┘                  │
└─────┬──────┘                                │
      │                                       │
      ▼                                       │
┌────────────┐                                │
│  validate  │                                │
└─────┬──────┘                                │
      │                                       │
  all valid?                                  │
   ╱       ╲                                  │
 yes        no & retry < max                  │
  │          │                                │
  │          └──► regenerate ─────────────────┘
  ▼                (回到 generate_cases, retry_count++)
┌──────────────┐
│ generate_code│
└──────┬───────┘
       │
       └──────► next_endpoint ────────────────┘
```

```python
# agent/graph/generate_graph.py
from langgraph.graph import StateGraph, END
from agent.graph.state import GenerateState
from agent.graph.nodes import parse_input, generate_cases, validate_cases, generate_code
from agent.graph.edges import should_retry, has_next_endpoint

def build_generate_graph():
    g = StateGraph(GenerateState)

    g.add_node("parse_input", parse_input)
    g.add_node("next_endpoint", next_endpoint)
    g.add_node("generate_cases", generate_cases)
    g.add_node("validate_cases", validate_cases)
    g.add_node("generate_code", generate_code)

    g.set_entry_point("parse_input")
    g.add_edge("parse_input", "next_endpoint")

    # 条件：是否还有待处理接口
    g.add_conditional_edges("next_endpoint", has_next_endpoint, {
        "continue": "generate_cases",
        "done": END,
    })

    g.add_edge("generate_cases", "validate_cases")

    # 条件：校验失败是否重试
    g.add_conditional_edges("validate_cases", should_retry, {
        "retry": "generate_cases",
        "accept": "generate_code",
    })

    g.add_edge("generate_code", "next_endpoint")

    return g.compile()
```

#### 4.4 类似地构建 `analyze_graph.py` 和 `flow_graph.py`

- **analyze_graph**: parse_code → extract_endpoint → generate_gaps → deduplicate → generate_code
- **flow_graph**: parse_swagger → design_flow → output_json

#### 4.5 删除 `agent/orchestrator/` 目录

- `flow_builder.py` → 合并到 `graph/nodes/design_flow.py`
- `dependency_resolver.py` → 合并到 `graph/nodes/design_flow.py`

---

### Phase 5：CLI 层简化

**目标**：`cli.py` 从业务编排简化为参数解析 + 图调用

```python
# agent/cli.py（重构后）
@cli.command()
@click.option("--from-swagger", ...)
@click.option("--from-text", ...)
@click.option("--from-doc", ...)
@click.option("--from-markdown", ...)
@click.option("--output", "-o", ...)
@click.option("--categories", "-c", default="normal,abnormal,boundary")
def generate(swagger_path, text, doc_path, md_path, output_path, categories):
    """从输入源生成测试用例"""
    from agent.graph.generate_graph import build_generate_graph

    graph = build_generate_graph()
    result = graph.invoke({
        "input_source": _detect_source(swagger_path, text, doc_path, md_path),
        "input_path": swagger_path or text or doc_path or md_path,
        "categories": [c.strip() for c in categories.split(",")],
        "output_path": output_path,
        "retry_count": 0,
        "max_retries": 2,
    })

    for path in result.get("generated_files", []):
        click.echo(f"已生成: {path}")
```

---

### Phase 6：可观测性集成（可选）

**目标**：集成 LangSmith 实现 trace、eval

```python
# agent/models/factory.py 中增加
import os
os.environ.setdefault("LANGSMITH_TRACING", "true")
os.environ.setdefault("LANGSMITH_PROJECT", "testcase-agent")
```

配置完成后，所有 LangGraph 节点的 LLM 调用自动被 trace，可在 LangSmith 面板查看：
- 每个节点的输入/输出
- LLM 调用延迟、token 消耗
- 重试次数和失败原因

---

## 五、迁移顺序与里程碑

| 阶段 | 内容 | 新增/删除文件 | 可验证标准 |
|------|------|--------------|-----------|
| Phase 1 | LLM 调用统一 | +`models/factory.py`，改 `config.py` | `create_llm().invoke("hi")` 两个 provider 都通 |
| Phase 2 | 结构化输出 | +`schemas/llm_output.py`，-`llm/tools.py`，-`llm/client.py` | 生成用例结果与旧版一致 |
| Phase 3 | Prompt 重构 | +`prompts/*.py`，-`llm/prompts.py`，-`llm/` | Prompt 渲染结果与旧版一致 |
| Phase 4 | LangGraph 图 | +`graph/**`，-`orchestrator/` | `generate` / `analyze` / `flow` 三个命令跑通 |
| Phase 5 | CLI 简化 | 改 `cli.py` | CLI 行为与旧版一致 |
| Phase 6 | 可观测性 | 改 `models/factory.py` | LangSmith 面板可看到 trace |

**建议从 Phase 1 开始逐步推进，每个阶段完成后用现有 CLI 命令做回归验证。**

## 六、风险与注意事项

1. **LangChain 版本变动** — `langchain-core` 0.3.x 和 `langgraph` 0.4.x API 已经较为稳定，但仍需锁定小版本
2. **结构化输出差异** — `with_structured_output()` 在 Anthropic 和 OpenAI 上底层实现不同（tool_use vs function_calling），需分别验证
3. **中文 Prompt** — LangChain 的 `ChatPromptTemplate` 对中文支持良好，无特殊问题
4. **依赖体积** — `langchain-core` + `langgraph` 约增加 20MB 依赖，可接受
5. **向后兼容** — CLI 接口（命令、参数）保持不变，用户无感知
6. **测试** — 每个 Phase 完成后需验证三个核心命令：`generate`、`analyze`、`flow`
