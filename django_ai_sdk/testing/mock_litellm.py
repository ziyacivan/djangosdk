"""
Mock helpers for litellm-backed modules.

Provides realistic fake response objects that match the attribute contracts
used throughout django-ai-sdk, so every external-API module can be tested
without network access.

Usage::

    from django_ai_sdk.testing.mock_litellm import (
        MockLiteLLMCompletion,
        MockLiteLLMEmbedding,
        MockLiteLLMImage,
        MockLiteLLMAudio,
        make_completion_response,
        make_stream_chunks,
        make_embedding_response,
        make_image_response,
    )

    with MockLiteLLMCompletion(text="Hello!") as mock:
        response = agent.handle("Hi")
    assert response.text == "Hello!"
"""

from __future__ import annotations

import contextlib
import json
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Response builders — return SimpleNamespace objects that mirror litellm's
# ModelResponse / EmbeddingResponse / ImageResponse attribute contracts.
# ---------------------------------------------------------------------------

def _make_usage(
    prompt_tokens: int = 10,
    completion_tokens: int = 5,
    total_tokens: int = 15,
    cached_tokens: int = 0,
) -> SimpleNamespace:
    details = SimpleNamespace(cached_tokens=cached_tokens)
    return SimpleNamespace(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        prompt_tokens_details=details,
    )


def _make_tool_call(
    tool_id: str = "call_abc",
    name: str = "my_tool",
    arguments: dict | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=tool_id,
        function=SimpleNamespace(
            name=name,
            arguments=json.dumps(arguments or {}),
        ),
    )


def make_completion_response(
    text: str = "Fake response.",
    model: str = "gpt-4o",
    thinking: str | None = None,
    tool_calls: list[dict] | None = None,
    prompt_tokens: int = 10,
    completion_tokens: int = 5,
    cached_tokens: int = 0,
) -> SimpleNamespace:
    """Build a fake litellm ``ModelResponse`` for ``litellm.completion()``."""
    raw_tool_calls = None
    if tool_calls:
        raw_tool_calls = [
            _make_tool_call(
                tool_id=tc.get("id", f"call_{i}"),
                name=tc["name"],
                arguments=tc.get("arguments", {}),
            )
            for i, tc in enumerate(tool_calls)
        ]

    message = SimpleNamespace(
        content=text,
        tool_calls=raw_tool_calls,
        thinking=thinking,
    )
    choice = SimpleNamespace(message=message)
    usage = _make_usage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        cached_tokens=cached_tokens,
    )
    return SimpleNamespace(
        choices=[choice],
        usage=usage,
        model=model,
    )


def make_stream_chunks(
    texts: list[str],
    thinking_prefix: str | None = None,
) -> list[SimpleNamespace]:
    """Build a list of fake streaming chunks for ``litellm.completion(stream=True)``."""
    chunks = []

    if thinking_prefix:
        delta = SimpleNamespace(content=None, thinking=thinking_prefix)
        chunks.append(SimpleNamespace(choices=[SimpleNamespace(delta=delta)]))

    for text in texts:
        delta = SimpleNamespace(content=text, thinking=None)
        chunks.append(SimpleNamespace(choices=[SimpleNamespace(delta=delta)]))

    return chunks


def make_embedding_response(
    vectors: list[list[float]] | None = None,
) -> SimpleNamespace:
    """Build a fake litellm ``EmbeddingResponse``."""
    vecs = vectors or [[0.1, 0.2, 0.3]]
    data = [{"embedding": v, "index": i} for i, v in enumerate(vecs)]
    return SimpleNamespace(data=data)


def make_image_response(
    url: str = "https://example.com/image.png",
    b64_json: str = "",
    revised_prompt: str = "",
) -> SimpleNamespace:
    """Build a fake litellm image generation response."""
    image_data = SimpleNamespace(
        url=url,
        b64_json=b64_json,
        revised_prompt=revised_prompt,
    )
    return SimpleNamespace(data=[image_data])


def make_audio_transcription_response(text: str = "Hello world.") -> SimpleNamespace:
    """Build a fake litellm speech-to-text response."""
    return SimpleNamespace(text=text)


def make_audio_speech_response(content: bytes = b"fake-audio-bytes") -> MagicMock:
    """Build a fake litellm TTS response whose .content is bytes."""
    mock = MagicMock()
    mock.content = content
    return mock


