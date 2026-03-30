class AiSdkError(Exception):
    """Base exception for all django-ai-sdk errors."""


class ProviderError(AiSdkError):
    """Raised when a provider call fails."""

    def __init__(self, message: str, provider: str = "", model: str = "") -> None:
        super().__init__(message)
        self.provider = provider
        self.model = model


class ToolError(AiSdkError):
    """Raised when a tool execution fails."""

    def __init__(self, message: str, tool_name: str = "") -> None:
        super().__init__(message)
        self.tool_name = tool_name


class SchemaError(AiSdkError):
    """Raised when structured output schema validation fails."""


class ReasoningError(AiSdkError):
    """Raised when reasoning model parameters are invalid."""


class CacheError(AiSdkError):
    """Raised when prompt cache operations fail."""


class ConfigurationError(AiSdkError):
    """Raised when AI_SDK settings are invalid."""
