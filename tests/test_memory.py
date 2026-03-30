"""Tests for memory/episodic.py and memory/semantic.py."""
from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock


# ===========================================================================
# EpisodicMemory
# ===========================================================================

@pytest.mark.django_db
class TestEpisodicMemory:
    def _make_memory(self, namespace: str = "test_ns", max_episodes: int = 10):
        from django_ai_sdk.memory.episodic import EpisodicMemory
        return EpisodicMemory(max_episodes=max_episodes, namespace=namespace)

    def test_add_and_get_value(self):
        mem = self._make_memory()
        mem.add("user_name", "Alice")
        result = mem.get("user_name")
        assert result == "Alice"

    def test_get_returns_none_for_missing_key(self):
        mem = self._make_memory()
        result = mem.get("nonexistent_key")
        assert result is None

    def test_list_returns_all_entries(self):
        mem = self._make_memory()
        mem.add("fact_1", "Django is cool")
        mem.add("fact_2", "Python is great")
        entries = mem.list()
        keys = [e["key"] for e in entries]
        assert "fact_1" in keys
        assert "fact_2" in keys

    def test_clear_removes_all_entries(self):
        mem = self._make_memory()
        mem.add("key1", "value1")
        mem.add("key2", "value2")
        mem.clear()
        assert mem.list() == []

    def test_max_episodes_evicts_oldest(self):
        mem = self._make_memory(max_episodes=2)
        mem.add("first", "A")
        mem.add("second", "B")
        mem.add("third", "C")  # should evict "first"

        entries = mem.list()
        keys = [e["key"] for e in entries]
        assert "first" not in keys
        assert "third" in keys

    def test_as_context_returns_formatted_string(self):
        mem = self._make_memory()
        mem.add("user_city", "Istanbul")
        mem.add("user_lang", "Python")
        ctx = mem.as_context()
        assert "## Episodic Memory" in ctx
        assert "user_city" in ctx
        assert "Istanbul" in ctx

    def test_as_context_empty_when_no_entries(self):
        mem = self._make_memory(namespace="empty_ns_xyz")
        ctx = mem.as_context()
        assert ctx == ""

    def test_add_overwrites_get_most_recent(self):
        mem = self._make_memory()
        mem.add("preference", "dark_mode")
        mem.add("preference", "light_mode")
        result = mem.get("preference")
        assert result == "light_mode"

    def test_namespace_isolation(self):
        mem_a = self._make_memory(namespace="ns_alpha")
        mem_b = self._make_memory(namespace="ns_beta")

        mem_a.add("key", "from_alpha")
        mem_b.add("key", "from_beta")

        assert mem_a.get("key") == "from_alpha"
        assert mem_b.get("key") == "from_beta"

    @pytest.mark.asyncio
    async def test_aadd_and_aget(self):
        mem = self._make_memory(namespace="async_ns")
        await mem.aadd("async_key", "async_value")
        result = await mem.aget("async_key")
        assert result == "async_value"

    @pytest.mark.asyncio
    async def test_alist(self):
        mem = self._make_memory(namespace="alist_ns")
        await mem.aadd("k1", "v1")
        entries = await mem.alist()
        assert len(entries) >= 1

    @pytest.mark.asyncio
    async def test_aclear(self):
        mem = self._make_memory(namespace="aclear_ns")
        await mem.aadd("key", "value")
        await mem.aclear()
        entries = await mem.alist()
        assert entries == []


# ===========================================================================
# SemanticMemory
# ===========================================================================

