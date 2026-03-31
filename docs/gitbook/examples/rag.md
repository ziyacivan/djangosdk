# RAG / Document Q&A

**Source:** [`examples/03-rag/`](https://github.com/ziyacivan/djangosdk/tree/master/examples/03-rag)

Upload documents (PDF or plain text), index them into pgvector, and ask questions. The agent cites its sources automatically.

## What it demonstrates

- `SemanticMemory` with pgvector for vector storage
- Chunking and embedding documents at ingestion time
- A `@tool` that the agent calls to retrieve relevant chunks
- Source attribution in the final response

## Requirements

- PostgreSQL with the `pgvector` extension
- OpenAI API key (embeddings: `text-embedding-3-small`, chat: `gpt-4.1`)

## Setup

```bash
# Enable pgvector in your database
psql -c "CREATE EXTENSION IF NOT EXISTS vector;"

cd examples/03-rag
pip install djangosdk pgvector pypdf psycopg2-binary python-decouple
cp .env.example .env   # set OPENAI_API_KEY + DATABASE_URL
python manage.py migrate
python manage.py runserver
```

## Key Code

```python
from djangosdk.agents import Agent
from djangosdk.agents.mixins import HasTools
from djangosdk.memory.semantic import SemanticMemory
from djangosdk.tools import tool

class DocumentQAAgent(Agent, HasTools):
    provider = "openai"
    model = "gpt-4.1"
    memory = SemanticMemory(top_k=5)
    system_prompt = (
        "Answer questions using only the provided document context. "
        "Always use search_documents before answering. Cite your sources."
    )

    @tool
    def search_documents(self, query: str) -> list[dict]:
        """Search the knowledge base for relevant information."""
        results = self.memory.search(query)
        return [{"content": r.content, "source": r.metadata["source"]} for r in results]
```

**Indexing documents:**

```python
from docs_qa.ingest import ingest_pdf, ingest_text

# From a PDF file
ingest_pdf("/path/to/document.pdf", source_name="my-doc.pdf")

# From plain text
ingest_text("Django ORM supports...", source_name="django-notes")
```

## API

```bash
# Index a document
curl -X POST http://localhost:8000/upload/ \
  -F "file=@document.pdf"

# Ask a question
curl -X POST http://localhost:8000/ask/ \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I filter with OR conditions?"}'
```

Response includes `answer` and `sources` (list of document names cited).
