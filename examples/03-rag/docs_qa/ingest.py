"""
Document ingestion helpers.

Usage:
    from docs_qa.ingest import ingest_pdf, ingest_text
    ingest_pdf("/path/to/document.pdf", source_name="my-doc.pdf")
    ingest_text("Raw text content...", source_name="manual-entry")
"""
import io
from djangosdk.memory.semantic import SemanticMemory

_memory = SemanticMemory(top_k=5)

CHUNK_SIZE = 800   # characters per chunk
CHUNK_OVERLAP = 100


def _chunk_text(text: str) -> list[str]:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end].strip())
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return [c for c in chunks if c]


def ingest_text(text: str, source_name: str = "unknown") -> int:
    """Chunk and index plain text. Returns the number of chunks indexed."""
    chunks = _chunk_text(text)
    for i, chunk in enumerate(chunks):
        _memory.add(chunk, metadata={"source": source_name, "chunk": i})
    return len(chunks)


def ingest_pdf(path: str, source_name: str | None = None) -> int:
    """
    Extract text from a PDF and index it.
    Requires: pip install pypdf
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        raise ImportError("pypdf is required for PDF ingestion: pip install pypdf")

    reader = PdfReader(path)
    total_chunks = 0
    name = source_name or path.split("/")[-1]

    for page_num, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        if not page_text.strip():
            continue
        chunks = _chunk_text(page_text)
        for i, chunk in enumerate(chunks):
            _memory.add(chunk, metadata={"source": name, "page": page_num, "chunk": i})
        total_chunks += len(chunks)

    return total_chunks
