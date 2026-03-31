# -*- coding: utf-8 -*-
"""CLI 入口：支持从多种输入源生成测试用例。"""

from __future__ import annotations

import json
import logging
import sys

import click

from agent.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


@click.group()
def cli():
    """测试用例生成 Agent - 自动生成 API 接口测试用例"""
    pass


@cli.command()
@click.option("--from-swagger", "swagger_path", help="Swagger/OpenAPI 文件路径")
@click.option("--from-text", "text", help="中文接口描述文本")
@click.option("--from-doc", "doc_path", help="Word (.docx) 文件路径")
@click.option("--from-markdown", "md_path", help="Markdown 文件路径")
@click.option("--output", "-o", "output_path", help="输出文件路径")
@click.option(
    "--categories", "-c",
    default="normal,abnormal,boundary",
    help="生成的用例类别，逗号分隔 (normal,abnormal,boundary)",
)
def generate(swagger_path, text, doc_path, md_path, output_path, categories):
    """从输入源生成测试用例"""
    from agent.schemas.api_schema import APIDocument

    # 1. 解析输入源
    doc = _parse_input(swagger_path, text, doc_path, md_path)
    if not doc.endpoints:
        click.echo("未能从输入中提取到任何接口信息", err=True)
        sys.exit(1)

    click.echo(f"提取到 {len(doc.endpoints)} 个接口:")
    for ep in doc.endpoints:
        click.echo(f"  - {ep.method} {ep.path}: {ep.summary}")

    # 2. 生成测试用例
    from agent.generators.case_generator import CaseGenerator
    from agent.generators.code_generator import CodeGenerator
    from agent.quality.validator import Validator

    cat_list = [c.strip() for c in categories.split(",")]
    generator = CaseGenerator()
    code_gen = CodeGenerator()
    validator = Validator()

    for endpoint in doc.endpoints:
        click.echo(f"\n生成 {endpoint.summary or endpoint.path} 的测试用例...")
        suite = generator.generate(endpoint, categories=cat_list)

        # 3. 质量校验
        suite.cases = validator.validate(suite.cases, endpoint)

        click.echo(f"  正常: {len(suite.normal_cases)} | 异常: {len(suite.abnormal_cases)} | 边界: {len(suite.boundary_cases)}")

        # 4. 生成代码
        path = code_gen.generate(suite, output_path)
        click.echo(f"  -> 已生成: {path}")


@cli.command()
@click.option("--code", "code_path", required=True, help="已有测试文件路径")
@click.option("--output", "-o", "output_path", help="输出文件路径")
def analyze(code_path, output_path):
    """分析已有测试代码，补全缺失用例"""
    from agent.parsers.code_analyzer import CodeAnalyzer
    from agent.generators.case_generator import CaseGenerator
    from agent.generators.code_generator import CodeGenerator
    from agent.quality.deduplicator import Deduplicator

    analyzer = CodeAnalyzer()
    existing_code = analyzer.get_source_code(code_path)
    existing_names = analyzer.get_existing_test_names(code_path)
    click.echo(f"已有 {len(existing_names)} 个测试函数: {existing_names}")

    # 提取接口信息
    doc = analyzer.parse(code_path)
    if not doc.endpoints:
        click.echo("未能从代码中提取接口信息", err=True)
        sys.exit(1)

    endpoint = doc.endpoints[0]
    click.echo(f"识别到接口: {endpoint.method} {endpoint.path}")

    # 生成缺失用例
    generator = CaseGenerator()
    gap_cases = generator.analyze_gaps(endpoint, existing_code)

    # 去重
    dedup = Deduplicator()
    gap_cases = dedup.deduplicate(gap_cases, existing_names)
    click.echo(f"发现 {len(gap_cases)} 个缺失用例")

    if not gap_cases:
        click.echo("没有发现缺失的测试场景")
        return

    from agent.schemas.test_case import TestSuite
    suite = TestSuite(
        endpoint_path=endpoint.path,
        endpoint_summary=f"{endpoint.summary} - 补充用例",
        base_url=endpoint.base_url,
        cases=gap_cases,
    )

    code_gen = CodeGenerator()
    path = code_gen.generate(suite, output_path)
    click.echo(f"  -> 已生成补充用例: {path}")


@cli.command()
@click.option("--endpoints", "swagger_path", required=True, help="Swagger/OpenAPI 文件路径")
@click.option("--description", "-d", "flow_desc", required=True, help="中文业务流程描述")
@click.option("--base-url", help="基础地址")
@click.option("--output", "-o", "output_path", help="输出文件路径")
def flow(swagger_path, flow_desc, base_url, output_path):
    """生成 E2E 流程测试"""
    from agent.parsers.swagger_parser import SwaggerParser
    from agent.orchestrator.flow_builder import FlowBuilder

    parser = SwaggerParser()
    doc = parser.parse(swagger_path)
    click.echo(f"加载 {len(doc.endpoints)} 个接口")

    builder = FlowBuilder()
    flow_def = builder.build(doc.endpoints, flow_desc, base_url or "")
    click.echo(f"生成流程: {flow_def.name} ({len(flow_def.steps)} 步)")

    # 输出流程定义
    output = output_path or "generated_tests/flow_definition.json"
    with open(output, "w", encoding="utf-8") as f:
        f.write(flow_def.model_dump_json(indent=2, exclude_none=True))
    click.echo(f"  -> 流程定义: {output}")


@cli.command()
@click.option("--file", "file_path", required=True, help="测试文件路径")
@click.option("--functions", "-f", help="要执行的函数名，逗号分隔")
def run(file_path, functions):
    """执行生成的测试文件"""
    from agent.runner.executor import TestExecutor
    from agent.runner.reporter import TestReporter

    func_list = [f.strip() for f in functions.split(",")] if functions else None

    executor = TestExecutor()
    results = executor.run_file(file_path, func_list)

    reporter = TestReporter()
    report = reporter.generate_report(results, file_path)
    click.echo(report)


def _parse_input(swagger_path, text, doc_path, md_path):
    """根据提供的参数选择解析器。"""
    from agent.schemas.api_schema import APIDocument

    if swagger_path:
        from agent.parsers.swagger_parser import SwaggerParser
        return SwaggerParser().parse(swagger_path)
    elif text:
        from agent.parsers.text_parser import TextParser
        return TextParser().parse(text)
    elif doc_path:
        from agent.parsers.word_parser import WordParser
        return WordParser().parse(doc_path)
    elif md_path:
        from agent.parsers.markdown_parser import MarkdownParser
        return MarkdownParser().parse(md_path)
    else:
        click.echo("请指定输入源: --from-swagger, --from-text, --from-doc, 或 --from-markdown", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
