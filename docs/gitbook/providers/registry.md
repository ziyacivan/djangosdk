# Provider Registry

`ProviderRegistry` is a singleton that manages all configured providers. It is built from `AI_SDK.PROVIDERS` during `AppConfig.ready()`.

## Accessing the Registry

```python
from djangosdk.providers.registry import registry

provider = registry.get("openai")      # Returns the LiteLLMProvider for openai
default_model = registry.get_default_model("anthropic", fallback="gpt-4.1")
```

## How It's Built

`AiSdkConfig.ready()` (in `apps.py`) reads `AI_SDK.PROVIDERS` and registers a `LiteLLMProvider` for each entry. You do not need to call `registry.register()` manually unless you are adding a custom provider.

## Registering a Custom Provider

```python
# myapp/apps.py
from django.apps import AppConfig

class MyAppConfig(AppConfig):
    name = "myapp"

    def ready(self):
        from djangosdk.providers.registry import registry
        from myapp.providers import MyCustomProvider
        registry.register("my_provider", MyCustomProvider())
```

Then use it in agents:

```python
class CustomAgent(Agent):
    provider = "my_provider"
    model = "my-model"
```

## Failover

The registry implements failover automatically. When a provider raises an exception, it tries the next provider in `AI_SDK.FAILOVER`. The `agent_failed_over` signal is fired before each retry.

```python
AI_SDK = {
    "FAILOVER": ["openai", "anthropic", "groq"],
}
```
