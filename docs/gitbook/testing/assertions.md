# Assertion Helpers

`django_ai_sdk.testing.assertions` provides helper functions that produce clear, descriptive failure messages when agent behavior does not match expectations.

## `assert_prompt_sent`

Assert that the agent sent a prompt containing a given substring to the provider.

```python
from django_ai_sdk.testing.assertions import assert_prompt_sent
from django_ai_sdk.testing.fakes import FakeProvider, override_ai_provider

def test_prompt_contains_order_id():
    fake = FakeProvider(text="Order found.")

    with override_ai_provider(fake):
        agent.handle("What is the status of order #XYZ789?")

    assert_prompt_sent(fake, "XYZ789")
```

Raises `AssertionError` with a descriptive message showing all prompts received if the substring is not found.

## `assert_tool_called`

Assert that the agent triggered a specific tool with the expected arguments.

```python
from django_ai_sdk.testing.assertions import assert_tool_called

fake = FakeProvider(
    text="Done.",
    tool_calls=[{"id": "1", "name": "cancel_order", "arguments": {"order_id": "XYZ"}}],
)

with override_ai_provider(fake):
    agent.handle("Cancel order XYZ")

assert_tool_called(fake, "cancel_order", order_id="XYZ")
```

## `assert_model_used`

Assert that every provider call used a specific model.

```python
from django_ai_sdk.testing.assertions import assert_model_used

with override_ai_provider(fake):
    agent.handle("Hello")

assert_model_used(fake, "gpt-4.1")
```

## `assert_system_prompt_contains`

Assert that the system prompt sent to the provider contains a given substring.

```python
from django_ai_sdk.testing.assertions import assert_system_prompt_contains

with override_ai_provider(fake):
    agent.handle("Hello")

assert_system_prompt_contains(fake, "customer support")
```

## Full Test Example

```python
import pytest
from django_ai_sdk.testing.fakes import FakeProvider, override_ai_provider
from django_ai_sdk.testing.assertions import (
    assert_prompt_sent,
    assert_tool_called,
    assert_model_used,
    assert_system_prompt_contains,
)
from myapp.agents import SupportAgent

@pytest.mark.django_db
def test_support_agent_cancels_order():
    fake = FakeProvider(
        text="Order ABC123 has been cancelled successfully.",
        tool_calls=[
            {
                "id": "call_1",
                "name": "cancel_order",
                "arguments": {"order_id": "ABC123"},
            }
        ],
    )

    with override_ai_provider(fake):
        response = SupportAgent().handle("Please cancel my order ABC123.")

    assert "cancelled" in response.text.lower()
    assert_prompt_sent(fake, "ABC123")
    assert_tool_called(fake, "cancel_order", order_id="ABC123")
    assert_model_used(fake, "gpt-4.1")
    assert_system_prompt_contains(fake, "customer support")
```
