"""Tests for built-in tools: web_search, web_fetch, rag."""
from __future__ import annotations

import json
import sys
import types
import pytest
from unittest.mock import MagicMock, patch


# ===========================================================================
# WebSearchTool
# ===========================================================================

def _mock_ddg_response(abstract: str = "", related: list = None) -> bytes:
    data = {
        "Heading": "Django",
        "AbstractText": abstract,
        "AbstractURL": "https://djangoproject.com",
        "RelatedTopics": related or [],
    }
    return json.dumps(data).encode("utf-8")


def _mock_urlopen(response_bytes: bytes):
    mock_resp = MagicMock()
    mock_resp.read.return_value = response_bytes
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


class TestWebSearchTool:
    def test_search_returns_abstract(self):
        from django_ai_sdk.tools.builtins.web_search import WebSearchTool

        tool = WebSearchTool()
        with patch("urllib.request.urlopen", return_value=_mock_urlopen(
            _mock_ddg_response(abstract="Django is a web framework.")
        )):
            results = tool.search("Django framework")

        assert len(results) >= 1
        assert results[0]["snippet"] == "Django is a web framework."

    def test_search_returns_related_topics(self):
        from django_ai_sdk.tools.builtins.web_search import WebSearchTool

        tool = WebSearchTool()
        related = [
            {"Text": "Django REST framework", "FirstURL": "https://www.django-rest-framework.org"},
            {"Text": "Django ORM", "FirstURL": "https://djangoproject.com/orm"},
        ]
        with patch("urllib.request.urlopen", return_value=_mock_urlopen(
            _mock_ddg_response(related=related)
        )):
            results = tool.search("Django", max_results=5)

        assert any("REST framework" in r["snippet"] for r in results)

    def test_search_respects_max_results(self):
        from django_ai_sdk.tools.builtins.web_search import WebSearchTool

        tool = WebSearchTool()
        related = [{"Text": f"Topic {i}", "FirstURL": f"https://example.com/{i}"} for i in range(10)]
        with patch("urllib.request.urlopen", return_value=_mock_urlopen(
            _mock_ddg_response(related=related)
        )):
            results = tool.search("query", max_results=3)

        assert len(results) <= 3

    def test_search_returns_error_on_network_failure(self):
        from django_ai_sdk.tools.builtins.web_search import WebSearchTool

        tool = WebSearchTool()
        with patch("urllib.request.urlopen", side_effect=OSError("network error")):
            results = tool.search("test")

        assert len(results) == 1
        assert "error" in results[0]

    def test_callable_interface(self):
        from django_ai_sdk.tools.builtins.web_search import WebSearchTool

        tool = WebSearchTool()
        with patch("urllib.request.urlopen", return_value=_mock_urlopen(
            _mock_ddg_response(abstract="Result.")
        )):
            results = tool(query="test")

        assert isinstance(results, list)

    def test_to_schema_returns_valid_schema(self):
        from django_ai_sdk.tools.builtins.web_search import WebSearchTool

        tool = WebSearchTool()
        schema = tool.to_schema()
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "web_search"
        assert "query" in schema["function"]["parameters"]["properties"]


# ===========================================================================
# WebFetchTool
# ===========================================================================

class TestWebFetchTool:
    def test_fetch_strips_html_tags(self):
        from django_ai_sdk.tools.builtins.web_fetch import WebFetchTool

        tool = WebFetchTool()
        html = "<html><body><h1>Hello</h1><p>World paragraph.</p></body></html>"
        with patch("urllib.request.urlopen", return_value=_mock_urlopen(html.encode())):
            result = tool.fetch("https://example.com")

        assert "<h1>" not in result
        assert "Hello" in result

    def test_fetch_truncates_to_max_chars(self):
        from django_ai_sdk.tools.builtins.web_fetch import WebFetchTool

        tool = WebFetchTool()
        long_html = "<p>" + "x" * 10000 + "</p>"
        with patch("urllib.request.urlopen", return_value=_mock_urlopen(long_html.encode())):
            result = tool.fetch("https://example.com", max_chars=100)

        assert len(result) <= 100

    def test_fetch_callable_interface(self):
        from django_ai_sdk.tools.builtins.web_fetch import WebFetchTool

        tool = WebFetchTool()
        html = "<p>Content.</p>"
        with patch("urllib.request.urlopen", return_value=_mock_urlopen(html.encode())):
            result = tool(url="https://example.com")

        assert "Content" in result

    def test_fetch_returns_error_string_on_failure(self):
        from django_ai_sdk.tools.builtins.web_fetch import WebFetchTool

        tool = WebFetchTool()
        with patch("urllib.request.urlopen", side_effect=OSError("403 Forbidden")):
            result = tool.fetch("https://example.com")

        assert "403 Forbidden" in result or "error" in result.lower()

    def test_to_schema_returns_valid_schema(self):
        from django_ai_sdk.tools.builtins.web_fetch import WebFetchTool

        tool = WebFetchTool()
        schema = tool.to_schema()
        assert schema["type"] == "function"
        assert "url" in schema["function"]["parameters"]["properties"]


