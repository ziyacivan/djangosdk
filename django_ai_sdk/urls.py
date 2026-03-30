"""
Optional default URL patterns for django-ai-sdk.

Include in your project's urls.py::

    path("ai/", include("django_ai_sdk.urls")),

This requires djangorestframework and a ``DEFAULT_AGENT_CLASS`` in AI_SDK settings.
"""
from __future__ import annotations

try:
    from django.urls import path
    from django_ai_sdk.views.chat import ChatAPIView
    from django_ai_sdk.views.streaming import StreamingChatAPIView

    urlpatterns = [
        path("chat/", ChatAPIView.as_view(), name="ai_sdk_chat"),
        path("chat/stream/", StreamingChatAPIView.as_view(), name="ai_sdk_chat_stream"),
    ]
except ImportError:
    urlpatterns = []
