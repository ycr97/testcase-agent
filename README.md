# 测试用例生成 Agent

基于 LangChain/LangGraph 的 API 测试用例生成 Agent。支持从多种输入源（Swagger、文档、文字描述、已有代码）生成覆盖正常、异常、边界场景的测试用例，并支持端到端流程编排。

## 项目结构

```
testCaseProject/
├── agent/
│   ├── __init__.py
│   ├── __main__.py              # python -m agent 入口
│   ├── cli.py                   # CLI 四个命令: generate/analyze/flow/run
│   ├── config.py                # 配置管理（YAML + 环境变量）
│   ├── models/
│   │   └── factory.py           # ChatModel 工厂
│   ├── parsers/
│   │   ├── base.py              # 解析器抽象基类
│   │   ├── swagger_parser.py    # Swagger/OpenAPI 解析（纯代码）
│   │   ├── text_parser.py       # 中文文字描述解析（LLM）
│   │   ├── markdown_parser.py   # Markdown 文档解析
│   │   ├── word_parser.py       # Word 文档解析
│   │   └── code_analyzer.py     # 已有代码分析（AST + LLM）
│   ├── prompts/
│   │   ├── extraction.py        # API 提取 Prompt
│   │   ├── generation.py        # 用例生成 Prompt
│   │   ├── gap_analysis.py      # 缺失用例分析 Prompt
│   │   └── flow_design.py       # 流程设计 Prompt
│   ├── graph/
│   │   ├── generate_graph.py    # generate 命令状态图
│   │   ├── analyze_graph.py     # analyze 命令状态图
│   │   ├── flow_graph.py        # flow 命令状态图
│   │   └── nodes/               # 图节点
│   ├── generators/
│   │   ├── case_generator.py    # 三轮用例生成（正常/异常/边界）
│   │   ├── code_generator.py    # Jinja2 模板渲染
│   │   └── templates/
│   │       └── test_file.py.j2  # 匹配现有代码风格的模板
│   ├── schemas/
│   │   ├── api_schema.py        # APIEndpoint 标准化模型
│   │   ├── test_case.py         # TestCase/TestSuite 模型
│   │   ├── flow.py              # FlowDefinition 模型
│   │   └── llm_output.py        # LLM 结构化输出模型
│   ├── quality/
│   │   ├── validator.py         # Schema 校验
│   │   └── deduplicator.py      # 去重
│   └── runner/
│       ├── executor.py          # 测试执行
│       └── reporter.py          # 报告生成
├── config/
│   └── settings.yaml            # 环境配置
├── generated_tests/             # 生成的测试文件输出目录
├── promotion/                   # 已有测试（配额调整）
├── growth_import_export_test/   # 已有测试（结案单导入导出）
├── pyproject.toml               # 依赖定义
└── README.md
```

## 安装

```bash
pip install -e .
```

## 配置

1. 设置模型 API Key：

```bash
export ANTHROPIC_API_KEY="your-api-key"
# 或
export OPENAI_API_KEY="your-api-key"
```

2. 可选：编辑 `config/settings.yaml` 中的 `llm.provider` 和模型参数。

## 使用方式

### 从中文描述生成测试用例

```bash
python -m agent generate --from-text "调整配额接口，POST方法，路径 /adjustQuota/v1，参数 orgCode, amount, operationType(ADD/SUBTRACT)"
```

### 从 Swagger/OpenAPI 文件生成

```bash
python -m agent generate --from-swagger ./swagger.json
```

### 从 Word 文档生成

```bash
python -m agent generate --from-doc ./api_doc.docx
```

### 从 Markdown 文档生成

```bash
python -m agent generate --from-markdown ./api_doc.md
```

### 分析已有代码，补全缺失用例

```bash
python -m agent analyze --code ./promotion/test_adjust_quota.py
```

### 生成 E2E 流程测试

```bash
python -m agent flow --endpoints ./swagger.json -d "创建订单后调整配额并导出"
```

### 执行生成的测试

```bash
python -m agent run --file ./generated_tests/test_xxx.py
```

### 常用选项

```bash
# 只生成正常场景用例
python -m agent generate --from-swagger ./swagger.json -c normal

# 指定输出文件
python -m agent generate --from-text "..." -o ./my_tests/test_api.py

# 执行指定函数
python -m agent run --file ./generated_tests/test_xxx.py -f test_add_quota,test_subtract_quota
```

## 核心设计

- **统一中间表示**：所有输入源解析为 `APIEndpoint` 标准格式，输入与生成完全解耦
- **三轮生成策略**：分别生成正常、异常、边界用例，确保覆盖全面
- **模板渲染生成代码**：通过 Jinja2 模板确定性渲染，非 LLM 直接生成代码，杜绝语法错误
- **Pydantic 结构化输出**：使用 `with_structured_output()` 约束 LLM 输出
- **LangGraph 编排**：通过状态图替代 CLI 中的硬编码线性流程
- **质量保障**：Pydantic schema 校验 + 去重 + 不确定字段标记 `# TODO: 请确认`
