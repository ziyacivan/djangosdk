from djangosdk.testing.assertions import (
    assert_model_used,
    assert_prompt_sent,
    assert_system_prompt_contains,
    assert_tool_called,
)
from djangosdk.testing.fakes import FakeAgent, FakeProvider, override_ai_provider
from djangosdk.testing.mock_litellm import (
    MockLiteLLMAudio,
    MockLiteLLMCompletion,
    MockLiteLLMEmbedding,
    MockLiteLLMImage,
    make_completion_response,
    make_embedding_response,
    make_image_response,
    make_stream_chunks,
)

__all__ = [
    # Fakes
    "FakeProvider",
    "FakeAgent",
    "override_ai_provider",
    # Assertions
    "assert_prompt_sent",
    "assert_tool_called",
    "assert_model_used",
    "assert_system_prompt_contains",
    # Mock context managers
    "MockLiteLLMCompletion",
    "MockLiteLLMEmbedding",
    "MockLiteLLMImage",
    "MockLiteLLMAudio",
    # Response builders
    "make_completion_response",
    "make_embedding_response",
    "make_image_response",
    "make_stream_chunks",
]
