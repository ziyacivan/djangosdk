# Mixins

The `Agent` class is composed from five mixins. Each mixin adds a discrete capability and can be used independently.

| Mixin | Module | Adds |
|---|---|---|
| `Promptable` | `agents/mixins/promptable.py` | `handle()`, `ahandle()`, `stream()`, `astream()`, tool loop |
| `HasTools` | `agents/mixins/has_tools.py` | `tools` list, tool dispatch |
| `HasStructuredOutput` | `agents/mixins/has_structured_output.py` | `output_schema`, Pydantic validation |
| `Conversational` | `agents/mixins/conversational.py` | `start_conversation()`, `with_conversation()`, DB persistence |
| `ReasoningMixin` | `agents/mixins/reasoning.py` | `reasoning` config injection |
