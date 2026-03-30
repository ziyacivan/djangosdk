# Installation

## Requirements

- Python ≥ 3.11
- Django ≥ 4.2
- litellm == 1.82.6 (**pin this exact version** — see security note below)

## Install from PyPI

```bash
pip install django-ai-sdk
```

## Install with DRF support

If you want to use the pre-built `ChatAPIView` and `StreamingChatAPIView`:

```bash
pip install django-ai-sdk[drf]
```

## Install from source

```bash
git clone https://github.com/yusufziyacivan/django-ai-sdk
cd django-ai-sdk
pip install -e ".[drf]"
```

## Add to INSTALLED_APPS

```python
# settings.py
INSTALLED_APPS = [
    ...
    "django_ai_sdk",
]
```

## Run migrations

The SDK ships with `Conversation` and `Message` ORM models for conversation persistence:

```bash
python manage.py migrate
```

## Security Note — litellm Version Pin

**Always pin `litellm==1.82.6`.** There was a supply chain incident in March 2026 affecting later versions. Before upgrading, verify package integrity:

```bash
pip show litellm | grep -E "Name|Version|Location"
# Verify the hash against the known-good release on PyPI
```

Never upgrade litellm in a production environment without auditing the diff and validating the release hash.
