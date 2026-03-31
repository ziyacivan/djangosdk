# Table of Contents

## Introduction

* [Overview](README.md)

## Getting Started

* [Installation](getting-started/installation.md)
* [Configuration](getting-started/configuration.md)
* [Quickstart](getting-started/quickstart.md)

## Core Concepts

* [Architecture](core-concepts.md)

## Agents

* [Overview](agents/overview.md)
* [Mixins](agents/mixins/README.md)
  * [Promptable](agents/mixins/promptable.md)
  * [HasTools](agents/mixins/has-tools.md)
  * [HasStructuredOutput](agents/mixins/has-structured-output.md)
  * [Conversational](agents/mixins/conversational.md)
  * [ReasoningMixin](agents/mixins/reasoning.md)

## Providers

* [Overview](providers/overview.md)
* [LiteLLM Provider](providers/litellm.md)
* [Provider Registry](providers/registry.md)
* [Prompt Caching](providers/prompt-caching.md)

## Tools

* [The @tool Decorator](tools/decorator.md)
* [Tool Registry](tools/registry.md)
* [Built-in Tools](tools/builtins.md)

## Streaming

* [Overview](streaming/overview.md)
* [Sync SSE](streaming/sse.md)
* [Async SSE](streaming/async-sse.md)

## Structured Output

* [Overview](structured-output.md)

## Conversation & Memory

* [Conversation Persistence](conversation/persistence.md)
* [Episodic Memory](conversation/episodic.md)
* [Semantic Memory](conversation/semantic.md)

## Testing

* [FakeProvider & FakeAgent](testing/fake-provider.md)
* [Assertion Helpers](testing/assertions.md)

## Django Integration

* [DRF Views](django-integration/views.md)
* [Django Admin](django-integration/admin.md)
* [Signals](django-integration/signals.md)
* [Management Commands](django-integration/management-commands.md)

## Advanced

* [Rate Limiting](rate-limiting.md)
* [Observability](observability.md)
* [MCP Support](mcp.md)
* [Embeddings](embeddings.md)
* [Audio & Images](audio-images.md)

## Examples

* [Overview](examples/README.md)
* [E-Commerce Concierge](examples/ecommerce-concierge.md)
* [Smart Django Shell](examples/smart-django-shell.md)
* [Product Searcher](examples/product-searcher.md)
* [ATS Checker](examples/ats-checker.md)

## Reference

* [Agent API](api-reference/agent.md)
* [AgentRequest](api-reference/agent-request.md)
* [AgentResponse](api-reference/agent-response.md)
* [Settings Reference](api-reference/settings.md)
