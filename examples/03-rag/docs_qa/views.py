import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .agents import DocumentQAAgent
from .ingest import ingest_text, ingest_pdf


def index(request):
    return render(request, "docs_qa/index.html")


@csrf_exempt
@require_POST
def ask(request):
    try:
        body = json.loads(request.body)
        question = body.get("question", "").strip()
    except (json.JSONDecodeError, AttributeError):
        question = request.POST.get("question", "").strip()

    if not question:
        return JsonResponse({"error": "question is required"}, status=400)

    agent = DocumentQAAgent()
    response = agent.handle(question)

    return JsonResponse({
        "answer": response.text,
        "sources": list({
            tc_result.get("source")
            for tc in (response.tool_calls or [])
            for tc_result in (tc.result if isinstance(tc.result, list) else [])
            if isinstance(tc_result, dict) and tc_result.get("source")
        }),
        "usage": {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
        },
    })


@csrf_exempt
@require_POST
def upload(request):
    """Upload a document for indexing."""
    uploaded_file = request.FILES.get("file")
    text_content = request.POST.get("text", "").strip()
    source_name = request.POST.get("source", "uploaded")

    if uploaded_file:
        # Handle PDF upload
        if uploaded_file.name.endswith(".pdf"):
            import tempfile, os
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                for chunk in uploaded_file.chunks():
                    tmp.write(chunk)
                tmp_path = tmp.name
            try:
                count = ingest_pdf(tmp_path, source_name=uploaded_file.name)
            finally:
                os.unlink(tmp_path)
        else:
            content = uploaded_file.read().decode("utf-8", errors="ignore")
            count = ingest_text(content, source_name=uploaded_file.name)
        return JsonResponse({"indexed_chunks": count, "source": uploaded_file.name})

    elif text_content:
        count = ingest_text(text_content, source_name=source_name)
        return JsonResponse({"indexed_chunks": count, "source": source_name})

    return JsonResponse({"error": "Provide a file or text content"}, status=400)