# ---------------------------------------------------------------------------
# Context managers — patch litellm at the call site.
# ---------------------------------------------------------------------------

@contextlib.contextmanager
def MockLiteLLMCompletion(
    text: str = "Fake response.",
    model: str = "gpt-4o",
    thinking: str | None = None,
    tool_calls: list[dict] | None = None,
    prompt_tokens: int = 10,
    completion_tokens: int = 5,
    cached_tokens: int = 0,
    stream_texts: list[str] | None = None,
):
    """
    Context manager that patches ``litellm.completion`` and ``litellm.acompletion``.

    Sync calls return a fake ModelResponse; async calls return the same via AsyncMock.
    When ``stream_texts`` is provided, streaming calls return an iterable of chunks.

    Example::

        with MockLiteLLMCompletion(text="Hi!") as mock:
            response = agent.handle("Hello")
        assert response.text == "Hi!"
        mock.completion.assert_called_once()
    """
    fake_response = make_completion_response(
        text=text,
        model=model,
        thinking=thinking,
        tool_calls=tool_calls,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cached_tokens=cached_tokens,
    )

    chunks = make_stream_chunks(stream_texts or [text])

    def _sync_completion(**kwargs):
        if kwargs.get("stream"):
            # Return an iterable of chunks; attach usage for the done sentinel
            mock_stream = iter(chunks)
            stream_obj = MagicMock()
            stream_obj.__iter__ = lambda s: mock_stream
            stream_obj.usage = fake_response.usage
            return stream_obj
        return fake_response

    async def _async_completion(**kwargs):
        if kwargs.get("stream"):
            async def _aiter():
                for c in chunks:
                    yield c
            stream_obj = _aiter()
            return stream_obj
        return fake_response

    mock_holder = SimpleNamespace()

    with patch("litellm.completion", side_effect=_sync_completion) as sync_mock, \
         patch("litellm.acompletion", new_callable=AsyncMock, side_effect=_async_completion) as async_mock:
        mock_holder.completion = sync_mock
        mock_holder.acompletion = async_mock
        yield mock_holder


@contextlib.contextmanager
def MockLiteLLMEmbedding(
    vectors: list[list[float]] | None = None,
):
    """
    Context manager that patches ``litellm.embedding`` and ``litellm.aembedding``.

    Example::

        with MockLiteLLMEmbedding(vectors=[[0.1, 0.2]]) as mock:
            vec = embed("hello")
        assert vec == [0.1, 0.2]
    """
    fake_response = make_embedding_response(vectors)

    async def _aembedding(**kwargs):
        return fake_response

    with patch("litellm.embedding", return_value=fake_response) as sync_mock, \
         patch("litellm.aembedding", new_callable=AsyncMock, side_effect=_aembedding) as async_mock:
        yield SimpleNamespace(embedding=sync_mock, aembedding=async_mock)


@contextlib.contextmanager
def MockLiteLLMImage(
    url: str = "https://example.com/image.png",
    b64_json: str = "",
    revised_prompt: str = "",
):
    """
    Context manager that patches ``litellm.image_generation``.

    Example::

        with MockLiteLLMImage(url="https://img.example.com/abc.png") as mock:
            result = generate_image("a sunset")
        assert result.url == "https://img.example.com/abc.png"
    """
    fake = make_image_response(url=url, b64_json=b64_json, revised_prompt=revised_prompt)
    with patch("litellm.image_generation", return_value=fake) as mock:
        yield mock


@contextlib.contextmanager
def MockLiteLLMAudio(
    transcription_text: str = "Hello world.",
    speech_content: bytes = b"fake-audio",
):
    """
    Context manager that patches litellm speech/transcription calls.

    Example::

        with MockLiteLLMAudio(transcription_text="Django is great.") as mock:
            result = transcribe("/tmp/audio.mp3")
        assert result.text == "Django is great."
    """
    fake_transcription = make_audio_transcription_response(transcription_text)
    fake_speech = make_audio_speech_response(speech_content)

    # litellm uses different call paths for transcription vs. speech
    with patch("litellm.transcription", return_value=fake_transcription) as t_mock, \
         patch("litellm.speech", return_value=fake_speech) as s_mock:
        yield SimpleNamespace(transcription=t_mock, speech=s_mock)
