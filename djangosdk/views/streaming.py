from __future__ import annotations

from typing import Any

try:
    from rest_framework.request import Request
    from rest_framework.views import APIView

    from djangosdk.agents.base import Agent

    class StreamingChatAPIView(APIView):
        """
        DRF view that returns an SSE stream from an Agent.

        Subclass and set ``agent_class`` to your Agent subclass.

        Example::

            class StreamingSupportView(StreamingChatAPIView):
                agent_class = SupportAgent
        """

        agent_class: type[Agent] | None = None

        def get_agent(self, request: Request) -> Agent:
            if self.agent_class is None:
                raise NotImplementedError("Set agent_class on your StreamingChatAPIView subclass.")
            return self.agent_class()

        def post(self, request: Request, *args: Any, **kwargs: Any):
            prompt = request.data.get("prompt", "")
            conversation_id = request.data.get("conversation_id")

            if not prompt:
                from rest_framework import status
                from rest_framework.response import Response
                return Response({"error": "prompt is required"}, status=status.HTTP_400_BAD_REQUEST)

            agent = self.get_agent(request)
            if conversation_id:
                agent = agent.with_conversation(conversation_id)

            return agent.stream(prompt)

except ImportError:
    pass  # DRF is optional
