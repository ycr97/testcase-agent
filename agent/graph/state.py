"""Graph 状态定义。"""

from __future__ import annotations

from operator import add
from typing import Annotated, TypedDict

from agent.schemas.api_schema import APIDocument, APIEndpoint
from agent.schemas.flow import FlowDefinition
from agent.schemas.test_case import TestCase


class GenerateState(TypedDict, total=False):
    input_source: str
    input_path: str
    categories: list[str]
    output_path: str | None
    document: APIDocument | None
    current_endpoint: APIEndpoint | None
    pending_endpoints: list[APIEndpoint]
    cases: list[TestCase]
    validated_cases: list[TestCase]
    generated_files: Annotated[list[str], add]
    retry_count: int
    max_retries: int
    error: str | None


class AnalyzeState(TypedDict, total=False):
    code_path: str
    output_path: str | None
    existing_code: str
    existing_names: list[str]
    document: APIDocument | None
    endpoint: APIEndpoint | None
    gap_cases: list[TestCase]
    deduplicated_cases: list[TestCase]
    generated_files: Annotated[list[str], add]
    error: str | None


class FlowState(TypedDict, total=False):
    input_source: str
    input_path: str
    flow_description: str
    base_url: str
    output_path: str | None
    document: APIDocument | None
    flow_definition: FlowDefinition | None
    generated_file: str | None
    error: str | None