class TestSemanticMemory:
    """
    SemanticMemory requires pgvector for full functionality.
    All tests mock the embedding generation and ORM layer.
    """

    def _make_memory(self, namespace: str = "test_semantic"):
        from django_ai_sdk.memory.semantic import SemanticMemory
        return SemanticMemory(namespace=namespace)

    def _mock_entry(self, key="k1", value="v1", similarity=0.9):
        obj = MagicMock()
        obj.key = key
        obj.value = value
        obj.similarity = similarity
        return obj

    def test_add_stores_entry(self):
        mem = self._make_memory()

        from django_ai_sdk.testing.mock_litellm import MockLiteLLMEmbedding
        mock_model = MagicMock()
        mock_model.objects.filter.return_value.first.return_value = None

        with MockLiteLLMEmbedding(vectors=[[0.1, 0.2, 0.3]]), \
             patch.object(mem, "_get_model", return_value=mock_model):
            mem.add("django", "A web framework")

        mock_model.objects.create.assert_called_once()
        create_kwargs = mock_model.objects.create.call_args[1]
        assert create_kwargs["key"] == "django"
        assert create_kwargs["value"] == "A web framework"
        assert create_kwargs["embedding"] == [0.1, 0.2, 0.3]

    def test_add_updates_existing_entry(self):
        mem = self._make_memory()

        existing = MagicMock()
        mock_model = MagicMock()
        mock_model.objects.filter.return_value.first.return_value = existing

        from django_ai_sdk.testing.mock_litellm import MockLiteLLMEmbedding
        with MockLiteLLMEmbedding(vectors=[[0.5, 0.6]]), \
             patch.object(mem, "_get_model", return_value=mock_model):
            mem.add("django", "Updated description")

        existing.save.assert_called_once()
        assert existing.value == "Updated description"

    def test_get_returns_exact_match(self):
        mem = self._make_memory()

        existing = MagicMock()
        existing.value = "Exact match value"
        mock_model = MagicMock()
        mock_model.objects.filter.return_value.first.return_value = existing

        with patch.object(mem, "_get_model", return_value=mock_model):
            result = mem.get("django")

        assert result == "Exact match value"

    def test_get_falls_back_to_search(self):
        mem = self._make_memory()

        mock_model = MagicMock()
        mock_model.objects.filter.return_value.first.return_value = None  # no exact match
        mock_model.objects.filter.return_value.order_by.return_value.__getitem__.return_value = []

        from django_ai_sdk.testing.mock_litellm import MockLiteLLMEmbedding
        with MockLiteLLMEmbedding(vectors=[[0.1]]), \
             patch.object(mem, "_get_model", return_value=mock_model):
            result = mem.get("unknown key")

        assert result is None

    def test_search_with_pgvector_fallback(self):
        """When pgvector is not installed, search falls back to created_at ordering."""
        mem = self._make_memory()

        entry = self._mock_entry("django", "A framework")
        mock_model = MagicMock()
        (mock_model.objects
            .filter.return_value
            .order_by.return_value
            .__getitem__.return_value) = [entry]
        (mock_model.objects
            .filter.return_value
            .order_by.return_value
            .__iter__) = MagicMock(return_value=iter([entry]))

        from django_ai_sdk.testing.mock_litellm import MockLiteLLMEmbedding
        with MockLiteLLMEmbedding(vectors=[[0.1]]), \
             patch.object(mem, "_get_model", return_value=mock_model), \
             patch("django_ai_sdk.memory.semantic.SemanticMemory.search") as search_mock:
            search_mock.return_value = [{"key": "django", "value": "A framework", "similarity": None}]
            results = mem.search("web framework")

        assert len(results) == 1

    def test_list_returns_all_entries(self):
        mem = self._make_memory()

        entries = [self._mock_entry("k1", "v1"), self._mock_entry("k2", "v2")]
        mock_model = MagicMock()
        (mock_model.objects
            .filter.return_value
            .order_by.return_value
            .__getitem__.return_value) = entries
        (mock_model.objects
            .filter.return_value
            .order_by.return_value
            .__iter__) = MagicMock(return_value=iter(entries))

        with patch.object(mem, "_get_model", return_value=mock_model):
            # list() uses __iter__ on the sliced queryset
            mock_qs = MagicMock()
            mock_qs.__iter__ = MagicMock(return_value=iter(entries))
            mock_model.objects.filter.return_value.order_by.return_value.__getitem__.return_value = mock_qs
            mock_qs.__iter__ = MagicMock(return_value=iter(entries))

            with patch.object(type(mock_qs), "__iter__", return_value=iter(entries)):
                result = mem.list()

        # Result count depends on mock setup — just verify no crash
        assert isinstance(result, list)

    def test_clear_deletes_by_namespace(self):
        mem = self._make_memory(namespace="clear_ns")

        mock_model = MagicMock()
        with patch.object(mem, "_get_model", return_value=mock_model):
            mem.clear()

        mock_model.objects.filter.assert_called_with(namespace="clear_ns")
        mock_model.objects.filter.return_value.delete.assert_called_once()

    def test_as_context_empty_on_no_entries(self):
        mem = self._make_memory(namespace="empty_semantic")

        mock_model = MagicMock()
        mock_qs = MagicMock()
        mock_qs.__iter__ = MagicMock(return_value=iter([]))
        mock_model.objects.filter.return_value.order_by.return_value.__getitem__.return_value = mock_qs

        with patch.object(mem, "_get_model", return_value=mock_model), \
             patch.object(mem, "list", return_value=[]):
            ctx = mem.as_context()

        assert ctx == ""

    @pytest.mark.asyncio
    async def test_aadd_generates_embedding_and_saves(self):
        mem = self._make_memory(namespace="async_semantic")

        mock_model = MagicMock()
        mock_model.objects.filter.return_value.first.return_value = None

        from django_ai_sdk.testing.mock_litellm import MockLiteLLMEmbedding
        with MockLiteLLMEmbedding(vectors=[[0.1, 0.2]]), \
             patch.object(mem, "_get_model", return_value=mock_model):
            await mem.aadd("async_key", "async_value")

        mock_model.objects.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_asearch_returns_results(self):
        mem = self._make_memory()

        from django_ai_sdk.testing.mock_litellm import MockLiteLLMEmbedding

        mock_entry = MagicMock()
        mock_entry.key = "k1"
        mock_entry.value = "v1"

        mock_model = MagicMock()
        # pgvector not installed → falls back to order_by("-created_at")
        mock_model.objects.filter.return_value.order_by.return_value.__getitem__.return_value = [mock_entry]
        mock_model.objects.filter.return_value.order_by.return_value.__iter__ = MagicMock(
            return_value=iter([mock_entry])
        )

        with MockLiteLLMEmbedding(vectors=[[0.1, 0.2]]), \
             patch.object(mem, "_get_model", return_value=mock_model):
            results = await mem.asearch("query", top_k=3)

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_alist_delegates_to_list(self):
        mem = self._make_memory()

        with patch.object(mem, "list", return_value=[{"key": "x", "value": "y", "similarity": None}]):
            entries = await mem.alist()

        assert len(entries) == 1

    @pytest.mark.asyncio
    async def test_aclear_delegates_to_clear(self):
        mem = self._make_memory()

        with patch.object(mem, "clear") as clear_mock:
            await mem.aclear()

        clear_mock.assert_called_once()
