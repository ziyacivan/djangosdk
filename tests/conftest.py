"""
Shared pytest fixtures for django-ai-sdk tests.
"""
from __future__ import annotations

import pytest


@pytest.fixture
def fake_completion(monkeypatch):
    """
    Fixture that injects a MockLiteLLMCompletion as the default litellm backend.
    Returns the mock holder so tests can assert on calls.

    Usage::

        def test_something(fake_completion):
            fake_completion.configure(text="Hello!")
            response = agent.handle("Hi")
            assert response.text == "Hello!"
    """
    from django_ai_sdk.testing.mock_litellm import MockLiteLLMCompletion

    class _FakeCompletionFixture:
        def __init__(self):
            self._ctx = None
            self._mock = None
            self._kwargs = {"text": "Fake response."}

        def configure(self, **kwargs):
            self._kwargs.update(kwargs)
            return self

        def __enter__(self):
            self._ctx = MockLiteLLMCompletion(**self._kwargs)
            self._mock = self._ctx.__enter__()
            return self._mock

        def __exit__(self, *args):
            if self._ctx:
                self._ctx.__exit__(*args)

    return _FakeCompletionFixture()


@pytest.fixture
def mcp_http_transport():
    """
    Fixture that patches urllib.request.urlopen for MCP HTTP transport tests.
    Returns a callable that configures the mocked JSON response.
    """
    import json
    from unittest.mock import MagicMock, patch

    responses = []

    def _set_response(data: dict):
        responses.append(data)

    mock_urlopen = MagicMock()

    def _urlopen_side_effect(req, **kwargs):
        if responses:
            payload = responses.pop(0)
        else:
            payload = {"jsonrpc": "2.0", "id": "1", "result": {}}
        resp = MagicMock()
        resp.read.return_value = json.dumps(payload).encode()
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        return resp

    mock_urlopen.side_effect = _urlopen_side_effect

    with patch("urllib.request.urlopen", mock_urlopen):
        _set_response.mock = mock_urlopen
        yield _set_response


@pytest.fixture(autouse=False)
def reset_mcp_registry():
    """
    Fixture that resets the global MCP tool/resource registries before each test.
    Use when tests register @mcp_tool or @mcp_resource functions.
    """
    from django_ai_sdk.mcp import decorators
    original_tools = dict(decorators._mcp_tools)
    original_resources = dict(decorators._mcp_resources)
    decorators._mcp_tools.clear()
    decorators._mcp_resources.clear()
    yield
    decorators._mcp_tools.clear()
    decorators._mcp_tools.update(original_tools)
    decorators._mcp_resources.clear()
    decorators._mcp_resources.update(original_resources)
