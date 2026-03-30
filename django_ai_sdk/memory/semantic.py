from __future__ import annotations

from typing import Any

from django_ai_sdk.memory.base import AbstractMemoryStore


class SemanticMemory(AbstractMemoryStore):
    """
    pgvector-backed semantic memory store.

    Generates embeddings via litellm and stores them in a ``SemanticMemoryEntry``
    ORM model. Retrieval uses cosine similarity search powered by pgvector.

    Required ORM model (add to django_ai_sdk/models/ and create a migration)::

        # django_ai_sdk/models/semantic_memory_entry.py
        import uuid
        from django.db import models
        try:
            from pgvector.django import VectorField
        except ImportError:
            VectorField = None  # fallback — migrations will fail without pgvector

        class SemanticMemoryEntry(models.Model):
            id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
            namespace = models.CharField(max_length=255, db_index=True)
            key = models.CharField(max_length=512)
            value = models.TextField()
            embedding = VectorField(dimensions=1536) if VectorField else models.JSONField(default=list)
            created_at = models.DateTimeField(auto_now_add=True)

            class Meta:
                ordering = ["-created_at"]
                indexes = [models.Index(fields=["namespace"])]

    Dependencies::

        pip install pgvector psycopg2-binary

    Example::

        class ResearchAgent(Agent):
            semantic_memory = SemanticMemory(namespace="research", max_results=5)

        agent = ResearchAgent()
        agent.semantic_memory.add("quantum computing", "A paradigm using quantum mechanics for computation")
        results = agent.semantic_memory.search("quantum physics", top_k=3)
        ctx = agent.semantic_memory.as_context()
    """

    def __init__(
        self,
        max_results: int = 5,
        namespace: str = "",
        embedding_model: str = "text-embedding-3-small",
        embedding_provider: str = "openai",
    ) -> None:
        self.max_results = max_results
        self.namespace = namespace or "__semantic_memory__"
        self.embedding_model = embedding_model
        self.embedding_provider = embedding_provider

    def _litellm_model_string(self) -> str:
        return f"{self.embedding_provider}/{self.embedding_model}"

    def _generate_embedding(self, text: str) -> list[float]:
        import litellm

        response = litellm.embedding(
            model=self._litellm_model_string(),
            input=[text],
        )
        return response.data[0]["embedding"]

    async def _agenerate_embedding(self, text: str) -> list[float]:
        import litellm

        response = await litellm.aembedding(
            model=self._litellm_model_string(),
            input=[text],
        )
        return response.data[0]["embedding"]

    def _get_model(self):
        from django_ai_sdk.models.semantic_memory_entry import SemanticMemoryEntry
        return SemanticMemoryEntry

    def add(self, key: str, value: Any, **kwargs) -> None:
        model = self._get_model()
        embedding = self._generate_embedding(f"{key} {value}")
        # Upsert: if same namespace+key exists, update it
        existing = model.objects.filter(namespace=self.namespace, key=key).first()
        if existing:
            existing.value = str(value)
            existing.embedding = embedding
            existing.save(update_fields=["value", "embedding"])
        else:
            model.objects.create(
                namespace=self.namespace,
                key=key,
                value=str(value),
                embedding=embedding,
            )

    def get(self, key: str, **kwargs) -> Any:
        """
        Returns the best semantically similar value for the given key query.
        Falls back to exact key lookup if pgvector is not available.
        """
        model = self._get_model()
        # Try exact match first
        exact = model.objects.filter(namespace=self.namespace, key=key).first()
        if exact:
            return exact.value

        # Semantic search fallback
        results = self.search(key, top_k=1)
        if results:
            return results[0]["value"]
        return None

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """
        Semantic search — returns top_k results ordered by cosine similarity.

        Each result is a dict with keys: key, value, similarity.
        Falls back to returning all entries ordered by created_at if pgvector
        cosine_distance is unavailable.
        """
        model = self._get_model()
        embedding = self._generate_embedding(query)

        try:
            from pgvector.django import CosineDistance

            qs = (
                model.objects.filter(namespace=self.namespace)
                .annotate(similarity=1 - CosineDistance("embedding", embedding))
                .order_by("-similarity")[: top_k]
            )
            return [
                {"key": entry.key, "value": entry.value, "similarity": float(entry.similarity)}
                for entry in qs
            ]
        except ImportError:
            # pgvector not installed — return entries without similarity scores
            qs = model.objects.filter(namespace=self.namespace).order_by("-created_at")[:top_k]
            return [
                {"key": entry.key, "value": entry.value, "similarity": None}
                for entry in qs
            ]

    def list(self, **kwargs) -> list[dict]:
        model = self._get_model()
        qs = model.objects.filter(namespace=self.namespace).order_by("-created_at")[: self.max_results]
        return [
            {"key": entry.key, "value": entry.value, "similarity": None}
            for entry in qs
        ]

    def as_context(self) -> str:
        items = self.list()
        if not items:
            return ""
        lines = ["## Semantic Memory"]
        for item in items:
            lines.append(f"- {item['key']}: {item['value']}")
        return "\n".join(lines)

    def clear(self, **kwargs) -> None:
        model = self._get_model()
        model.objects.filter(namespace=self.namespace).delete()

    # ------------------------------------------------------------------ async

    async def aadd(self, key: str, value: Any, **kwargs) -> None:
        model = self._get_model()
        embedding = await self._agenerate_embedding(f"{key} {value}")

        from asgiref.sync import sync_to_async

        @sync_to_async
        def _save():
            existing = model.objects.filter(namespace=self.namespace, key=key).first()
            if existing:
                existing.value = str(value)
                existing.embedding = embedding
                existing.save(update_fields=["value", "embedding"])
            else:
                model.objects.create(
                    namespace=self.namespace,
                    key=key,
                    value=str(value),
                    embedding=embedding,
                )

        await _save()

    async def aget(self, key: str, **kwargs) -> Any:
        from asgiref.sync import sync_to_async

        model = self._get_model()
        exact = await sync_to_async(
            lambda: model.objects.filter(namespace=self.namespace, key=key).first()
        )()
        if exact:
            return exact.value

        results = await self.asearch(key, top_k=1)
        if results:
            return results[0]["value"]
        return None

    async def asearch(self, query: str, top_k: int = 5) -> list[dict]:
        embedding = await self._agenerate_embedding(query)

        from asgiref.sync import sync_to_async

        @sync_to_async
        def _query():
            model = self._get_model()
            try:
                from pgvector.django import CosineDistance

                qs = (
                    model.objects.filter(namespace=self.namespace)
                    .annotate(similarity=1 - CosineDistance("embedding", embedding))
                    .order_by("-similarity")[:top_k]
                )
                return [
                    {"key": e.key, "value": e.value, "similarity": float(e.similarity)}
                    for e in qs
                ]
            except ImportError:
                qs = model.objects.filter(namespace=self.namespace).order_by("-created_at")[:top_k]
                return [{"key": e.key, "value": e.value, "similarity": None} for e in qs]

        return await _query()

    async def alist(self, **kwargs) -> list[dict]:
        from asgiref.sync import sync_to_async

        return await sync_to_async(self.list)(**kwargs)

    async def aclear(self, **kwargs) -> None:
        from asgiref.sync import sync_to_async

        await sync_to_async(self.clear)(**kwargs)
