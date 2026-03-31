import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .agents import O4MiniSolverAgent, ClaudeSonnetSolverAgent

AGENT_MAP = {
    "o4-mini": O4MiniSolverAgent,
    "claude-3-7": ClaudeSonnetSolverAgent,
}


def index(request):
    return render(request, "solver/index.html")


@csrf_exempt
@require_POST
def solve(request):
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, AttributeError):
        body = {}

    problem = body.get("problem", "").strip()
    model_key = body.get("model", "o4-mini")

    if not problem:
        return JsonResponse({"error": "problem is required"}, status=400)

    agent_class = AGENT_MAP.get(model_key, O4MiniSolverAgent)
    agent = agent_class()

    try:
        response = agent.handle(problem)
    except Exception as e:
        # If the chosen provider key is not configured, fall back gracefully
        return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({
        "answer": response.text,
        "thinking": response.thinking,
        "model": model_key,
        "usage": {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
        },
    })
