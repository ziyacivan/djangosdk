"""Tests for images/generate.py, audio/transcribe.py, audio/synthesize.py."""
from __future__ import annotations

import io
import pytest
from unittest.mock import patch
from django_ai_sdk.testing.mock_litellm import MockLiteLLMImage, MockLiteLLMAudio


# ===========================================================================
# Image generation
# ===========================================================================

class TestGenerateImage:
    def test_returns_image_response_with_url(self):
        from django_ai_sdk.images.generate import generate_image

        with MockLiteLLMImage(url="https://cdn.example.com/img.png") as mock:
            result = generate_image("A sunset over mountains")

        assert result.url == "https://cdn.example.com/img.png"
        assert result.model == "dall-e-3"
        assert result.provider == "openai"
        mock.assert_called_once()

    def test_returns_b64_json_response(self):
        from django_ai_sdk.images.generate import generate_image

        with MockLiteLLMImage(b64_json="base64encodeddata"):
            result = generate_image("test", response_format="b64_json")

        assert result.b64_json == "base64encodeddata"

    def test_revised_prompt_captured(self):
        from django_ai_sdk.images.generate import generate_image

        with MockLiteLLMImage(revised_prompt="Enhanced prompt"):
            result = generate_image("Original prompt")

        assert result.revised_prompt == "Enhanced prompt"

    def test_gemini_provider(self):
        from django_ai_sdk.images.generate import generate_image

        with MockLiteLLMImage(url="https://img.google.com/abc") as mock:
            result = generate_image(
                "A city skyline",
                provider="gemini",
                model="imagen-3.0-generate-002",
            )

        assert result.provider == "gemini"
        call_kwargs = mock.call_args[1]
        assert "gemini" in call_kwargs["model"]

    def test_custom_size_passed_to_litellm(self):
        from django_ai_sdk.images.generate import generate_image

        with MockLiteLLMImage() as mock:
            generate_image("test", size="512x512")

        call_kwargs = mock.call_args[1]
        assert call_kwargs["size"] == "512x512"

    def test_openai_quality_parameter(self):
        from django_ai_sdk.images.generate import generate_image

        with MockLiteLLMImage() as mock:
            generate_image("test", provider="openai", quality="hd")

        call_kwargs = mock.call_args[1]
        assert call_kwargs.get("quality") == "hd"

    def test_empty_data_returns_empty_url(self):
        from types import SimpleNamespace
        from django_ai_sdk.images.generate import generate_image

        with patch("litellm.image_generation", return_value=SimpleNamespace(data=[])):
            result = generate_image("test")

        assert result.url == ""

    @pytest.mark.asyncio
    async def test_agenerate_image(self):
        from django_ai_sdk.images.generate import agenerate_image

        with MockLiteLLMImage(url="https://async-img.example.com/pic.png"):
            result = await agenerate_image("async prompt")

        assert result.url == "https://async-img.example.com/pic.png"


# ===========================================================================
# Audio transcription
# ===========================================================================

class TestTranscribe:
    def test_transcribe_bytes_returns_text(self):
        from django_ai_sdk.audio.transcribe import transcribe

        audio_bytes = b"fake-audio-data"
        with MockLiteLLMAudio(transcription_text="Hello from bytes.") as mock:
            result = transcribe(audio_bytes)

        assert result.text == "Hello from bytes."
        mock.transcription.assert_called_once()

    def test_transcribe_file_path(self):
        from django_ai_sdk.audio.transcribe import transcribe

        fake_file = io.BytesIO(b"audio")
        with MockLiteLLMAudio(transcription_text="File audio text."), \
             patch("builtins.open", return_value=fake_file.__enter__()):
            result = transcribe("/tmp/audio.mp3")

        assert result.text == "File audio text."

    def test_transcribe_language_parameter(self):
        from django_ai_sdk.audio.transcribe import transcribe

        with MockLiteLLMAudio(transcription_text="Merhaba.") as mock:
            transcribe(b"audio", language="tr")

        call_kwargs = mock.transcription.call_args[1]
        assert call_kwargs.get("language") == "tr"

    def test_transcribe_custom_model(self):
        from django_ai_sdk.audio.transcribe import transcribe

        with MockLiteLLMAudio(transcription_text="Groq result.") as mock:
            transcribe(b"audio", provider="groq", model="whisper-large-v3")

        call_kwargs = mock.transcription.call_args[1]
        assert "whisper-large-v3" in call_kwargs.get("model", "")

    def test_transcribe_response_fields(self):
        from django_ai_sdk.audio.transcribe import transcribe

        with MockLiteLLMAudio(transcription_text="Test."):
            result = transcribe(b"audio", provider="openai", model="whisper-1")

        assert result.model == "whisper-1"
        assert result.provider == "openai"

    @pytest.mark.asyncio
    async def test_atranscribe(self):
        from django_ai_sdk.audio.transcribe import atranscribe

        with MockLiteLLMAudio(transcription_text="Async transcription."):
            result = await atranscribe(b"audio")

        assert result.text == "Async transcription."


# ===========================================================================
# Audio synthesis (TTS)
# ===========================================================================

class TestSynthesize:
    def test_synthesize_returns_audio_bytes(self):
        from django_ai_sdk.audio.synthesize import synthesize

        with MockLiteLLMAudio(speech_content=b"mp3-audio-data") as mock:
            result = synthesize("Hello world.")

        assert result.audio_bytes == b"mp3-audio-data"
        mock.speech.assert_called_once()

    def test_synthesize_default_model_and_voice(self):
        from django_ai_sdk.audio.synthesize import synthesize

        with MockLiteLLMAudio() as mock:
            synthesize("Test speech.")

        call_kwargs = mock.speech.call_args[1]
        assert "model" in call_kwargs
        assert "voice" in call_kwargs

    def test_synthesize_custom_voice(self):
        from django_ai_sdk.audio.synthesize import synthesize

        with MockLiteLLMAudio() as mock:
            synthesize("Test", voice="nova")

        call_kwargs = mock.speech.call_args[1]
        assert call_kwargs.get("voice") == "nova"

    def test_synthesize_custom_format(self):
        from django_ai_sdk.audio.synthesize import synthesize

        with MockLiteLLMAudio(speech_content=b"opus-data") as mock:
            result = synthesize("Test", response_format="opus")

        assert result.audio_bytes == b"opus-data"
        call_kwargs = mock.speech.call_args[1]
        assert call_kwargs.get("response_format") == "opus"

    def test_synthesize_content_type_for_wav(self):
        from django_ai_sdk.audio.synthesize import synthesize

        with MockLiteLLMAudio():
            result = synthesize("Test", response_format="wav")

        assert "wav" in result.content_type

    def test_synthesize_response_fields(self):
        from django_ai_sdk.audio.synthesize import synthesize

        with MockLiteLLMAudio():
            result = synthesize("Hello", provider="openai", model="tts-1-hd")

        assert result.model == "tts-1-hd"
        assert result.provider == "openai"

    @pytest.mark.asyncio
    async def test_asynthesize(self):
        from django_ai_sdk.audio.synthesize import asynthesize

        with MockLiteLLMAudio(speech_content=b"async-audio"):
            result = await asynthesize("Async TTS test.")

        assert result.audio_bytes == b"async-audio"
