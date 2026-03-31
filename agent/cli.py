# -*- coding: utf-8 -*-
"""CLI 入口：支持从多种输入源生成测试用例。"""

from __future__ import annotations

import logging

import click

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
    from agent.graph.generate_graph import build_generate_graph

    graph = build_generate_graph()
    result = graph.invoke(
        {
            "input_source": _detect_source(swagger_path, text, doc_path, md_path),
            "input_path": swagger_path or text or doc_path or md_path,
            "categories": [c.strip() for c in categories.split(",") if c.strip()],
            "output_path": output_path,
            "retry_count": 0,
            "max_retries": 2,
            "generated_files": [],
        }
    )

    document = result.get("document")
    if not document or not document.endpoints:
        raise click.ClickException("未能从输入中提取到任何接口信息")

    click.echo(f"提取到 {len(document.endpoints)} 个接口:")
    for endpoint in document.endpoints:
        click.echo(f"  - {endpoint.method} {endpoint.path}: {endpoint.summary}")

    generated_files = result.get("generated_files", [])
    if not generated_files:
        raise click.ClickException("未生成测试文件")

    for path in generated_files:
        click.echo(f"已生成: {path}")


@cli.command()
@click.option("--code", "code_path", required=True, help="已有测试文件路径")
@click.option("--output", "-o", "output_path", help="输出文件路径")
def analyze(code_path, output_path):
    """分析已有测试代码，补全缺失用例"""
    from agent.graph.analyze_graph import build_analyze_graph

    graph = build_analyze_graph()
    result = graph.invoke(
        {
            "code_path": code_path,
            "output_path": output_path,
            "generated_files": [],
        }
    )

    existing_names = result.get("existing_names", [])
    click.echo(f"已有 {len(existing_names)} 个测试函数: {existing_names}")

    endpoint = result.get("endpoint")
    if endpoint is None:
        raise click.ClickException("未能从代码中提取接口信息")
    click.echo(f"识别到接口: {endpoint.method} {endpoint.path}")

    gap_cases = result.get("deduplicated_cases", [])
    click.echo(f"发现 {len(gap_cases)} 个缺失用例")
    if not gap_cases:
        click.echo("没有发现缺失的测试场景")
        return

    for path in result.get("generated_files", []):
        click.echo(f"已生成补充用例: {path}")


@cli.command()
@click.option("--endpoints", "swagger_path", required=True, help="Swagger/OpenAPI 文件路径")
@click.option("--description", "-d", "flow_desc", required=True, help="中文业务流程描述")
@click.option("--base-url", help="基础地址")
@click.option("--output", "-o", "output_path", help="输出文件路径")
def flow(swagger_path, flow_desc, base_url, output_path):
    """生成 E2E 流程测试"""
    from agent.graph.flow_graph import build_flow_graph

    graph = build_flow_graph()
    result = graph.invoke(
        {
            "input_source": "swagger",
            "input_path": swagger_path,
            "flow_description": flow_desc,
            "base_url": base_url or "",
            "output_path": output_path,
        }
    )

    document = result.get("document")
    flow_definition = result.get("flow_definition")
    if not document:
        raise click.ClickException("Swagger 解析失败")
    if not flow_definition:
        raise click.ClickException("未生成流程定义")

    click.echo(f"加载 {len(document.endpoints)} 个接口")
    click.echo(f"生成流程: {flow_definition.name} ({len(flow_definition.steps)} 步)")
    click.echo(f"流程定义: {result.get('generated_file')}")


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
    """兼容旧函数名，转发到输入源检测。"""
    return _detect_source(swagger_path, text, doc_path, md_path)


def _detect_source(swagger_path, text, doc_path, md_path) -> str:
    """校验并识别输入源类型。"""
    sources = {
        "swagger": swagger_path,
        "text": text,
        "doc": doc_path,
        "markdown": md_path,
    }
    provided = [name for name, value in sources.items() if value]
    if not provided:
        raise click.ClickException(
            "请指定输入源: --from-swagger, --from-text, --from-doc, 或 --from-markdown"
        )
    if len(provided) > 1:
        raise click.ClickException("一次只能指定一个输入源")
    return provided[0]


if __name__ == "__main__":
    cli()
