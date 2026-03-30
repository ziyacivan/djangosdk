from __future__ import annotations

from typing import Any

try:
    from rest_framework import status
    from rest_framework.request import Request
    from rest_framework.response import Response
    from rest_framework.views import APIView

    from djangosdk.agents.base import Agent
    from djangosdk.exceptions import AiSdkError

    class ChatAPIView(APIView):
        """
        DRF view that handles single-turn and multi-turn chat via an Agent.

        Subclass and set ``agent_class`` to your Agent subclass.

        Example::

            class SupportChatView(ChatAPIView):
                agent_class = SupportAgent

            # urls.py
            path("chat/", SupportChatView.as_view()),
        """

        agent_class: type[Agent] | None = None

        def get_agent(self, request: Request) -> Agent:
            if self.agent_class is None:
                raise NotImplementedError("Set agent_class on your ChatAPIView subclass.")
            return self.agent_class()

        def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
            prompt = request.data.get("prompt", "")
            conversation_id = request.data.get("conversation_id")

            if not prompt:
                return Response(
                    {"error": "prompt is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            agent = self.get_agent(request)

            if conversation_id:
                agent = agent.with_conversation(conversation_id)

            try:
                response = agent.handle(prompt)
            except AiSdkError as exc:
                return Response(
                    {"error": str(exc)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            return Response(
                {
                    "text": response.text,
                    "conversation_id": response.conversation_id or conversation_id,
                    "thinking": response.thinking.content if response.thinking else None,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "cache_read_tokens": response.usage.cache_read_tokens,
                        "cache_write_tokens": response.usage.cache_write_tokens,
                        "total_tokens": response.usage.total_tokens,
                    },
                }
            )

except ImportError:
    pass  # DRF is optional
