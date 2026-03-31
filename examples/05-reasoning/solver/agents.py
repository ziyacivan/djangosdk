from djangosdk.agents import Agent
from djangosdk.providers.schemas import ReasoningConfig


class O4MiniSolverAgent(Agent):
    """Uses OpenAI o4-mini with high reasoning effort."""
    provider = "openai"
    model = "o4-mini"
    system_prompt = (
        "You are an expert problem solver. Think through the problem carefully step by step. "
        "Show your reasoning clearly. For math problems, verify your answer."
    )
    reasoning = ReasoningConfig(effort="high")


class ClaudeSonnetSolverAgent(Agent):
    """Uses Claude 3.7 Sonnet with extended thinking enabled."""
    provider = "anthropic"
    model = "claude-3-7-sonnet-20250219"
    system_prompt = (
        "You are an expert problem solver. Use your extended thinking to reason deeply "
        "before answering. For math problems, show all steps."
    )
    reasoning = ReasoningConfig(
        extended_thinking=True,
        thinking_budget=10000,
        stream_thinking=False,
    )
