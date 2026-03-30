from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class SynthesisResponse:
    audio_bytes: bytes = b""
    content_type: str = "audio/mpeg"
    model: str = ""
    provider: str = ""
    raw: Any = None


_FORMAT_TO_CONTENT_TYPE = {
    "mp3": "audio/mpeg",
    "opus": "audio/ogg; codecs=opus",
    "aac": "audio/aac",
    "flac": "audio/flac",
    "wav": "audio/wav",
    "pcm": "audio/pcm",
}


def synthesize(
    text: str,
    *,
    provider: str = "openai",
    model: str = "tts-1",
    voice: str = "alloy",
    speed: float = 1.0,
    response_format: str = "mp3",
    **kwargs,
) -> SynthesisResponse:
    """
    Synthesize text to speech.

    Supported providers:
    - openai: tts-1, tts-1-hd (via litellm speech)
    - voices: alloy, echo, fable, onyx, nova, shimmer

    The returned ``SynthesisResponse.audio_bytes`` contains the raw audio data
    in the requested ``response_format``.

    Example::

        audio = synthesize("Hello world", voice="alloy", provider="openai")
        with open("output.mp3", "wb") as f:
            f.write(audio.audio_bytes)
    """
    import litellm

    litellm_model = f"{provider}/{model}"

    call_kwargs: dict[str, Any] = {
        "model": litellm_model,
        "input": text,
        "voice": voice,
        "speed": speed,
        "response_format": response_format,
    }
    call_kwargs.update(kwargs)

    raw = litellm.speech(**call_kwargs)

    # litellm.speech() returns an object whose content can be read as bytes.
    # It may be an httpx.Response, a requests.Response, or a bytes-like object.
    audio_bytes: bytes = b""
    if hasattr(raw, "content"):
        audio_bytes = raw.content  # httpx / requests Response
    elif hasattr(raw, "read"):
        audio_bytes = raw.read()
    elif isinstance(raw, (bytes, bytearray)):
        audio_bytes = bytes(raw)

    content_type = _FORMAT_TO_CONTENT_TYPE.get(response_format, "audio/mpeg")

    return SynthesisResponse(
        audio_bytes=audio_bytes,
        content_type=content_type,
        model=model,
        provider=provider,
        raw=raw,
    )


async def asynthesize(text: str, **kwargs) -> SynthesisResponse:
    """Async version of synthesize."""
    from asgiref.sync import sync_to_async

    return await sync_to_async(synthesize)(text, **kwargs)
