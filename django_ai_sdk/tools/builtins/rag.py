from __future__ import annotations

from typing import Any


class RAGTool:
    """
    Built-in Retrieval-Augmented Generation tool backed by pgvector.

    Requires ``pgvector`` extension in PostgreSQL and the ``pgvector`` Python
    package (``pip install pgvector``).

    Example::

        from django_ai_sdk.tools.builtins import RAGTool

        class DocumentAgent(Agent):
            tools = [
                RAGTool(
                    model=Document,
                    embedding_field="embedding",
                    text_field="content",
                    provider="openai",
                )
            ]
            system_prompt = "Search the document database and answer questions."

    The agent calls ``rag_search(query="…", top_k=5)`` automatically.
    """

    name = "rag_search"
    description = (
        "Search the document database using semantic similarity and return the "
        "most relevant passages. Use this tool to answer questions about stored documents."
    )

    def __init__(
        self,
        model: Any,
        embedding_field: str = "embedding",
        text_field: str = "content",
        top_k: int = 5,
        provider: str = "openai",
        embedding_model: str | None = None,
        metadata_fields: list[str] | None = None,
    ) -> None:
        self._model = model
        self._embedding_field = embedding_field
        self._text_field = text_field
        self._top_k = top_k
        self._provider = provider
        self._embedding_model = embedding_model
        self._metadata_fields = metadata_fields or []

    def __call__(self, query: str, top_k: int | None = None) -> list[dict]:
        return self.search(query, top_k=top_k or self._top_k)

    def search(self, query: str, top_k: int | None = None) -> list[dict]:
        from django_ai_sdk.embeddings import embed

        limit = top_k or self._top_k

        try:
            query_vector = embed(query, provider=self._provider, model=self._embedding_model)
        except Exception as exc:
            return [{"error": f"Embedding failed: {exc}"}]

        try:
            from pgvector.django import CosineDistance
        except ImportError as exc:
            raise ImportError(
                "pgvector is required for RAGTool. Run: pip install pgvector"
            ) from exc

        qs = (
            self._model.objects.annotate(
                _similarity=CosineDistance(self._embedding_field, query_vector)
            )
            .filter(_similarity__lt=0.5)
            .order_by("_similarity")[:limit]
        )

        results = []
        for obj in qs:
            item: dict[str, Any] = {
                "text": getattr(obj, self._text_field, ""),
                "similarity": float(getattr(obj, "_similarity", 0)),
            }
            for field in self._metadata_fields:
                item[field] = getattr(obj, field, None)
            results.append(item)

        return results

    def to_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query for semantic similarity.",
                        },
                        "top_k": {
                            "type": "integer",
                            "description": f"Number of results to return (default {self._top_k}).",
                            "default": self._top_k,
                        },
                    },
                    "required": ["query"],
                },
            },
        }
