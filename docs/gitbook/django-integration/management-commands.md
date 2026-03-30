# Management Commands

`djangosdk` provides two management commands for configuration validation and diagnostics.

## `ai_sdk_check`

Sends a test prompt to each configured provider and reports the results.

```bash
python manage.py ai_sdk_check
```

**Output:**
```
Checking provider: openai (gpt-4.1)... OK (312ms)
Checking provider: anthropic (claude-3-5-haiku-20241022)... OK (541ms)
Checking provider: ollama (llama4-scout)... FAILED: Connection refused
```

Use this to verify that API keys are correct and providers are reachable before deploying.

## `ai_sdk_publish`

Prints the resolved `AI_SDK` settings block to stdout (with API keys redacted).

```bash
python manage.py ai_sdk_publish
```

**Output:**
```python
AI_SDK = {
    "DEFAULT_PROVIDER": "openai",
    "DEFAULT_MODEL": "gpt-4.1",
    "PROVIDERS": {
        "openai": {
            "api_key": "sk-...REDACTED",
        },
        "anthropic": {
            "api_key": "sk-ant-...REDACTED",
        },
    },
    "FAILOVER": ["openai", "anthropic"],
    "CONVERSATION": {
        "PERSIST": True,
        "MAX_HISTORY": 50,
        "AUTO_SUMMARIZE": False,
    },
    ...
}
```

Useful for reviewing the active configuration and confirming that defaults have been applied correctly.
