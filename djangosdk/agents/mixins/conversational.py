from __future__ import annotations

import uuid
from typing import Any


class Conversational:
    """
    Mixin that adds conversation persistence to an Agent.

    Conversation history is stored via the ORM ``Conversation`` and ``Message`` models.

    Example::

        agent = SupportAgent()
        conv = agent.start_conversation()
        r1 = agent.with_conversation(conv.id).handle("Hello!")
        r2 = agent.with_conversation(conv.id).handle("Cancel my order.")
    """

    _conversation_id: str | None = None

    def with_conversation(self, conversation_id: str | uuid.UUID) -> "Conversational":
        """Return a copy of this agent bound to the given conversation."""
        import copy
        clone = copy.copy(self)
        clone._conversation_id = str(conversation_id)
        return clone

    def start_conversation(self, metadata: dict[str, Any] | None = None) -> Any:
        """Create and persist a new Conversation record, then return it."""
        from djangosdk.models.conversation import Conversation
        conv = Conversation.objects.create(
            agent_class=f"{self.__class__.__module__}.{self.__class__.__name__}",
            provider=getattr(self, "provider", ""),
            model=getattr(self, "model", ""),
            metadata=metadata or {},
        )
        self._conversation_id = str(conv.id)
        return conv

    def _maybe_auto_summarize(self, total_count: int, max_history: int) -> None:
        """
        When ``AUTO_SUMMARIZE`` is enabled and the conversation exceeds
        ``MAX_HISTORY``, generate a summary of older messages and store it as
        the first message so the context stays within the token budget.
        """
        from djangosdk.conf import ai_settings

        cfg = ai_settings.get("CONVERSATION", {})
        if not cfg.get("AUTO_SUMMARIZE", False):
            return
        if total_count <= max_history:
            return

        from djangosdk.models.message import Message
        from djangosdk.providers.registry import registry

        old_msgs = list(
            Message.objects.filter(conversation_id=self._conversation_id)
            .order_by("created_at")[: total_count - max_history]
        )
        if not old_msgs:
            return

        # Build a compact transcript for the summarization call
        transcript = "\n".join(
            f"{m.role.upper()}: {m.content}" for m in old_msgs if m.content
        )
        summarize_prompt = (
            f"Summarize the following conversation transcript concisely:\n\n{transcript}"
        )

        try:
            from djangosdk.agents.request import AgentRequest

            provider_name = getattr(self, "provider", "") or ai_settings.DEFAULT_PROVIDER
            model = getattr(self, "model", "") or ai_settings.DEFAULT_MODEL
            req = AgentRequest(
                messages=[{"role": "user", "content": summarize_prompt}],
                model=model,
                provider=provider_name,
                system_prompt="You are a helpful summarizer.",
            )
            provider = registry.get(provider_name)
            summary_response = provider.complete(req)
            summary_text = summary_response.text
        except Exception:
            summary_text = "[Earlier conversation summarized — full history unavailable.]"

        # Delete old messages and insert summary as a system message
        ids_to_delete = [m.id for m in old_msgs]
        Message.objects.filter(id__in=ids_to_delete).delete()
        Message.objects.create(
            conversation_id=self._conversation_id,
            role=Message.Role.SYSTEM,
            content=f"[Summary of earlier conversation]\n{summary_text}",
        )

    def _load_conversation_messages(self) -> list[dict[str, Any]]:
        """Load persisted messages for the current conversation."""
        if not self._conversation_id:
            return []

        from djangosdk.conf import ai_settings
        from djangosdk.models.message import Message

        max_history = ai_settings.get("CONVERSATION", {}).get("MAX_HISTORY", 50)

        total_count = Message.objects.filter(
            conversation_id=self._conversation_id
        ).count()
        self._maybe_auto_summarize(total_count, max_history)

        messages = (
            Message.objects
            .filter(conversation_id=self._conversation_id)
            .order_by("-created_at")[:max_history]
        )
        messages = list(reversed(messages))

        result = []
        for msg in messages:
            if msg.role == Message.Role.TOOL:
                result.append({
                    "role": "tool",
                    "tool_call_id": msg.tool_call_id or "",
                    "content": msg.content,
                })
            elif msg.tool_calls:
                result.append({
                    "role": msg.role,
                    "content": msg.content,
                    "tool_calls": msg.tool_calls,
                })
            else:
                result.append({"role": msg.role, "content": msg.content})
        return result

    def _persist_message(
        self,
        role: str,
        content: str,
        tool_calls: list | None = None,
        tool_call_id: str | None = None,
        thinking_content: str = "",
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        cache_read_tokens: int | None = None,
        cache_write_tokens: int | None = None,
    ) -> None:
        if not self._conversation_id:
            return
        from djangosdk.conf import ai_settings
        if not ai_settings.get("CONVERSATION", {}).get("PERSIST", True):
            return
        from djangosdk.models.message import Message
        Message.objects.create(
            conversation_id=self._conversation_id,
            role=role,
            content=content,
            tool_calls=tool_calls,
            tool_call_id=tool_call_id,
            thinking_content=thinking_content or "",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cache_read_tokens=cache_read_tokens,
            cache_write_tokens=cache_write_tokens,
        )

    async def _apersist_message(self, **kwargs) -> None:
        if not self._conversation_id:
            return
        from asgiref.sync import sync_to_async
        await sync_to_async(self._persist_message)(**kwargs)
