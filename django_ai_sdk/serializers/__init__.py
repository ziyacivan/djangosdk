# DRF serializers — only available when djangorestframework is installed
try:
    from django_ai_sdk.serializers.conversation import ConversationSerializer
    from django_ai_sdk.serializers.message import MessageSerializer
    __all__ = ["ConversationSerializer", "MessageSerializer"]
except ImportError:
    __all__ = []
