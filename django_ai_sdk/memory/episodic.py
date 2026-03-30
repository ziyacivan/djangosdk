from __future__ import annotations

from typing import Any

from django_ai_sdk.memory.base import AbstractMemoryStore


class EpisodicMemory(AbstractMemoryStore):
    """
    DB-backed episodic memory store.

    Stores agent experiences and facts as ``Message`` records in a dedicated
    ``Conversation`` (tagged ``type=episodic_memory``). Episodes are evicted
    FIFO once ``max_episodes`` is reached.

    Example::

        class PersonalAssistant(Agent):
            episodic_memory = EpisodicMemory(max_episodes=100)

        agent = PersonalAssistant()
        agent.episodic_memory.add("user_name", "Alice")
        ctx = agent.episodic_memory.as_context()  # inject into system_prompt
    """

    def __init__(self, max_episodes: int = 100, namespace: str = "") -> None:
        self.max_episodes = max_episodes
        self.namespace = namespace  # scopes memory to an agent or user key

    def _agent_class_key(self) -> str:
        return self.namespace or "__episodic_memory__"

    def _get_or_create_memory_conversation(self):
        from django_ai_sdk.models.conversation import Conversation

        conv, _ = Conversation.objects.get_or_create(
            agent_class=self._agent_class_key(),
            defaults={"metadata": {"type": "episodic_memory"}},
        )
        return conv

    def add(self, key: str, value: Any, **kwargs) -> None:
        from django_ai_sdk.models.message import Message

        conv = self._get_or_create_memory_conversation()

        # Enforce max_episodes — evict oldest entry first
        count = Message.objects.filter(conversation=conv).count()
        if count >= self.max_episodes:
            oldest = (
                Message.objects.filter(conversation=conv)
                .order_by("created_at")
                .first()
            )
            if oldest:
                oldest.delete()

        Message.objects.create(
            conversation=conv,
            role=Message.Role.SYSTEM,
            content=f"{key}: {value}",
            tool_calls={"memory_key": key, "memory_value": str(value)},
        )

    def get(self, key: str, **kwargs) -> Any:
        from django_ai_sdk.models.message import Message

        conv = self._get_or_create_memory_conversation()
        msg = (
            Message.objects.filter(
                conversation=conv, tool_calls__memory_key=key
            )
            .order_by("-created_at")
            .first()
        )
        if msg and msg.tool_calls:
            return msg.tool_calls.get("memory_value")
        return None

    def list(self, **kwargs) -> list[dict]:
        from django_ai_sdk.models.message import Message

        conv = self._get_or_create_memory_conversation()
        msgs = (
            Message.objects.filter(conversation=conv)
            .order_by("-created_at")[: self.max_episodes]
        )
        result = []
        for m in msgs:
            if m.tool_calls and "memory_key" in m.tool_calls:
                result.append(
                    {
                        "key": m.tool_calls["memory_key"],
                        "value": m.tool_calls["memory_value"],
                        "created_at": m.created_at,
                    }
                )
        return result

    def as_context(self) -> str:
        items = self.list()
        if not items:
            return ""
        lines = ["## Episodic Memory", "Previous facts and experiences:"]
        for item in items:
            lines.append(f"- {item['key']}: {item['value']}")
        return "\n".join(lines)

    def clear(self, **kwargs) -> None:
        from django_ai_sdk.models.message import Message

        conv = self._get_or_create_memory_conversation()
        Message.objects.filter(conversation=conv).delete()

    # ------------------------------------------------------------------ async

    async def aadd(self, key: str, value: Any, **kwargs) -> None:
        from asgiref.sync import sync_to_async

        await sync_to_async(self.add)(key, value, **kwargs)

    async def aget(self, key: str, **kwargs) -> Any:
        from asgiref.sync import sync_to_async

        return await sync_to_async(self.get)(key, **kwargs)

    async def alist(self, **kwargs) -> list[dict]:
        from asgiref.sync import sync_to_async

        return await sync_to_async(self.list)(**kwargs)

    async def aclear(self, **kwargs) -> None:
        from asgiref.sync import sync_to_async

        await sync_to_async(self.clear)(**kwargs)
