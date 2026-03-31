# -*- coding: utf-8 -*-
"""解析器基类"""

from __future__ import annotations

from abc import ABC, abstractmethod

from agent.schemas.api_schema import APIDocument


class BaseParser(ABC):
    """所有解析器的抽象基类，输出统一的 APIDocument。"""

    @abstractmethod
    def parse(self, source: str) -> APIDocument:
        """
        解析输入源，返回标准化的 APIDocument。

        Args:
            source: 输入源（文件路径或文本内容，由子类决定）

        Returns:
            APIDocument: 标准化的接口文档
        """
        ...
