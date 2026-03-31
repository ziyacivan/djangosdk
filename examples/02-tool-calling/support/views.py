import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .agents import SupportAgent


def index(request):
    return render(request, "support/index.html")


@csrf_exempt
@require_POST
def chat(request):
    try:
        body = json.loads(request.body)
        message = body.get("message", "").strip()
    except (json.JSONDecodeError, AttributeError):
        message = request.POST.get("message", "").strip()

    if not message:
        return JsonResponse({"error": "message is required"}, status=400)

    agent = SupportAgent()
    response = agent.handle(message)

    return JsonResponse({
        "text": response.text,
        "tools_called": [tc.name for tc in (response.tool_calls or [])],
        "usage": {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
        },
    })
