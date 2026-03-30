"""Tests for embeddings/embed.py."""
from __future__ import annotations

import pytest
from djangosdk.testing.mock_litellm import MockLiteLLMEmbedding


class TestEmbed:
    def test_embed_single_string_returns_vector(self):
        from djangosdk.embeddings.embed import embed

        with MockLiteLLMEmbedding(vectors=[[0.1, 0.2, 0.3]]):
            result = embed("Django is great.")

        # Single string input → single vector (not a list of lists)
        assert isinstance(result, list)
        assert result == [0.1, 0.2, 0.3]

    def test_embed_list_returns_list_of_vectors(self):
        from djangosdk.embeddings.embed import embed

        vecs = [[0.1, 0.2], [0.3, 0.4]]
        with MockLiteLLMEmbedding(vectors=vecs):
            result = embed(["text one", "text two"])

        assert len(result) == 2
        assert result[0] == [0.1, 0.2]
        assert result[1] == [0.3, 0.4]

    def test_embed_uses_correct_model_for_openai(self):
        from djangosdk.embeddings.embed import embed

        with MockLiteLLMEmbedding() as mock:
            embed("test", provider="openai")

        call_kwargs = mock.embedding.call_args[1]
        assert "text-embedding" in call_kwargs["model"]

    def test_embed_prefixes_provider_for_non_openai(self):
        from djangosdk.embeddings.embed import embed

        with MockLiteLLMEmbedding() as mock:
            embed("test", provider="gemini")

        call_kwargs = mock.embedding.call_args[1]
        assert "gemini/" in call_kwargs["model"]

    def test_embed_custom_model(self):
        from djangosdk.embeddings.embed import embed

        with MockLiteLLMEmbedding() as mock:
            embed("test", provider="openai", model="text-embedding-3-large")

        call_kwargs = mock.embedding.call_args[1]
        assert call_kwargs["model"] == "text-embedding-3-large"

    def test_embed_raises_provider_error_on_litellm_exception(self):
        from unittest.mock import patch
        from djangosdk.exceptions import ProviderError
        from djangosdk.embeddings.embed import embed

        with patch("litellm.embedding", side_effect=Exception("quota exceeded")):
            with pytest.raises(ProviderError, match="quota exceeded"):
                embed("test")

    @pytest.mark.asyncio
    async def test_aembed_single_string(self):
        from djangosdk.embeddings.embed import aembed

        with MockLiteLLMEmbedding(vectors=[[0.5, 0.6]]):
            result = await aembed("async test")

        assert result == [0.5, 0.6]

    @pytest.mark.asyncio
    async def test_aembed_list(self):
        from djangosdk.embeddings.embed import aembed

        with MockLiteLLMEmbedding(vectors=[[0.1], [0.2]]):
            result = await aembed(["a", "b"])

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_aembed_raises_provider_error(self):
        from unittest.mock import patch, AsyncMock
        from djangosdk.exceptions import ProviderError
        from djangosdk.embeddings.embed import aembed

        with patch("litellm.aembedding", new_callable=AsyncMock, side_effect=Exception("error")):
            with pytest.raises(ProviderError):
                await aembed("test")
