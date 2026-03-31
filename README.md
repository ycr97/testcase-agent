# 测试用例生成 Agent

基于 LangChain/LangGraph 的 API 测试用例生成工具。

它支持从 Swagger/OpenAPI、Word、Markdown、中文自由描述和已有测试代码中提取接口信息，生成接口测试用例、补齐缺失场景，并输出 E2E 流程定义。

## 核心能力

- 多模型支持：通过 `llm.provider` 在 Anthropic 和 OpenAI 间切换
- 图编排：`generate`、`analyze`、`flow` 三个命令都由 LangGraph 驱动
- 结构化输出：使用 Pydantic + `with_structured_output()` 约束 LLM 输出
- 确定性代码生成：测试代码由 Jinja2 模板渲染，不直接让 LLM 产出 Python 文件
- 质量控制：生成后经过校验、去重和重试逻辑处理

## 架构概览

### generate

`parse_input -> next_endpoint -> generate_cases -> validate_cases -> generate_code`

- 支持多接口逐个处理
- 校验不通过时按 `max_retries` 重试
- 最终输出到 `generated_tests/` 或显式指定的路径

### analyze

`analyze_code -> generate_gap_cases -> deduplicate_cases -> generate_code`

- 从已有测试代码中提取接口
- 生成缺失场景
- 和现有测试名、请求数据做去重

### flow

`parse_swagger -> design_flow -> output_flow`

- 从 Swagger 读取可用接口
- 让 LLM 设计调用链
- 输出 JSON 流程定义

## 安装

要求：

- Python 3.12+

安装方式：

```bash
python -m pip install -e .
```

安装后可直接使用：

```bash
python -m agent --help
```

## 配置

配置文件位于 `config/settings.yaml`。

默认配置示例：

```yaml
llm:
  provider: anthropic
  model: claude-sonnet-4-20250514
  max_tokens: 4096
  temperature: 0.0
```

### 环境变量

Anthropic：

```bash
export ANTHROPIC_API_KEY="your-api-key"
```

OpenAI：

```bash
export OPENAI_API_KEY="your-api-key"
```

可选环境变量：

```bash
export TEST_ENV="uat"
export AUTH_TOKEN="your-auth-token"
```

如果配置了 LangSmith，也会自动开启 tracing：

```bash
export LANGSMITH_API_KEY="your-langsmith-key"
export LANGSMITH_PROJECT="testcase-agent"
```

## 使用方式

### 1. 从中文描述生成测试用例

```bash
python -m agent generate \
  --from-text "调整配额接口，POST方法，路径 /adjustQuota/v1，参数 orgCode, amount, operationType(ADD/SUBTRACT)"
```

### 2. 从 Swagger/OpenAPI 生成测试用例

```bash
python -m agent generate --from-swagger ./swagger.json
```

### 3. 从 Word 文档生成测试用例

```bash
python -m agent generate --from-doc ./api_doc.docx
```

### 4. 从 Markdown 文档生成测试用例

```bash
python -m agent generate --from-markdown ./api_doc.md
```

### 5. 分析已有测试代码并补全缺失场景

```bash
python -m agent analyze --code ./tests/test_adjust_quota.py
```

### 6. 生成 E2E 流程定义

```bash
python -m agent flow \
  --endpoints ./swagger.json \
  -d "创建订单后调整配额并导出"
```

### 7. 执行生成的测试文件

```bash
python -m agent run --file ./generated_tests/test_xxx.py
```

## 常用参数

只生成正常场景：

```bash
python -m agent generate --from-swagger ./swagger.json -c normal
```

生成正常 + 异常场景：

```bash
python -m agent generate --from-swagger ./swagger.json -c normal,abnormal
```

指定输出文件：

```bash
python -m agent generate --from-text "..." -o ./my_tests/test_api.py
```

指定输出目录：

```bash
python -m agent generate --from-swagger ./swagger.json -o ./my_tests/
```

执行指定函数：

```bash
python -m agent run --file ./generated_tests/test_xxx.py -f test_add_quota,test_subtract_quota
```

## 输出规则

- `generate` 默认输出到 `generated_tests/`
- 当输入包含多个接口时：
  - 如果 `-o` 是目录，按接口路径生成多个文件
  - 如果 `-o` 是单个 `.py` 文件名，会自动追加接口后缀，避免互相覆盖
- `flow` 默认输出到 `generated_tests/flow_definition.json`

## 项目结构

```text
testcase-agent/
├── agent/
│   ├── cli.py
│   ├── config.py
│   ├── models/
│   │   └── factory.py
│   ├── prompts/
│   │   ├── extraction.py
│   │   ├── generation.py
│   │   ├── gap_analysis.py
│   │   └── flow_design.py
│   ├── graph/
│   │   ├── state.py
│   │   ├── edges.py
│   │   ├── generate_graph.py
│   │   ├── analyze_graph.py
│   │   ├── flow_graph.py
│   │   └── nodes/
│   ├── parsers/
│   ├── generators/
│   ├── quality/
│   ├── runner/
│   └── schemas/
├── config/
│   └── settings.yaml
├── generated_tests/
├── pyproject.toml
└── README.md
```

## 关键模块说明

- `agent/models/factory.py`：统一创建 ChatModel
- `agent/prompts/`：按场景拆分的 Prompt 模板
- `agent/graph/`：LangGraph 状态、节点和图定义
- `agent/parsers/`：多输入源解析器
- `agent/generators/code_generator.py`：Jinja2 测试代码渲染
- `agent/schemas/llm_output.py`：LLM 结构化输出模型

## 当前验证

本仓库已经验证过以下基础命令可运行：

```bash
python -m compileall agent
python -m pip install -e .
python -m agent --help
python -m agent generate --help
```

真实生成链路仍依赖可用的模型 API Key 和输入样例。
