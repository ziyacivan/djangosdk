from __future__ import annotations

from django.contrib import admin

from djangosdk.models.conversation import Conversation
from djangosdk.models.message import Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = (
        "id",
        "role",
        "content",
        "thinking_content",
        "prompt_tokens",
        "completion_tokens",
        "cache_read_tokens",
        "cost_usd",
        "created_at",
    )
    fields = readonly_fields
    can_delete = False
    show_change_link = False
    ordering = ("created_at",)
    max_num = 0


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "agent_class",
        "provider",
        "model",
        "total_tokens",
        "total_cost_usd",
        "created_at",
        "updated_at",
    )
    list_filter = ("agent_class", "provider", "model")
    search_fields = ("id", "agent_class", "provider", "model")
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("-created_at",)
    inlines = [MessageInline]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("messages")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "conversation",
        "role",
        "short_content",
        "prompt_tokens",
        "completion_tokens",
        "cost_usd",
        "created_at",
    )
    list_filter = ("role", "conversation__agent_class")
    search_fields = ("content", "conversation__id")
    readonly_fields = ("id", "created_at")
    ordering = ("-created_at",)
    raw_id_fields = ("conversation",)

    @admin.display(description="Content")
    def short_content(self, obj: Message) -> str:
        return (obj.content or "")[:80] + ("…" if len(obj.content or "") > 80 else "")