# ===========================================================================
# RAGTool
# ===========================================================================

class TestRAGTool:
    def _make_model_class(self):
        """Build a minimal fake Django model class for RAGTool."""
        mock_model = MagicMock()
        return mock_model

    def _inject_fake_pgvector(self):
        """Inject fake pgvector modules so imports succeed without the real package."""
        mock_cosine = MagicMock()
        fake_pgvector_django = types.ModuleType("pgvector.django")
        fake_pgvector_django.CosineDistance = mock_cosine
        fake_pgvector = types.ModuleType("pgvector")
        fake_pgvector.django = fake_pgvector_django
        sys.modules["pgvector"] = fake_pgvector
        sys.modules["pgvector.django"] = fake_pgvector_django
        # Force reimport of rag module with fake pgvector available
        sys.modules.pop("django_ai_sdk.tools.builtins.rag", None)
        return mock_cosine

    def _remove_fake_pgvector(self):
        sys.modules.pop("pgvector", None)
        sys.modules.pop("pgvector.django", None)
        sys.modules.pop("django_ai_sdk.tools.builtins.rag", None)

    def test_search_calls_embed_and_queryset(self):
        mock_cosine_cls = self._inject_fake_pgvector()
        try:
            from django_ai_sdk.tools.builtins.rag import RAGTool
            from django_ai_sdk.testing.mock_litellm import MockLiteLLMEmbedding

            mock_model = self._make_model_class()

            # Mock the annotated queryset result (pgvector path: annotate → filter → order_by)
            mock_obj = MagicMock()
            mock_obj.content = "Django is a web framework."
            mock_obj.similarity = 0.9
            mock_model.objects.filter.return_value.annotate.return_value.order_by.return_value.__getitem__.return_value = [mock_obj]
            mock_model.objects.filter.return_value.annotate.return_value.order_by.return_value.__iter__ = MagicMock(
                return_value=iter([mock_obj])
            )

            tool = RAGTool(model=mock_model, text_field="content")

            with MockLiteLLMEmbedding(vectors=[[0.1, 0.2, 0.3]]):
                results = tool.search("What is Django?", top_k=3)

            assert isinstance(results, list)
        finally:
            self._remove_fake_pgvector()

    def test_search_falls_back_on_import_error(self):
        """When pgvector is not installed, RAGTool raises ImportError."""
        from django_ai_sdk.tools.builtins.rag import RAGTool
        from django_ai_sdk.testing.mock_litellm import MockLiteLLMEmbedding

        mock_model = self._make_model_class()
        tool = RAGTool(model=mock_model, text_field="content")

        with MockLiteLLMEmbedding(vectors=[[0.1, 0.2]]):
            with pytest.raises(ImportError, match="pgvector is required"):
                tool.search("query")

    def test_to_schema_returns_valid_schema(self):
        from django_ai_sdk.tools.builtins.rag import RAGTool

        mock_model = self._make_model_class()
        tool = RAGTool(model=mock_model)
        schema = tool.to_schema()
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "rag_search"
        assert "query" in schema["function"]["parameters"]["properties"]

    def test_search_returns_error_dict_on_embedding_failure(self):
        from django_ai_sdk.tools.builtins.rag import RAGTool

        mock_model = self._make_model_class()
        tool = RAGTool(model=mock_model)

        with patch("litellm.embedding", side_effect=Exception("embed failed")):
            results = tool.search("test query")

        assert len(results) == 1
        assert "error" in results[0]
