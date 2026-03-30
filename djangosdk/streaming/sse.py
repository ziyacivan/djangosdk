from __future__ import annotations

import json
from typing import Iterator

from django.http import StreamingHttpResponse

from djangosdk.agents.response import StreamChunk
from djangosdk.conf import ai_settings


def format_sse_chunk(chunk: StreamChunk) -> str:
    """Format a StreamChunk as an SSE data line."""
    data: dict = {"type": chunk.type}

    if chunk.type in ("text_delta", "thinking_delta"):
        data["text"] = chunk.text
        if chunk.thinking:
            data["thinking"] = True

    elif chunk.type == "done":
        if chunk.usage:
            data["usage"] = {
                "prompt_tokens": chunk.usage.prompt_tokens,
                "completion_tokens": chunk.usage.completion_tokens,
                "total_tokens": chunk.usage.total_tokens,
                "cache_read_tokens": chunk.usage.cache_read_tokens,
                "cache_write_tokens": chunk.usage.cache_write_tokens,
            }

    elif chunk.type == "tool_call" and chunk.tool_call:
        data["tool_call"] = chunk.tool_call

    separator = ai_settings.get("STREAMING", {}).get("CHUNK_SEPARATOR", "\n\n")
    return f"data: {json.dumps(data)}{separator}"


def iter_sse(chunks: Iterator[StreamChunk]) -> Iterator[str]:
    """Yield SSE-formatted strings from a StreamChunk iterator."""
    for chunk in chunks:
        yield format_sse_chunk(chunk)


class SyncSSEResponse(StreamingHttpResponse):
    """A Django StreamingHttpResponse for SSE from synchronous generators."""

    def __init__(self, chunks: Iterator[StreamChunk], **kwargs) -> None:
        retry_ms = ai_settings.get("STREAMING", {}).get("SSE_RETRY_MS", 3000)

        def generator():
            yield f"retry: {retry_ms}\n\n"
            yield from iter_sse(chunks)

        super().__init__(
            streaming_content=generator(),
            content_type="text/event-stream",
            **kwargs,
        )
        self["Cache-Control"] = "no-cache"
        self["X-Accel-Buffering"] = "no"
