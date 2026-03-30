import pytest
from pydantic import BaseModel
from django_ai_sdk.structured.output import StructuredOutput
from django_ai_sdk.exceptions import SchemaError


class OrderStatus(BaseModel):
    order_id: str
    status: str
    total: float


def test_get_json_schema():
    schema = StructuredOutput.get_json_schema(OrderStatus)
    assert schema["type"] == "object"
    assert "order_id" in schema["properties"]


def test_validate_from_dict():
    obj = StructuredOutput.validate(OrderStatus, {"order_id": "123", "status": "shipped", "total": 49.99})
    assert obj.order_id == "123"
    assert obj.status == "shipped"


def test_validate_from_json_string():
    obj = StructuredOutput.validate(OrderStatus, '{"order_id": "456", "status": "pending", "total": 10.0}')
    assert obj.order_id == "456"


def test_validate_invalid_raises():
    with pytest.raises(SchemaError):
        StructuredOutput.validate(OrderStatus, '{"bad": "data"}')


def test_extract_json_from_code_block():
    text = '```json\n{"order_id": "789", "status": "done", "total": 5.0}\n```'
    extracted = StructuredOutput.extract_json_from_text(text)
    obj = StructuredOutput.validate(OrderStatus, extracted)
    assert obj.order_id == "789"
