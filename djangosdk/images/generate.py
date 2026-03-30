from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ImageResponse:
    url: str = ""
    b64_json: str = ""
    revised_prompt: str = ""
    model: str = ""
    provider: str = ""
    raw: Any = None


def generate_image(
    prompt: str,
    *,
    provider: str = "openai",
    model: str = "dall-e-3",
    size: str = "1024x1024",
    quality: str = "standard",
    n: int = 1,
    response_format: str = "url",
    **kwargs,
) -> ImageResponse:
    """
    Generate an image using the specified provider.

    Supported providers/models:
    - openai: dall-e-3, dall-e-2 (via litellm image_generation)
    - gemini: imagen-3.0-generate-002 (via litellm)
    - xai: aurora (via litellm)

    litellm model string format: ``provider/model``, e.g. ``openai/dall-e-3``.

    Example::

        img = generate_image("A sunset over mountains", provider="openai", size="1024x1024")
        print(img.url)

        img = generate_image(
            "A futuristic city",
            provider="gemini",
            model="imagen-3.0-generate-002",
        )
        print(img.url)
    """
    import litellm

    litellm_model = f"{provider}/{model}"

    call_kwargs: dict[str, Any] = {
        "model": litellm_model,
        "prompt": prompt,
        "n": n,
        "size": size,
    }

    # quality and response_format are supported by OpenAI; pass through for others
    if provider == "openai":
        call_kwargs["quality"] = quality
        call_kwargs["response_format"] = response_format

    call_kwargs.update(kwargs)

    raw = litellm.image_generation(**call_kwargs)

    # litellm returns an ImageResponse-like object with a .data list
    data = raw.data[0] if raw.data else {}

    url = getattr(data, "url", "") or (data.get("url", "") if isinstance(data, dict) else "")
    b64_json = getattr(data, "b64_json", "") or (data.get("b64_json", "") if isinstance(data, dict) else "")
    revised_prompt = (
        getattr(data, "revised_prompt", "")
        or (data.get("revised_prompt", "") if isinstance(data, dict) else "")
    )

    return ImageResponse(
        url=url or "",
        b64_json=b64_json or "",
        revised_prompt=revised_prompt or "",
        model=model,
        provider=provider,
        raw=raw,
    )


async def agenerate_image(prompt: str, **kwargs) -> ImageResponse:
    """Async version of generate_image."""
    from asgiref.sync import sync_to_async

    return await sync_to_async(generate_image)(prompt, **kwargs)
