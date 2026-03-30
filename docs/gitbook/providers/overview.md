# Providers

Providers are the bridge between `djangosdk` and the underlying AI APIs. The SDK ships with one concrete provider — `LiteLLMProvider` — which routes every request through [litellm](https://github.com/BerriAI/litellm), giving you access to 100+ models across 12+ providers.

## Supported Providers

All providers below are configured in `AI_SDK.PROVIDERS` and accessed by name:

| Provider key | Models |
|---|---|
| `openai` | GPT-4.1, GPT-4.5, o3, o4-mini, DALL-E 3, Whisper |
| `anthropic` | Claude 3.7 Sonnet, Claude 3.5 Haiku, Claude 3 Opus |
| `gemini` | Gemini 2.0 Flash, Gemini 2.5 Flash |
| `groq` | Llama 3, Qwen3, Mistral |
| `deepseek` | DeepSeek V3, DeepSeek R1 |
| `mistral` | Mistral Medium 3.1, Mistral Small |
| `xai` | Grok 3, Grok 3 Mini |
| `ollama` | Llama 4 Scout, Llama 4 Maverick, any local model |
| `together` | Community open-source models |
| `azure` | Azure OpenAI deployments |
| `bedrock` | AWS Bedrock (Claude, Llama) |
| `vertex` | Google Vertex AI |

## Abstract Provider Interface

Custom providers must implement `AbstractProvider`:

```python
from djangosdk.providers.base import AbstractProvider
from djangosdk.agents.request import AgentRequest
from djangosdk.agents.response import AgentResponse, StreamChunk
from typing import Iterator, AsyncIterator

class MyCustomProvider(AbstractProvider):
    def complete(self, request: AgentRequest) -> AgentResponse:
        ...

    async def acomplete(self, request: AgentRequest) -> AgentResponse:
        ...

    def stream(self, request: AgentRequest) -> Iterator[StreamChunk]:
        ...

    async def astream(self, request: AgentRequest) -> AsyncIterator[StreamChunk]:
        ...
```

Register your custom provider in the `ProviderRegistry`:

```python
from djangosdk.providers.registry import registry
registry.register("my_provider", MyCustomProvider())
```
