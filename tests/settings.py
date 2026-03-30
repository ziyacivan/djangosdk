SECRET_KEY = "test-secret-key-django-ai-sdk"
DEBUG = True
ROOT_URLCONF = "tests.urls"
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "rest_framework",
    "djangosdk",
]
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
AI_SDK = {
    "DEFAULT_PROVIDER": "fake",
    "DEFAULT_MODEL": "fake-model",
    "PROVIDERS": {},
    "CONVERSATION": {
        "PERSIST": False,
    },
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
