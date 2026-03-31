from djangosdk.agents import Agent
from djangosdk.agents.mixins import HasTools
from djangosdk.memory.semantic import SemanticMemory
from djangosdk.tools import tool


class DocumentQAAgent(Agent, HasTools):
    provider = "openai"
    model = "gpt-4.1"
    system_prompt = (
        "You are a helpful assistant that answers questions based on uploaded documents. "
        "Always use the search_documents tool to find relevant context before answering. "
        "Cite your sources by mentioning the document name. "
        "If you cannot find relevant information, say so clearly."
    )
    memory = SemanticMemory(top_k=5)

    @tool
    def search_documents(self, query: str) -> list[dict]:
        """Search the document knowledge base for information relevant to the query."""
        results = self.memory.search(query)
        if not results:
            return [{"message": "No relevant documents found."}]
        return [
            {
                "content": r.content,
                "source": r.metadata.get("source", "unknown"),
                "page": r.metadata.get("page"),
                "score": round(r.score, 3) if hasattr(r, "score") else None,
            }
            for r in results
        ]
