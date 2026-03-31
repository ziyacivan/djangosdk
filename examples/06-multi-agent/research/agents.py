from djangosdk.agents import Agent


class GathererAgent(Agent):
    """Step 1: Collects raw facts about the topic."""
    provider = "openai"
    model = "gpt-4.1-mini"
    system_prompt = (
        "You are a research assistant. Given a topic, produce a bullet-point list "
        "of the most important facts, statistics, and recent developments. "
        "Be thorough and factual. Include dates and numbers where possible."
    )


class AnalystAgent(Agent):
    """Step 2: Identifies patterns and insights from raw facts."""
    provider = "openai"
    model = "gpt-4.1"
    system_prompt = (
        "You are a senior research analyst. You receive a list of raw facts about a topic. "
        "Your job is to identify the 3 most important trends, compare them, "
        "and explain the underlying dynamics. Be analytical and insightful."
    )


class WriterAgent(Agent):
    """Step 3: Writes a polished executive summary."""
    provider = "openai"
    model = "gpt-4.1"
    system_prompt = (
        "You are an expert writer. You receive research analysis and write a concise, "
        "professional executive summary (3–4 paragraphs). "
        "Use clear language. End with a 'Key Takeaways' section with 3 bullet points."
    )


def run_research_pipeline(topic: str) -> dict:
    """
    Runs GathererAgent → AnalystAgent → WriterAgent in sequence.
    Each agent's output is passed as input to the next.
    Returns a dict with all three stages' outputs.
    """
    # Stage 1: Gather raw facts
    gatherer = GathererAgent()
    facts_response = gatherer.handle(f"Research topic: {topic}")
    raw_facts = facts_response.text

    # Stage 2: Analyze patterns
    analyst = AnalystAgent()
    analysis_response = analyst.handle(
        f"Here are the raw facts about '{topic}':\n\n{raw_facts}\n\nProvide your analysis."
    )
    analysis = analysis_response.text

    # Stage 3: Write executive summary
    writer = WriterAgent()
    report_response = writer.handle(
        f"Topic: {topic}\n\nAnalysis:\n{analysis}\n\nWrite the executive summary."
    )

    return {
        "topic": topic,
        "raw_facts": raw_facts,
        "analysis": analysis,
        "report": report_response.text,
        "usage": {
            "gather": {
                "prompt_tokens": facts_response.usage.prompt_tokens,
                "completion_tokens": facts_response.usage.completion_tokens,
            },
            "analyze": {
                "prompt_tokens": analysis_response.usage.prompt_tokens,
                "completion_tokens": analysis_response.usage.completion_tokens,
            },
            "write": {
                "prompt_tokens": report_response.usage.prompt_tokens,
                "completion_tokens": report_response.usage.completion_tokens,
            },
        },
    }
