from __future__ import annotations

import json
from typing import Any, Type

from pydantic import BaseModel

from django_ai_sdk.exceptions import SchemaError


class StructuredOutput:
    """Utilities for working with Pydantic-based structured output."""

    @staticmethod
    def get_json_schema(model_class: Type[BaseModel]) -> dict[str, Any]:
        """Extract a JSON schema from a Pydantic v2 model."""
        try:
            schema = model_class.model_json_schema()
        except Exception as exc:
            raise SchemaError(f"Failed to extract JSON schema from {model_class}: {exc}") from exc
        return schema

    @staticmethod
    def validate(model_class: Type[BaseModel], data: str | dict) -> BaseModel:
        """Validate and return a Pydantic model instance from JSON string or dict."""
        try:
            if isinstance(data, str):
                return model_class.model_validate_json(data)
            return model_class.model_validate(data)
        except Exception as exc:
            raise SchemaError(f"Structured output validation failed: {exc}") from exc

    @staticmethod
    def build_openai_response_format(model_class: Type[BaseModel]) -> dict[str, Any]:
        """Build OpenAI response_format parameter for JSON schema enforcement."""
        schema = StructuredOutput.get_json_schema(model_class)
        return {
            "type": "json_schema",
            "json_schema": {
                "name": model_class.__name__,
                "schema": schema,
                "strict": True,
            },
        }

    @staticmethod
    def extract_json_from_text(text: str) -> str:
        """Extract JSON from a text response that may contain markdown code blocks."""
        text = text.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            inner = []
            in_block = False
            for line in lines:
                if line.startswith("```") and not in_block:
                    in_block = True
                    continue
                if line.startswith("```") and in_block:
                    break
                if in_block:
                    inner.append(line)
            text = "\n".join(inner).strip()
        return text
