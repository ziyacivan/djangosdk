# DRF views — only available when djangorestframework is installed
try:
    from django_ai_sdk.views.chat import ChatAPIView
    from django_ai_sdk.views.streaming import StreamingChatAPIView
    __all__ = ["ChatAPIView", "StreamingChatAPIView"]
except ImportError:
    __all__ = []
