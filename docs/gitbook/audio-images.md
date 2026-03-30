# Audio & Images

`django-ai-sdk` provides APIs for audio transcription, text-to-speech synthesis, and image generation.

## Audio

### Transcription (Speech-to-Text)

```python
from django_ai_sdk.audio.transcribe import transcribe, atranscribe

# Synchronous
transcript = transcribe("/path/to/audio.mp3", model="whisper-1")
print(transcript.text)

# Async
transcript = await atranscribe("/path/to/audio.mp3")
```

**Supported models:** OpenAI Whisper (`whisper-1`), Groq Whisper (`whisper-large-v3`), and any model supported by litellm.

### Synthesis (Text-to-Speech)

```python
from django_ai_sdk.audio.synthesize import synthesize, asynthesize

audio_bytes = synthesize(
    "Hello, how can I help you today?",
    model="tts-1",
    voice="alloy",
)

with open("output.mp3", "wb") as f:
    f.write(audio_bytes)
```

**Supported voices (OpenAI):** `alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer`

### In a Django View

```python
from django.http import HttpResponse
from django_ai_sdk.audio.synthesize import synthesize

def speak_view(request):
    text = request.GET.get("text", "Hello!")
    audio = synthesize(text)
    return HttpResponse(audio, content_type="audio/mpeg")
```

## Images

### Image Generation

```python
from django_ai_sdk.images.generate import generate_image, agenerate_image

result = generate_image(
    prompt="A Django logo made of geometric shapes, minimalist style",
    model="dall-e-3",
    size="1024x1024",
    quality="standard",
)

print(result.url)      # URL to the generated image
print(result.b64)      # Base64-encoded image data (if requested)
```

**Supported models:**
- OpenAI: `dall-e-3`, `dall-e-2`
- Google: `imagen-3` (via Vertex AI)
- xAI: `grok-2-image` (Aurora)

### In a Django View

```python
from django.http import JsonResponse
from django_ai_sdk.images.generate import generate_image

def generate_view(request):
    prompt = request.POST.get("prompt", "")
    result = generate_image(prompt=prompt, model="dall-e-3")
    return JsonResponse({"image_url": result.url})
```

## Configuration

```python
AI_SDK = {
    "PROVIDERS": {
        "openai": {"api_key": env("OPENAI_API_KEY")},
    },
    "AUDIO": {
        "DEFAULT_MODEL": "whisper-1",
        "TTS_MODEL": "tts-1",
        "TTS_VOICE": "alloy",
    },
    "IMAGES": {
        "DEFAULT_MODEL": "dall-e-3",
        "DEFAULT_SIZE": "1024x1024",
    },
}
```
