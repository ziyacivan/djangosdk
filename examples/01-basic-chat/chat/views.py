from django.http import StreamingHttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .agents import ChatAgent


def index(request):
    return render(request, "chat/index.html")


@require_POST
async def stream(request):
    prompt = request.POST.get("message", "").strip()
    if not prompt:
        return StreamingHttpResponse("data: \n\n", content_type="text/event-stream")

    agent = ChatAgent()

    async def event_generator():
        async for chunk in agent.astream(prompt):
            # SSE format: each chunk as a data line
            text = chunk.replace("\n", " ")
            yield f"data: {text}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingHttpResponse(
        event_generator(),
        content_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
