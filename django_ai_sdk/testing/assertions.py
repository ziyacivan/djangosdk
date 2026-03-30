from __future__ import annotations

from typing import Any

from django_ai_sdk.testing.fakes import FakeProvider


def assert_prompt_sent(fake: FakeProvider, expected_substring: str) -> None:
    """
    Assert that at least one call to the provider contained ``expected_substring``
    in one of the user messages.

    Example::

        assert_prompt_sent(fake, "order #123")
    """
    for request in fake.calls:
        for msg in request.messages:
            if msg.get("role") == "user" and expected_substring in (msg.get("content") or ""):
                return
    all_prompts = [
        msg.get("content", "")
        for req in fake.calls
        for msg in req.messages
        if msg.get("role") == "user"
    ]
    raise AssertionError(
        f"Expected prompt containing {expected_substring!r} but got: {all_prompts!r}"
    )


def assert_tool_called(fake: FakeProvider, tool_name: str, **expected_args: Any) -> None:
    """
    Assert that the agent executed the named tool with the given arguments.

    Note: this checks tool_calls in the FakeProvider responses, not actual execution.
    For actual execution checking, inspect the agent's tool registry calls.

    Example::

        assert_tool_called(fake, "lookup_order", order_id="123")
    """
    for request in fake.calls:
        for tc in (fake._tool_calls or []):
            if tc.get("name") == tool_name:
                args = tc.get("arguments", tc.get("args", {}))
                if all(args.get(k) == v for k, v in expected_args.items()):
                    return

    raise AssertionError(
        f"Expected tool '{tool_name}' to be called with {expected_args!r}. "
        f"Configured tool_calls: {fake._tool_calls!r}"
    )


def assert_model_used(fake: FakeProvider, model: str) -> None:
    """Assert that every provider call used the given model."""
    for request in fake.calls:
        if request.model != model:
            raise AssertionError(
                f"Expected model '{model}' but got '{request.model}'"
            )


def assert_system_prompt_contains(fake: FakeProvider, substring: str) -> None:
    """Assert that at least one call included a system prompt containing ``substring``."""
    for request in fake.calls:
        if substring in request.system_prompt:
            return
    system_prompts = [req.system_prompt for req in fake.calls]
    raise AssertionError(
        f"Expected system prompt containing {substring!r} but got: {system_prompts!r}"
    )
