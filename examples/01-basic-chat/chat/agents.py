from djangosdk.agents import Agent


class ChatAgent(Agent):
    system_prompt = (
        "You are a helpful assistant. Be concise and friendly. "
        "Format your responses with markdown when appropriate."
    )
