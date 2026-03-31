# -*- coding: utf-8 -*-
"""代码生成器：使用 Jinja2 模板将 TestSuite 渲染为 Python 测试文件。"""

from __future__ import annotations

import json
import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from agent.schemas.test_case import TestSuite
from agent.config import get_settings, PROJECT_ROOT

TEMPLATES_DIR = Path(__file__).parent / "templates"


def _tojson_cn(value, indent=4):
    """自定义 Jinja2 filter：输出 Python 字面量（True/False/None 而非 true/false/null）。"""
    text = json.dumps(value, ensure_ascii=False, indent=indent)
    # JSON -> Python 字面量转换
    import re as _re
    # 替换所有独立的 JSON 布尔/null 为 Python 字面量
    text = _re.sub(r'\btrue\b', 'True', text)
    text = _re.sub(r'\bfalse\b', 'False', text)
    text = _re.sub(r'\bnull\b', 'None', text)
    return text


class CodeGenerator:
    """将 TestSuite 渲染为 Python 测试文件。"""

    def __init__(self):
        self._env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            keep_trailing_newline=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self._env.filters["tojson_cn"] = _tojson_cn

    def generate(self, suite: TestSuite, output_path: str | None = None) -> str:
        """
        生成测试文件。

        Args:
            suite: 测试套件
            output_path: 输出文件路径。为 None 时自动生成到 generated_tests/

        Returns:
            生成的文件路径
        """
        template = self._env.get_template("test_file.py.j2")

        # 确定 HTTP 方法（从第一个用例或默认 POST）
        method = "POST"
        if suite.cases:
            method = suite.cases[0].method

        content = template.render(suite=suite, method=method)

        if not output_path:
            settings = get_settings()
            output_dir = PROJECT_ROOT / settings.output.directory
            output_dir.mkdir(parents=True, exist_ok=True)
            # 从接口路径生成文件名
            filename = self._path_to_filename(suite.endpoint_path)
            output_path = str(output_dir / filename)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        return output_path

    def render_to_string(self, suite: TestSuite) -> str:
        """渲染为字符串（不写文件），用于预览。"""
        template = self._env.get_template("test_file.py.j2")
        method = "POST"
        if suite.cases:
            method = suite.cases[0].method
        return template.render(suite=suite, method=method)

    @staticmethod
    def _path_to_filename(api_path: str) -> str:
        """将接口路径转换为文件名。如 /a/b/c/v1 -> test_a_b_c_v1.py"""
        clean = api_path.strip("/").replace("/", "_").replace("-", "_")
        clean = re.sub(r"[^a-zA-Z0-9_]", "", clean)
        if not clean:
            clean = "unnamed_api"
        return f"test_{clean}.py"
