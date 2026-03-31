# -*- coding: utf-8 -*-
"""测试报告生成器"""

from __future__ import annotations

from datetime import datetime


class TestReporter:
    """生成测试执行报告。"""

    def generate_report(self, results: dict[str, dict], file_path: str = "") -> str:
        """
        生成文本格式的测试报告。

        Args:
            results: {函数名: {"status": "pass"|"fail"|"error", "message": str}}
            file_path: 测试文件路径
        """
        total = len(results)
        passed = sum(1 for r in results.values() if r["status"] == "pass")
        failed = sum(1 for r in results.values() if r["status"] == "fail")
        errors = sum(1 for r in results.values() if r["status"] == "error")

        lines = [
            "=" * 60,
            f"测试报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"测试文件: {file_path}",
            "=" * 60,
            f"总计: {total} | 通过: {passed} | 失败: {failed} | 错误: {errors}",
            "-" * 60,
        ]

        for name, result in results.items():
            status_icon = {"pass": "✓", "fail": "✗", "error": "!"}
            icon = status_icon.get(result["status"], "?")
            line = f"  [{icon}] {name}"
            if result["message"]:
                line += f" - {result['message']}"
            lines.append(line)

        lines.append("=" * 60)
        return "\n".join(lines)
