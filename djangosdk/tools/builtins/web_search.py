from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any


class WebSearchTool:
    """
    Built-in tool that searches the web using DuckDuckGo Instant Answer API.

    No API key required for basic usage.

    Example::

        class ResearchAgent(Agent):
            tools = [WebSearchTool()]

    The agent will call ``web_search(query="…", max_results=5)`` automatically.
    """

    name = "web_search"
    description = "Search the web for up-to-date information. Returns a list of relevant results."

    def __call__(self, query: str, max_results: int = 5) -> list[dict[str, str]]:
        return self.search(query, max_results=max_results)

    def search(self, query: str, max_results: int = 5) -> list[dict[str, str]]:
        encoded = urllib.parse.quote_plus(query)
        url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1&skip_disambig=1"
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "django-ai-sdk/2.0"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            return [{"error": str(exc)}]

        results = []

        # Abstract (top answer)
        if data.get("AbstractText"):
            results.append(
                {
                    "title": data.get("Heading", ""),
                    "url": data.get("AbstractURL", ""),
                    "snippet": data["AbstractText"],
                }
            )

        # Related topics
        for topic in data.get("RelatedTopics", []):
            if len(results) >= max_results:
                break
            if "Text" in topic:
                results.append(
                    {
                        "title": topic.get("Text", "")[:80],
                        "url": topic.get("FirstURL", ""),
                        "snippet": topic.get("Text", ""),
                    }
                )

        return results[:max_results]

    def to_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query.",
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default 5).",
                            "default": 5,
                        },
                    },
                    "required": ["query"],
                },
            },
        }
