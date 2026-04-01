---
name: generate-media
description: >
  Scaffolds calls to the embeddings, audio (transcription/synthesis), and image
  generation modules. Invoke when the user says "generate an image", "transcribe
  audio", "generate speech", "use the images module", "add image generation to
  my agent", "process audio with the SDK", or "embed a document".
triggers:
  - generate an image
  - transcribe audio
  - generate speech
  - use the images module
  - add image generation to my agent
  - process audio with the SDK
  - embed a document
  - text to speech
  - speech to text
  - image generation
  - generate embeddings
  - embed text
  - DALL-E
  - Gemini image
---

# Generate Media with django-ai-sdk

You are using the media generation modules: `embeddings/`, `audio/`, and `images/`.

---

## Part 1 — Embeddings

### Generate a Text Embedding

```python
from djangosdk.embeddings.embed import embed, aembed


# Sync
vector = embed(
    text="Django is a high-level Python web framework.",
    model="text-embedding-3-small",
    provider="openai",
)
print(len(vector))  # 1536

# Async
vector = await aembed(
    text="Django is a high-level Python web framework.",
    model="text-embedding-3-small",
    provider="openai",
)
```

### Store Embeddings in a Django Model

```python
from django.db import models

try:
    from pgvector.django import VectorField
    EMBEDDING_FIELD = VectorField(dimensions=1536, null=True)
except ImportError:
    EMBEDDING_FIELD = models.JSONField(default=list)


class Document(models.Model):
    title = models.CharField(max_length=500)
    content = models.TextField()
    embedding = EMBEDDING_FIELD

    def save(self, *args, **kwargs):
        if self.content and not self.embedding:
            from djangosdk.embeddings.embed import embed
            self.embedding = embed(self.content)
        super().save(*args, **kwargs)
```

### Use with SemanticMemory (RAG)

For full RAG with agent memory, use `SemanticMemory` — it handles embedding generation automatically. See `scaffold-memory` skill.

---

## Part 2 — Audio

### Transcription (Speech → Text)

```python
from djangosdk.audio.transcribe import transcribe, atranscribe


# Sync — from file path
text = transcribe(
    audio_path="/path/to/recording.mp3",
    model="whisper-1",
    provider="openai",
    language="tr",   # optional: ISO 639-1 language code
)
print(text)

# Sync — from bytes
with open("recording.wav", "rb") as f:
    audio_bytes = f.read()

text = transcribe(audio_bytes=audio_bytes, model="whisper-1", provider="openai")

# Async
text = await atranscribe(audio_path="/path/to/audio.mp3", model="whisper-1")
```

### Speech Synthesis (Text → Audio)

```python
from djangosdk.audio.synthesize import synthesize, asynthesize


# Sync
audio_bytes = synthesize(
    text="Merhaba, nasıl yardımcı olabilirim?",
    model="tts-1",
    provider="openai",
    voice="nova",   # alloy | echo | fable | onyx | nova | shimmer
)

# Save to file
with open("response.mp3", "wb") as f:
    f.write(audio_bytes)

# Serve from Django view
from django.http import HttpResponse

def tts_view(request):
    text = request.GET.get("text", "Hello!")
    audio = synthesize(text=text, model="tts-1", voice="nova")
    return HttpResponse(audio, content_type="audio/mpeg")
```

### Voice Agent Pattern

Combine transcription + agent + synthesis for a voice interface:

```python
from djangosdk.audio.transcribe import transcribe
from djangosdk.audio.synthesize import synthesize
from myapp.agents import SupportAgent


def voice_agent(audio_path: str) -> bytes:
    """Transcribe audio, run agent, return spoken response."""
    text = transcribe(audio_path=audio_path, model="whisper-1")
    agent = SupportAgent()
    response = agent.handle(text)
    return synthesize(text=response.text, model="tts-1", voice="nova")
```

---

## Part 3 — Image Generation

### Generate an Image

```python
from djangosdk.images.generate import generate_image, agenerate_image


# OpenAI DALL-E 3
image_url = generate_image(
    prompt="A Django logo as a Renaissance oil painting",
    model="dall-e-3",
    provider="openai",
    size="1024x1024",
    quality="hd",
)
print(image_url)  # https://...

# Google Gemini Imagen
image_url = generate_image(
    prompt="A futuristic cityscape with Python code flowing through the sky",
    model="imagen-3.0-generate-001",
    provider="gemini",
)

# Async
image_url = await agenerate_image(
    prompt="A serene mountain landscape",
    model="dall-e-3",
    provider="openai",
)
```

### Agent That Generates Images

```python
from djangosdk.agents.base import Agent
from djangosdk.images.generate import generate_image
from djangosdk.tools.decorator import tool


@tool
def create_product_image(product_name: str, style: str = "photorealistic") -> str:
    """Generate a product image using DALL-E 3."""
    prompt = f"Professional product photo of {product_name}, {style} style, white background"
    url = generate_image(prompt=prompt, model="dall-e-3", provider="openai")
    return f"Generated image: {url}"


class ProductMarketingAgent(Agent):
    model = "gpt-4.1"
    system_prompt = "You are a product marketing assistant. Create compelling product images."
    tools = [create_product_image]
```

---

## Part 4 — Django Model Integration

### Store Generated Media URLs

```python
from django.db import models


class GeneratedImage(models.Model):
    prompt = models.TextField()
    image_url = models.URLField(max_length=2000)
    model = models.CharField(max_length=100, default="dall-e-3")
    created_at = models.DateTimeField(auto_now_add=True)

    @classmethod
    def create_from_prompt(cls, prompt: str) -> "GeneratedImage":
        from djangosdk.images.generate import generate_image
        url = generate_image(prompt=prompt, model="dall-e-3", provider="openai")
        return cls.objects.create(prompt=prompt, image_url=url)


class AudioTranscript(models.Model):
    audio_file = models.FileField(upload_to="audio/")
    transcript = models.TextField(blank=True)
    language = models.CharField(max_length=10, default="en")
    created_at = models.DateTimeField(auto_now_add=True)

    def transcribe(self) -> str:
        from djangosdk.audio.transcribe import transcribe
        text = transcribe(audio_path=self.audio_file.path, model="whisper-1")
        self.transcript = text
        self.save(update_fields=["transcript"])
        return text
```

---

## Part 5 — Test Media Modules

Mock media generation to avoid real API calls in tests:

```python
from unittest.mock import patch
import pytest


def test_image_generation_tool(fake_provider):
    with patch("djangosdk.images.generate.generate_image") as mock_gen:
        mock_gen.return_value = "https://example.com/generated.png"
        from myapp.agents import ProductMarketingAgent

        fake_provider.set_response(
            text="",
            tool_calls=[{"name": "create_product_image", "arguments": {"product_name": "Coffee Mug"}}]
        )
        fake_provider.set_response("Here's your product image: https://example.com/generated.png")

        agent = ProductMarketingAgent()
        agent._provider = fake_provider
        response = agent.handle("Create an image for Coffee Mug")

        mock_gen.assert_called_once()
        assert "Coffee Mug" in mock_gen.call_args[1]["prompt"]


def test_audio_transcription():
    with patch("djangosdk.audio.transcribe.transcribe") as mock_transcribe:
        mock_transcribe.return_value = "Hello, how can I help you?"
        from djangosdk.audio.transcribe import transcribe
        result = transcribe(audio_path="/fake/audio.mp3")
        assert result == "Hello, how can I help you?"
```
