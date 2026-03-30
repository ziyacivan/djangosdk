# Django Admin

`django-ai-sdk` registers `Conversation` and `Message` models in Django Admin, giving you a built-in interface for browsing and managing AI interactions.

## What's Available

### Conversation Admin

- List view with `id`, `agent_class`, `provider`, `model`, `created_at`, `total_cost`
- Search by `id`, `agent_class`
- Filter by `provider`, `model`
- Read-only detail view with all fields

### Message Admin

- List view with `id`, `conversation`, `role`, `created_at`, `prompt_tokens`, `completion_tokens`
- Search by `content`
- Filter by `role`
- Inline display of `tool_calls` and `thinking_content`

## Enabling Admin

Ensure `django.contrib.admin` is in `INSTALLED_APPS` (it is by default in new Django projects) and that you have run migrations:

```bash
python manage.py migrate
```

Visit `/admin/django_ai_sdk/conversation/` to see conversations.

## Customizing Admin

You can extend the admin classes for your needs:

```python
# myapp/admin.py
from django.contrib import admin
from django_ai_sdk.models.conversation import Conversation

# Unregister and re-register with custom config
admin.site.unregister(Conversation)

@admin.register(Conversation)
class MyConversationAdmin(admin.ModelAdmin):
    list_display = ["id", "agent_class", "model", "total_cost", "created_at"]
    list_filter = ["provider", "model"]
    search_fields = ["metadata"]
    readonly_fields = ["id", "created_at", "updated_at"]
```
