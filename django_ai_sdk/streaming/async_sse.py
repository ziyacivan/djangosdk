from __future__ import annotations

import json
from typing import AsyncIterator

from django.http import StreamingHttpResponse

from django_ai_sdk.agents.response import StreamChunk
from django_ai_sdk.conf import ai_settings
from django_ai_sdk.streaming.sse import format_sse_chunk


async def aiter_sse(chunks: AsyncIterator[StreamChunk]) -> AsyncIterator[str]:
    """Yield SSE-formatted strings from an async StreamChunk iterator."""
    async for chunk in chunks:
        yield format_sse_chunk(chunk)


class AsyncSSEResponse(StreamingHttpResponse):
    """A Django StreamingHttpResponse for SSE from async generators."""

    def __init__(self, chunks: AsyncIterator[StreamChunk], **kwargs) -> None:
        retry_ms = ai_settings.get("STREAMING", {}).get("SSE_RETRY_MS", 3000)

        async def generator():
            yield f"retry: {retry_ms}\n\n"
            async for chunk in chunks:
                yield format_sse_chunk(chunk)

        super().__init__(
            streaming_content=generator(),
            content_type="text/event-stream",
            **kwargs,
        )
        self["Cache-Control"] = "no-cache"
        self["X-Accel-Buffering"] = "no"
