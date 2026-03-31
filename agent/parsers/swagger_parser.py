# -*- coding: utf-8 -*-
"""Swagger/OpenAPI 文档解析器（纯代码，无需 LLM）"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from agent.parsers.base import BaseParser
from agent.schemas.api_schema import APIDocument, APIEndpoint, APIParameter


class SwaggerParser(BaseParser):
    """解析 OpenAPI 2.0/3.0 JSON/YAML 文件。"""

    def parse(self, source: str) -> APIDocument:
        """
        Args:
            source: Swagger/OpenAPI 文件路径
        """
        path = Path(source)
        with open(path, "r", encoding="utf-8") as f:
            if path.suffix in (".yaml", ".yml"):
                spec = yaml.safe_load(f)
            else:
                spec = json.load(f)

        # 判断 OpenAPI 版本
        if spec.get("openapi", "").startswith("3"):
            return self._parse_openapi3(spec)
        else:
            return self._parse_swagger2(spec)

    def _parse_openapi3(self, spec: dict) -> APIDocument:
        title = spec.get("info", {}).get("title", "")
        description = spec.get("info", {}).get("description", "")
        base_url = ""
        servers = spec.get("servers", [])
        if servers:
            base_url = servers[0].get("url", "")

        endpoints = []
        for path, methods in spec.get("paths", {}).items():
            for method, operation in methods.items():
                if method in ("get", "post", "put", "delete", "patch"):
                    endpoint = self._parse_operation_v3(path, method.upper(), operation, spec, base_url)
                    endpoints.append(endpoint)

        return APIDocument(title=title, description=description, endpoints=endpoints)

    def _parse_swagger2(self, spec: dict) -> APIDocument:
        title = spec.get("info", {}).get("title", "")
        description = spec.get("info", {}).get("description", "")
        host = spec.get("host", "")
        base_path = spec.get("basePath", "")
        schemes = spec.get("schemes", ["https"])
        base_url = f"{schemes[0]}://{host}{base_path}" if host else ""

        endpoints = []
        for path, methods in spec.get("paths", {}).items():
            for method, operation in methods.items():
                if method in ("get", "post", "put", "delete", "patch"):
                    endpoint = self._parse_operation_v2(path, method.upper(), operation, spec, base_url)
                    endpoints.append(endpoint)

        return APIDocument(title=title, description=description, endpoints=endpoints)

    def _parse_operation_v3(
        self, path: str, method: str, operation: dict, spec: dict, base_url: str
    ) -> APIEndpoint:
        summary = operation.get("summary", "")
        desc = operation.get("description", "")
        tags = operation.get("tags", [])

        # 解析参数
        query_params = []
        path_params = []
        for param in operation.get("parameters", []):
            p = self._parse_parameter(param, spec)
            if param.get("in") == "query":
                query_params.append(p)
            elif param.get("in") == "path":
                path_params.append(p)

        # 解析请求体
        request_body = []
        request_body_type = "json"
        request_body_is_array = False
        rb = operation.get("requestBody", {})
        if rb:
            content = rb.get("content", {})
            if "application/json" in content:
                schema = content["application/json"].get("schema", {})
                schema = self._resolve_ref(schema, spec)
                if schema.get("type") == "array":
                    request_body_is_array = True
                    item_schema = self._resolve_ref(schema.get("items", {}), spec)
                    request_body = self._schema_to_params(item_schema, spec)
                else:
                    request_body = self._schema_to_params(schema, spec)
            elif "multipart/form-data" in content:
                request_body_type = "form-data"
                schema = content["multipart/form-data"].get("schema", {})
                schema = self._resolve_ref(schema, spec)
                request_body = self._schema_to_params(schema, spec)

        # 解析响应
        response_schema = {}
        responses = operation.get("responses", {})
        ok_resp = responses.get("200", responses.get("201", {}))
        if ok_resp:
            resp_content = ok_resp.get("content", {})
            if "application/json" in resp_content:
                response_schema = resp_content["application/json"].get("schema", {})

        return APIEndpoint(
            path=path,
            method=method,
            summary=summary,
            description=desc,
            base_url=base_url,
            request_body=request_body,
            request_body_type=request_body_type,
            request_body_is_array=request_body_is_array,
            query_params=query_params,
            path_params=path_params,
            response_schema=response_schema,
            tags=tags,
        )

    def _parse_operation_v2(
        self, path: str, method: str, operation: dict, spec: dict, base_url: str
    ) -> APIEndpoint:
        summary = operation.get("summary", "")
        desc = operation.get("description", "")
        tags = operation.get("tags", [])

        query_params = []
        path_params = []
        request_body = []
        request_body_is_array = False

        for param in operation.get("parameters", []):
            if param.get("in") == "body":
                schema = self._resolve_ref(param.get("schema", {}), spec)
                if schema.get("type") == "array":
                    request_body_is_array = True
                    item_schema = self._resolve_ref(schema.get("items", {}), spec)
                    request_body = self._schema_to_params(item_schema, spec)
                else:
                    request_body = self._schema_to_params(schema, spec)
            elif param.get("in") == "query":
                query_params.append(self._parse_parameter(param, spec))
            elif param.get("in") == "path":
                path_params.append(self._parse_parameter(param, spec))

        response_schema = {}
        responses = operation.get("responses", {})
        ok_resp = responses.get("200", responses.get("201", {}))
        if ok_resp and "schema" in ok_resp:
            response_schema = ok_resp["schema"]

        return APIEndpoint(
            path=path,
            method=method,
            summary=summary,
            description=desc,
            base_url=base_url,
            request_body=request_body,
            request_body_is_array=request_body_is_array,
            query_params=query_params,
            path_params=path_params,
            response_schema=response_schema,
            tags=tags,
        )

    def _parse_parameter(self, param: dict, spec: dict) -> APIParameter:
        return APIParameter(
            name=param.get("name", ""),
            type=param.get("type", param.get("schema", {}).get("type", "string")),
            required=param.get("required", False),
            description=param.get("description", ""),
            enum=param.get("enum"),
            example=param.get("example"),
        )

    def _schema_to_params(self, schema: dict, spec: dict) -> list[APIParameter]:
        """将 JSON Schema 的 properties 转换为 APIParameter 列表。"""
        schema = self._resolve_ref(schema, spec)
        params = []
        required_fields = set(schema.get("required", []))
        for name, prop in schema.get("properties", {}).items():
            prop = self._resolve_ref(prop, spec)
            children = []
            if prop.get("type") == "object":
                children = self._schema_to_params(prop, spec)
            elif prop.get("type") == "array" and "items" in prop:
                item_schema = self._resolve_ref(prop["items"], spec)
                if item_schema.get("type") == "object":
                    children = self._schema_to_params(item_schema, spec)

            params.append(APIParameter(
                name=name,
                type=prop.get("type", "string"),
                required=name in required_fields,
                description=prop.get("description", ""),
                enum=prop.get("enum"),
                example=prop.get("example"),
                children=children,
            ))
        return params

    def _resolve_ref(self, schema: dict, spec: dict) -> dict:
        """解析 $ref 引用。"""
        ref = schema.get("$ref")
        if not ref:
            return schema
        parts = ref.lstrip("#/").split("/")
        resolved = spec
        for part in parts:
            resolved = resolved.get(part, {})
        return resolved
