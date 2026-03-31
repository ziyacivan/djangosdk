# 03 — RAG / Document Q&A

Upload documents (PDF or text), index them into pgvector, and ask questions with source attribution.

## What it demonstrates

- `SemanticMemory` with pgvector for vector storage
- Document chunking and embedding ingestion
- `@tool` for retrieval — agent calls `search_documents` automatically
- Source attribution in responses

## Requirements

- PostgreSQL with the pgvector extension enabled
- OpenAI API key (for embeddings + chat)

## Setup

```bash
# 1. Enable pgvector in PostgreSQL
psql -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env: OPENAI_API_KEY + DATABASE_URL

# 4. Run migrations
python manage.py migrate

# 5. Start server
python manage.py runserver
```

Open [http://localhost:8000](http://localhost:8000).

## API

### Index a document

```bash
# PDF
curl -X POST http://localhost:8000/upload/ \
  -F "file=@/path/to/document.pdf"

# Plain text
curl -X POST http://localhost:8000/upload/ \
  -F "text=Django ORM supports complex queries via Q objects..." \
  -F "source=django-notes"
```

### Ask a question

```bash
curl -X POST http://localhost:8000/ask/ \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I filter with OR conditions?"}'
```

## Key files

| File | Purpose |
|------|---------|
| `docs_qa/agents.py` | `DocumentQAAgent` with `SemanticMemory` + `search_documents` tool |
| `docs_qa/ingest.py` | PDF + text chunking and indexing helpers |
| `docs_qa/views.py` | `/ask/` and `/upload/` endpoints |
