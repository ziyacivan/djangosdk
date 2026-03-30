# DRF views — only available when djangorestframework is installed
try:
    from djangosdk.views.chat import ChatAPIView
    from djangosdk.views.streaming import StreamingChatAPIView
    __all__ = ["ChatAPIView", "StreamingChatAPIView"]
except ImportError:
    __all__ = []
