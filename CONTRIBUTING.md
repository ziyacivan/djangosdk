# Contributing to django-ai-sdk

Thank you for your interest in contributing! This document explains how to get started.

## Development Setup

```bash
# Clone the repo
git clone https://github.com/ziyacivan/djangosdk.git
cd djangosdk

# Install with dev extras (using uv)
uv add --editable ".[dev]"

# Run the test suite
pytest tests/ -v

# Check coverage
coverage run -m pytest tests/
coverage report
```

## Running Tests

```bash
# All tests
pytest

# Single file
pytest tests/test_agent.py -v

# With coverage
coverage run -m pytest && coverage report --fail-under=80
```

## Code Style

- Python 3.11+ type hints on all public functions
- Docstrings for public classes and methods (Google style)
- Run `ruff check djangosdk/` before submitting a PR

## Pull Request Guidelines

1. **One concern per PR** — bug fix or feature, not both
2. **Tests required** — new code must include tests using `FakeProvider`; never call real APIs in tests
3. **No litellm version bumps without security audit** — see `CLAUDE.md` for details
4. **Update CHANGELOG.md** — add an entry under `[Unreleased]`
5. **Target `master`** — all PRs merge into `master`

## Adding a New Provider

Providers are configured via `AI_SDK.PROVIDERS` settings and routed through `LiteLLMProvider`. You do not need to write provider-specific code — just add an `add-provider` entry via the `/add-provider` skill or update `AI_SDK` settings directly.

## Adding a New Tool

Use the `@tool` decorator:

```python
from djangosdk.tools.decorator import tool

@tool
def lookup_order(order_id: str) -> dict:
    """Look up an order by ID.

    Args:
        order_id: The unique order identifier.
    """
    return {"order_id": order_id, "status": "shipped"}
```

The decorator automatically generates the OpenAI-compatible JSON schema from type hints and docstring.

## Reporting Bugs

Open an issue on GitHub with:
- Python version
- Django version
- `djangosdk` version
- Minimal reproduction script
- Expected vs actual behavior

## Security

Do **not** open public issues for security vulnerabilities. Email the maintainer directly. See `CLAUDE.md` for the litellm supply chain policy.
