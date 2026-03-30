# LiteLLM Provider

`LiteLLMProvider` is the default provider. It wraps [litellm](https://github.com/BerriAI/litellm) and translates `AgentRequest` into litellm calls, injecting provider-specific parameters automatically.

## What It Does

- Translates `AgentRequest` to litellm `completion()` / `acompletion()` calls
- Injects `reasoning_effort`, `thinking`, or `budget_tokens` based on `ReasoningConfig`
- Applies `PromptCacheMiddleware` for Anthropic and OpenAI prompt caching
- Normalizes the litellm response into `AgentResponse`
- Normalizes streaming chunks into `StreamChunk`

## Automatic Reasoning Parameter Injection

When an agent has a `reasoning` attribute set, `LiteLLMProvider` automatically maps it:

```python
# Agent config:
reasoning = ReasoningConfig(effort="high")
# → litellm receives: reasoning_effort="high"

reasoning = ReasoningConfig(extended_thinking=True, thinking_budget=15000)
# → litellm receives: thinking={"type": "enabled", "budget_tokens": 15000}

reasoning = ReasoningConfig(budget_tokens=8000)
# → litellm receives: budget_tokens=8000
```

## Failover

If the primary provider fails, `ProviderRegistry` tries the next provider in `AI_SDK.FAILOVER`:

```python
AI_SDK = {
    "FAILOVER": ["openai", "anthropic"],
}
```

When a failover occurs, the `agent_failed_over` signal is fired with `from_provider` and `to_provider` kwargs.

## Using a Custom litellm Model String

You can pass any litellm-supported model string directly on the agent:

```python
class AzureAgent(Agent):
    provider = "azure"
    model = "azure/gpt-4o"  # litellm format: provider/model

class OllamaAgent(Agent):
    provider = "ollama"
    model = "ollama/llama4-scout"
```

## Passing Extra Parameters

Use `AgentRequest.extra` or the `providers.schemas.ProviderConfig.extra` dict to pass through any litellm parameter that the SDK does not expose directly:

```python
AI_SDK = {
    "PROVIDERS": {
        "openai": {
            "api_key": env("OPENAI_API_KEY"),
            "seed": 42,   # Extra — passed through to litellm
        },
    },
}
```
