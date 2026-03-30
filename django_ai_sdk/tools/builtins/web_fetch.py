from __future__ import annotations

import html
import re
import urllib.request
from typing import Any


class WebFetchTool:
    """
    Built-in tool that fetches and extracts plain text from a URL.

    HTML tags are stripped; the returned text is truncated to ``max_chars``
    (default 4000) to avoid flooding the context window.

    Example::

        class ResearchAgent(Agent):
            tools = [WebFetchTool()]
    """

    name = "web_fetch"
    description = (
        "Fetch the content of a web page and return its plain text. "
        "Useful for reading articles, documentation, or any URL."
    )

    def __call__(self, url: str, max_chars: int = 4000) -> str:
        return self.fetch(url, max_chars=max_chars)

    def fetch(self, url: str, max_chars: int = 4000) -> str:
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "django-ai-sdk/2.0",
                    "Accept": "text/html,text/plain",
                },
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read(1024 * 512).decode("utf-8", errors="replace")
        except Exception as exc:
            return f"Error fetching {url}: {exc}"

        text = self._extract_text(raw)
        return text[:max_chars]

    def _extract_text(self, html_content: str) -> str:
        # Remove script/style blocks
        text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html_content, flags=re.DOTALL | re.IGNORECASE)
        # Remove all remaining tags
        text = re.sub(r"<[^>]+>", " ", text)
        # Decode HTML entities
        text = html.unescape(text)
        # Collapse whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def to_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "The URL to fetch.",
                        },
                        "max_chars": {
                            "type": "integer",
                            "description": "Maximum characters to return (default 4000).",
                            "default": 4000,
                        },
                    },
                    "required": ["url"],
                },
            },
        }
