import pytest
from django_ai_sdk.tools.decorator import tool, _build_tool_schema
from django_ai_sdk.tools.registry import ToolRegistry
from django_ai_sdk.exceptions import ToolError


@tool
def get_weather(city: str, unit: str = "celsius") -> dict:
    """Get the current weather for a city.

    Args:
        city: The city name.
        unit: Temperature unit.
    """
    return {"city": city, "temp": 22, "unit": unit}


def test_tool_decorator_marks_function():
    assert hasattr(get_weather, "__tool__")
    assert get_weather.__tool__ is True


def test_tool_schema_structure():
    schema = get_weather.__tool_schema__
    assert schema["type"] == "function"
    fn = schema["function"]
    assert fn["name"] == "get_weather"
    assert "city" in fn["parameters"]["properties"]
    assert "city" in fn["parameters"]["required"]
    assert "unit" not in fn["parameters"]["required"]


def test_tool_registry_execute():
    registry = ToolRegistry()
    registry.register(get_weather)
    result = registry.execute("get_weather", {"city": "Istanbul"})
    assert result["city"] == "Istanbul"


def test_tool_registry_unknown_tool():
    registry = ToolRegistry()
    with pytest.raises(ToolError):
        registry.execute("nonexistent", {})


@pytest.mark.asyncio
async def test_tool_registry_aexecute():
    registry = ToolRegistry()
    registry.register(get_weather)
    result = await registry.aexecute("get_weather", {"city": "Ankara"})
    assert result["city"] == "Ankara"
