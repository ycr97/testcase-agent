# -*- coding: utf-8 -*-
"""测试执行器"""

from __future__ import annotations

import importlib.util
import sys
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class TestExecutor:
    """执行生成的测试文件。"""

    def run_file(self, file_path: str, functions: list[str] | None = None) -> dict:
        """
        执行测试文件中的测试函数。

        Args:
            file_path: 测试文件路径
            functions: 要执行的函数名列表，为 None 时执行所有 test_ 函数

        Returns:
            {函数名: {"status": "pass"|"fail"|"error", "message": str}}
        """
        path = Path(file_path)
        spec = importlib.util.spec_from_file_location(path.stem, str(path))
        module = importlib.util.module_from_spec(spec)
        sys.modules[path.stem] = module
        spec.loader.exec_module(module)

        # 获取所有 test_ 函数
        if functions is None:
            functions = [
                name for name in dir(module)
                if name.startswith("test_") and callable(getattr(module, name))
            ]

        results = {}
        for func_name in functions:
            func = getattr(module, func_name, None)
            if not func or not callable(func):
                results[func_name] = {"status": "error", "message": f"函数 {func_name} 不存在"}
                continue

            try:
                func()
                results[func_name] = {"status": "pass", "message": ""}
            except AssertionError as e:
                results[func_name] = {"status": "fail", "message": str(e)}
            except Exception as e:
                results[func_name] = {"status": "error", "message": str(e)}

        return results
