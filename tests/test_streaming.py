from __future__ import annotations

import json

from djangosdk.agents.response import StreamChunk, UsageInfo
from djangosdk.streaming.sse import format_sse_chunk, iter_sse, SyncSSEResponse


def test_format_sse_text_delta():
    chunk = StreamChunk(type="text_delta", text="Hello")
    line = format_sse_chunk(chunk)
    assert line.startswith("data: ")
    payload = json.loads(line[len("data: "):].strip())
    assert payload["type"] == "text_delta"
    assert payload["text"] == "Hello"


def test_format_sse_thinking_delta():
    chunk = StreamChunk(type="thinking_delta", text="Thinking...", thinking=True)
    line = format_sse_chunk(chunk)
    payload = json.loads(line[len("data: "):].strip())
    assert payload["type"] == "thinking_delta"
    assert payload.get("thinking") is True


def test_format_sse_done_with_usage():
    usage = UsageInfo(prompt_tokens=10, completion_tokens=5, total_tokens=15)
    chunk = StreamChunk(type="done", usage=usage)
    line = format_sse_chunk(chunk)
    payload = json.loads(line[len("data: "):].strip())
    assert payload["type"] == "done"
    assert payload["usage"]["prompt_tokens"] == 10
    assert payload["usage"]["total_tokens"] == 15


def test_iter_sse_yields_formatted_chunks():
    chunks = [
        StreamChunk(type="text_delta", text="Hi"),
        StreamChunk(type="done"),
    ]
    lines = list(iter_sse(iter(chunks)))
    assert len(lines) == 2
    first = json.loads(lines[0][len("data: "):].strip())
    assert first["text"] == "Hi"


def test_sync_sse_response_content_type():
    def _chunks():
        yield StreamChunk(type="text_delta", text="A")
        yield StreamChunk(type="done")

    resp = SyncSSEResponse(_chunks())
    assert resp["Content-Type"] == "text/event-stream"
    assert resp["Cache-Control"] == "no-cache"
    assert resp["X-Accel-Buffering"] == "no"


def test_sync_sse_response_starts_with_retry():
    def _chunks():
        yield StreamChunk(type="done")

    resp = SyncSSEResponse(_chunks())
    content = b"".join(resp.streaming_content).decode()
    assert content.startswith("retry:")


def test_sync_sse_response_contains_data():
    def _chunks():
        yield StreamChunk(type="text_delta", text="world")
        yield StreamChunk(type="done")

    resp = SyncSSEResponse(_chunks())
    content = b"".join(resp.streaming_content).decode()
    assert '"text": "world"' in content or '"text":"world"' in content
