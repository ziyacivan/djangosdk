# Built-in Tools

`djangosdk` ships with a set of ready-to-use built-in tools under `djangosdk.tools.builtins`.

## Web Search

```python
from djangosdk.tools.builtins.web_search import web_search

class ResearchAgent(Agent):
    tools = [web_search]
```

The `web_search` tool performs a web search and returns a list of results. It requires a search API key configured in your settings (e.g., SerpAPI or Brave Search).

## Web Fetch

```python
from djangosdk.tools.builtins.web_fetch import web_fetch

class ScraperAgent(Agent):
    tools = [web_fetch]
```

The `web_fetch` tool fetches the content of a URL and returns it as text.

## RAG (Retrieval-Augmented Generation)

```python
from djangosdk.tools.builtins.rag import rag_search

class KnowledgeAgent(Agent):
    tools = [rag_search]
```

The `rag_search` tool queries the embeddings store for semantically similar documents and returns them as context.

> **Note:** RAG tools require the embeddings module to be configured. See [Embeddings](../embeddings.md).

## Using Multiple Built-ins

```python
from djangosdk.tools.builtins.web_search import web_search
from djangosdk.tools.builtins.web_fetch import web_fetch

class WebAgent(Agent):
    provider = "openai"
    model = "gpt-4.1"
    tools = [web_search, web_fetch]
    system_prompt = "You can search the web and read pages to answer questions."
```
