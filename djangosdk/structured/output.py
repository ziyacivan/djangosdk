from __future__ import annotations

from typing import Any, Type

from pydantic import BaseModel

from djangosdk.exceptions import SchemaError


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
        """Extract JSON from a text response.

        Handles three formats in priority order:
        1. Markdown fenced code blocks (```json ... ``` or ``` ... ```)
        2. Already-valid bare JSON
        3. First top-level ``{...}`` or ``[...]`` found inside mixed prose
        """
        import json

        text = text.strip()

        # 1. Markdown fenced block
        if text.startswith("```"):
            lines = text.splitlines()
            inner: list[str] = []
            in_block = False
            for line in lines:
                if line.startswith("```") and not in_block:
                    in_block = True
                    continue
                if line.startswith("```") and in_block:
                    break
                if in_block:
                    inner.append(line)
            candidate = "\n".join(inner).strip()
            try:
                json.loads(candidate)
                return candidate
            except (json.JSONDecodeError, ValueError):
                pass

        # 2. Already valid JSON
        try:
            json.loads(text)
            return text
        except (json.JSONDecodeError, ValueError):
            pass

        # 3. Find the outermost { ... } or [ ... ] in mixed prose
        for start_char, end_char in (("{", "}"), ("[", "]")):
            start = text.find(start_char)
            if start == -1:
                continue
            depth = 0
            in_string = False
            escape_next = False
            for i, ch in enumerate(text[start:], start):
                if escape_next:
                    escape_next = False
                    continue
                if ch == "\\" and in_string:
                    escape_next = True
                    continue
                if ch == '"' and not escape_next:
                    in_string = not in_string
                    continue
                if in_string:
                    continue
                if ch == start_char:
                    depth += 1
                elif ch == end_char:
                    depth -= 1
                    if depth == 0:
                        candidate = text[start: i + 1]
                        try:
                            json.loads(candidate)
                            return candidate
                        except (json.JSONDecodeError, ValueError):
                            break

        return text
