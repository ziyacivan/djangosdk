---
name: add-provider
description: >
  Adds a new AI provider configuration to the django-ai-sdk settings. Invoke when
  the user says "add a provider", "configure Anthropic", "configure OpenAI",
  "configure Gemini", "add Ollama", "add DeepSeek", "add xAI", "add Grok",
  "add Groq", "add Mistral", "add Azure OpenAI", "add Perplexity", "add OpenRouter",
  "set up a new provider", "how do I add [provider name]", or "configure the
  [provider] provider in settings". Also triggers on "add provider config".
triggers:
  - add a provider
  - configure anthropic
  - configure openai
  - configure gemini
  - add ollama
  - add deepseek
  - add xai
  - add grok
  - add groq
  - add mistral
  - add azure openai
  - add perplexity
  - add openrouter
  - set up a new provider
  - how do I add provider
  - configure the provider
  - add provider config
---

# Add a New Provider Configuration

All provider configuration lives in `settings.AI_SDK` — never hardcode API keys or model names.

## Settings Schema

```python
# settings.py
import environ

env = environ.Env()

AI_SDK = {
    "DEFAULT_PROVIDER": "openai",
    "DEFAULT_MODEL": "gpt-4.1",
    "PROVIDERS": {
        # Add provider configs here
    },
    "MODELS": {
        # Optional: per-model parameter overrides
        "gpt-4.1": {"temperature": 0.7, "max_tokens": 4096},
    },
}
```

## Provider Configuration Reference

### OpenAI

```python
"openai": {
    "api_key": env("OPENAI_API_KEY"),
    # Optional:
    "organization": env("OPENAI_ORG_ID", default=None),
    "base_url": None,  # for custom deployments
}
```

Recommended models: `gpt-4.1`, `gpt-4.5-preview`, `o3`, `o4-mini`

For `o3`/`o4-mini` reasoning — configure on the agent, not in settings:
```python
class MyAgent(Agent):
    provider = "openai"
    model = "o3"
    reasoning = ReasoningConfig(effort="medium")  # "low" | "medium" | "high"
```

### Anthropic

```python
"anthropic": {
    "api_key": env("ANTHROPIC_API_KEY"),
}
```

Recommended models: `claude-3-5-haiku-20241022`, `claude-3-7-sonnet-20250219`

For Claude 3.7 extended thinking:
```python
class ThinkingAgent(Agent):
    provider = "anthropic"
    model = "claude-3-7-sonnet-20250219"
    reasoning = ReasoningConfig(extended_thinking=True, thinking_budget=16000)
```

### Google (Gemini)

```python
"gemini": {
    "api_key": env("GEMINI_API_KEY"),
}
```

litellm model prefix: `gemini/gemini-2.0-flash`, `gemini/gemini-2.5-flash-preview`

### Groq

```python
"groq": {
    "api_key": env("GROQ_API_KEY"),
}
```

litellm model prefix: `groq/llama-4-scout-17b-16e-instruct`, `groq/qwen3-32b`

### Mistral

```python
"mistral": {
    "api_key": env("MISTRAL_API_KEY"),
}
```

litellm model prefix: `mistral/mistral-medium-3`, `mistral/mistral-large-latest`

### DeepSeek

```python
"deepseek": {
    "api_key": env("DEEPSEEK_API_KEY"),
}
```

litellm model prefix: `deepseek/deepseek-chat`, `deepseek/deepseek-r1`

For DeepSeek R1 reasoning:
```python
class R1Agent(Agent):
    provider = "deepseek"
    model = "deepseek/deepseek-r1"
    reasoning = ReasoningConfig(budget_tokens=8000)
```

### xAI (Grok)

```python
"xai": {
    "api_key": env("XAI_API_KEY"),
}
```

litellm model prefix: `xai/grok-3`, `xai/grok-3-fast`

### Ollama (Local)

```python
"ollama": {
    "base_url": "http://localhost:11434",
    "api_key": "ollama",  # placeholder, not validated by Ollama
}
```

litellm model prefix: `ollama/llama4:scout`, `ollama/llama4:maverick`, `ollama/qwen3:32b`

### Azure OpenAI

```python
"azure": {
    "api_key": env("AZURE_OPENAI_API_KEY"),
    "base_url": env("AZURE_OPENAI_ENDPOINT"),
    "api_version": "2024-08-01-preview",
}
```

litellm model: use your deployment name, e.g. `azure/my-gpt4-deployment`

### OpenRouter

```python
"openrouter": {
    "api_key": env("OPENROUTER_API_KEY"),
    "base_url": "https://openrouter.ai/api/v1",
}
```

litellm model: `openrouter/[provider]/[model]`, e.g. `openrouter/anthropic/claude-3-7-sonnet`

### Perplexity

```python
"perplexity": {
    "api_key": env("PERPLEXITY_API_KEY"),
    "base_url": "https://api.perplexity.ai",
}
```

litellm model: `perplexity/sonar-pro`, `perplexity/sonar-reasoning`

## Using a Non-Default Provider in an Agent

Set at the class level:

```python
class AnthropicAgent(Agent):
    provider = "anthropic"
    model = "claude-3-5-haiku-20241022"
    system_prompt = "You are helpful."
```

Or override at call time:

```python
response = agent.handle("Hello", provider="groq", model="groq/qwen3-32b")
```

## Security Checklist

Before committing provider configuration:

- [ ] API key read from environment variable — never hardcoded in settings.py
- [ ] `.env` file is in `.gitignore`
- [ ] `litellm` pinned to `>=1.82.6` in `pyproject.toml`
  - **WARNING:** There was a supply chain incident with litellm in March 2026. Always verify package integrity (`pip hash` or lock file checksums) before upgrading.
- [ ] Run `python manage.py ai_sdk_check` to confirm the provider responds correctly

## Verify Configuration

```bash
python manage.py ai_sdk_check
# ✓ openai (gpt-4.1) — OK
# ✓ anthropic (claude-3-5-haiku-20241022) — OK
# ✗ groq — Connection refused (check GROQ_API_KEY)
```

## Adding a Custom Provider

To wrap a provider not natively supported by litellm, implement `AbstractProvider`:

```python
from django_ai_sdk.providers.base import AbstractProvider
from django_ai_sdk.agents.request import AgentRequest
from django_ai_sdk.agents.response import AgentResponse


class MyCustomProvider(AbstractProvider):
    def complete(self, request: AgentRequest) -> AgentResponse:
        # translate request → your API → AgentResponse
        ...

    async def acomplete(self, request: AgentRequest) -> AgentResponse:
        ...

    def stream(self, request: AgentRequest):
        ...

    async def astream(self, request: AgentRequest):
        ...
```

Register it in `apps.py` or settings via `ProviderRegistry.register("custom", MyCustomProvider)`.
