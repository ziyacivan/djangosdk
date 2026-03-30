from __future__ import annotations

import json
from typing import Any, AsyncGenerator, Iterator

from django.http import StreamingHttpResponse

from django_ai_sdk.agents.request import AgentRequest
from django_ai_sdk.agents.response import AgentResponse, StreamChunk
from django_ai_sdk.signals import (
    agent_completed,
    agent_failed,
    agent_started,
    cache_hit,
    cache_miss,
)


class Promptable:
    """
    Core mixin providing handle/ahandle/stream/astream methods.

    This is the heart of the Agent — it builds requests, runs the tool loop,
    persists messages, and emits signals.
    """

    def _build_request(self, prompt: str, extra_messages: list | None = None) -> AgentRequest:
        """Assemble an AgentRequest from agent config + conversation history + prompt."""
        from django_ai_sdk.conf import ai_settings
        from django_ai_sdk.providers.registry import registry

        provider_name = getattr(self, "provider", "") or ai_settings.DEFAULT_PROVIDER
        model = getattr(self, "model", "") or registry.get_default_model(provider_name, ai_settings.DEFAULT_MODEL)

        history = getattr(self, "_load_conversation_messages", lambda: [])()
        messages = list(history) + (extra_messages or [])
        messages.append({"role": "user", "content": prompt})

        tool_schemas = getattr(self, "_get_tool_schemas", lambda: [])()
        tool_schemas = list(tool_schemas) + self._get_mcp_tool_schemas()
        output_schema = getattr(self, "_get_output_json_schema", lambda: None)()

        return AgentRequest(
            messages=messages,
            model=model,
            provider=provider_name,
            system_prompt=getattr(self, "system_prompt", ""),
            temperature=getattr(self, "temperature", 0.7),
            max_tokens=getattr(self, "max_tokens", 2048),
            tools=tool_schemas,
            output_schema=output_schema,
            reasoning=getattr(self, "reasoning", None),
            enable_cache=getattr(self, "enable_cache", True),
        )

    def _get_provider(self):
        from django_ai_sdk.conf import ai_settings
        from django_ai_sdk.providers.registry import registry
        name = getattr(self, "provider", "") or ai_settings.DEFAULT_PROVIDER
        return registry.get(name)

    def _get_mcp_tool_schemas(self) -> list[dict]:
        """Return tool schemas from all configured MCP servers."""
        mcp_servers = getattr(self, "mcp_servers", [])
        if not mcp_servers:
            return []
        schemas = []
        try:
            from django_ai_sdk.mcp.client import MCPClient
            for server_cfg in mcp_servers:
                client = MCPClient.from_dict(server_cfg)
                schemas.extend(client.to_tool_schemas())
        except Exception:
            pass  # MCP failures are non-fatal
        return schemas

    def _dispatch_mcp_tool(self, tool_name: str, arguments: dict):
        """Try to dispatch a tool call to an MCP server."""
        mcp_servers = getattr(self, "mcp_servers", [])
        try:
            from django_ai_sdk.mcp.client import MCPClient
            for server_cfg in mcp_servers:
                client = MCPClient.from_dict(server_cfg)
                available = {t["name"] for t in client.list_tools()}
                if tool_name in available:
                    return client.call_tool(tool_name, arguments)
        except Exception:
            pass
        return None

    def handle(self, prompt: str, **kwargs: Any) -> AgentResponse:
        """Synchronous, blocking completion with tool-call loop."""
        agent_started.send(
            sender=self.__class__,
            agent=self,
            prompt=prompt,
            model=getattr(self, "model", ""),
            provider=getattr(self, "provider", ""),
        )
        try:
            response = self._run_tool_loop(prompt)
        except Exception as exc:
            agent_failed.send(
                sender=self.__class__,
                agent=self,
                exception=exc,
                model=getattr(self, "model", ""),
                provider=getattr(self, "provider", ""),
            )
            raise

        self._emit_cache_signal(response)
        self._save_turn(prompt, response)

        agent_completed.send(
            sender=self.__class__,
            agent=self,
            response=response,
            model=response.model,
            provider=response.provider,
        )
        return response

    def _run_tool_loop(self, prompt: str, extra_messages: list | None = None) -> AgentResponse:
        provider = self._get_provider()
        max_iters = getattr(self, "max_tool_iterations", 10)
        extra = list(extra_messages or [])

        for _ in range(max_iters):
            request = self._build_request(prompt, extra_messages=extra[1:] if extra else None)
            if extra:
                request.messages = request.messages[:-1] + extra + [request.messages[-1]]
            response = provider.complete(request)

            if not response.tool_calls:
                return response

            # Build assistant message with tool_calls
            assistant_msg: dict[str, Any] = {
                "role": "assistant",
                "content": response.text or "",
                "tool_calls": [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": json.dumps(tc["arguments"]),
                        },
                    }
                    for tc in response.tool_calls
                ],
            }
            tool_results = getattr(self, "_execute_tool_calls", lambda x: [])(response.tool_calls)
            extra = extra + [assistant_msg] + tool_results
            prompt = ""  # Subsequent turns use tool results, not a new user prompt

        return response  # type: ignore[return-value]

    def stream(self, prompt: str, **kwargs: Any) -> StreamingHttpResponse:
        """Synchronous SSE streaming response."""
        from django_ai_sdk.streaming.sse import SyncSSEResponse

        def _chunks() -> Iterator[StreamChunk]:
            request = self._build_request(prompt)
            provider = self._get_provider()
            yield from provider.stream(request)

        return SyncSSEResponse(_chunks())

    async def ahandle(self, prompt: str, **kwargs: Any) -> AgentResponse:
        """Asynchronous completion with tool-call loop."""
        agent_started.send(
            sender=self.__class__,
            agent=self,
            prompt=prompt,
            model=getattr(self, "model", ""),
            provider=getattr(self, "provider", ""),
        )
        try:
            response = await self._arun_tool_loop(prompt)
        except Exception as exc:
            agent_failed.send(
                sender=self.__class__,
                agent=self,
                exception=exc,
                model=getattr(self, "model", ""),
                provider=getattr(self, "provider", ""),
            )
            raise

        self._emit_cache_signal(response)
        await self._asave_turn(prompt, response)

        agent_completed.send(
            sender=self.__class__,
            agent=self,
            response=response,
            model=response.model,
            provider=response.provider,
        )
        return response

    async def _arun_tool_loop(self, prompt: str, extra_messages: list | None = None) -> AgentResponse:
        provider = self._get_provider()
        max_iters = getattr(self, "max_tool_iterations", 10)
        extra = list(extra_messages or [])

        for _ in range(max_iters):
            request = self._build_request(prompt, extra_messages=extra[1:] if extra else None)
            if extra:
                request.messages = request.messages[:-1] + extra + [request.messages[-1]]
            response = await provider.acomplete(request)

            if not response.tool_calls:
                return response

            assistant_msg: dict[str, Any] = {
                "role": "assistant",
                "content": response.text or "",
                "tool_calls": [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": json.dumps(tc["arguments"]),
                        },
                    }
                    for tc in response.tool_calls
                ],
            }
            tool_results = await getattr(self, "_aexecute_tool_calls", self._fake_aexecute)(response.tool_calls)
            extra = extra + [assistant_msg] + tool_results
            prompt = ""

        return response  # type: ignore[return-value]

    async def _fake_aexecute(self, tool_calls):
        return []

    async def astream(self, prompt: str, **kwargs: Any) -> AsyncGenerator[StreamChunk, None]:
        """Asynchronous streaming generator of StreamChunks."""
        request = self._build_request(prompt)
        provider = self._get_provider()
        async for chunk in provider.astream(request):
            yield chunk

    def _emit_cache_signal(self, response: AgentResponse) -> None:
        if response.usage and response.usage.cache_read_tokens > 0:
            cache_hit.send(
                sender=self.__class__,
                agent=self,
                cache_read_tokens=response.usage.cache_read_tokens,
            )
        else:
            cache_miss.send(sender=self.__class__, agent=self)

    def _save_turn(self, prompt: str, response: AgentResponse) -> None:
        persist = getattr(self, "_persist_message", None)
        if persist is None:
            return
        persist(role="user", content=prompt)
        thinking_content = response.thinking.content if response.thinking else ""
        persist(
            role="assistant",
            content=response.text,
            thinking_content=thinking_content,
            prompt_tokens=response.usage.prompt_tokens if response.usage else None,
            completion_tokens=response.usage.completion_tokens if response.usage else None,
            cache_read_tokens=response.usage.cache_read_tokens if response.usage else None,
        )
        if self._conversation_id:
            response.conversation_id = self._conversation_id

    async def _asave_turn(self, prompt: str, response: AgentResponse) -> None:
        apersist = getattr(self, "_apersist_message", None)
        if apersist is None:
            return
        await apersist(role="user", content=prompt)
        thinking_content = response.thinking.content if response.thinking else ""
        await apersist(
            role="assistant",
            content=response.text,
            thinking_content=thinking_content,
            prompt_tokens=response.usage.prompt_tokens if response.usage else None,
            completion_tokens=response.usage.completion_tokens if response.usage else None,
            cache_read_tokens=response.usage.cache_read_tokens if response.usage else None,
        )
        if self._conversation_id:
            response.conversation_id = self._conversation_id
