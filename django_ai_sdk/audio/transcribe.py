from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Union


@dataclass
class TranscriptionResponse:
    text: str = ""
    language: str = ""
    duration: float = 0.0
    model: str = ""
    provider: str = ""
    raw: Any = None


def transcribe(
    audio_file: Union[str, bytes, os.PathLike],
    *,
    provider: str = "openai",
    model: str = "whisper-1",
    language: str | None = None,
    **kwargs,
) -> TranscriptionResponse:
    """
    Transcribe audio to text using Whisper or compatible models.

    Supported providers:
    - openai: whisper-1 (via litellm transcription)
    - groq: whisper-large-v3 (via litellm)

    ``audio_file`` can be:
    - A file path (str or PathLike) — the file is opened and streamed.
    - Raw bytes of an audio file.

    Example::

        result = transcribe("recording.mp3", provider="openai")
        print(result.text)

        result = transcribe("lecture.mp3", provider="groq", model="whisper-large-v3")
        print(result.text)
    """
    import litellm

    litellm_model = f"{provider}/{model}"

    call_kwargs: dict[str, Any] = {"model": litellm_model}
    if language:
        call_kwargs["language"] = language
    call_kwargs.update(kwargs)

    if isinstance(audio_file, (str, os.PathLike)):
        with open(audio_file, "rb") as fh:
            raw = litellm.transcription(file=fh, **call_kwargs)
    else:
        # bytes — wrap in a file-like object
        import io
        raw = litellm.transcription(file=io.BytesIO(audio_file), **call_kwargs)

    text = getattr(raw, "text", "") or ""
    detected_language = getattr(raw, "language", "") or ""
    duration = float(getattr(raw, "duration", 0.0) or 0.0)

    return TranscriptionResponse(
        text=text,
        language=detected_language,
        duration=duration,
        model=model,
        provider=provider,
        raw=raw,
    )


async def atranscribe(
    audio_file: Union[str, bytes, os.PathLike],
    **kwargs,
) -> TranscriptionResponse:
    """Async version of transcribe."""
    from asgiref.sync import sync_to_async

    return await sync_to_async(transcribe)(audio_file, **kwargs)
