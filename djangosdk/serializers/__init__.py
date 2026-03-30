# DRF serializers — only available when djangorestframework is installed
try:
    from djangosdk.serializers.conversation import ConversationSerializer
    from djangosdk.serializers.message import MessageSerializer
    __all__ = ["ConversationSerializer", "MessageSerializer"]
except ImportError:
    __all__ = []
