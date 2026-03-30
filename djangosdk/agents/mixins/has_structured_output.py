from __future__ import annotations

from typing import Any, Type

from pydantic import BaseModel


class HasStructuredOutput:
    """
    Mixin that adds Pydantic structured output validation to an Agent.

    Set ``output_schema`` to a Pydantic model class to have responses automatically
    validated and returned as ``response.structured``.

    Example::

        class OrderResponse(BaseModel):
            order_id: str
            status: str

        class OrderAgent(Agent):
            output_schema = OrderResponse
    """

    output_schema: Type[BaseModel] | None = None

    def _get_output_json_schema(self) -> dict[str, Any] | None:
        if self.output_schema is None:
            return None
        from djangosdk.structured.output import StructuredOutput
        return StructuredOutput.get_json_schema(self.output_schema)

    def _validate_structured_output(self, text: str) -> Any:
        if self.output_schema is None:
            return None
        from djangosdk.structured.output import StructuredOutput
        json_text = StructuredOutput.extract_json_from_text(text)
        return StructuredOutput.validate(self.output_schema, json_text)
