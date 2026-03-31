import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .agents import run_research_pipeline


def index(request):
    return render(request, "research/index.html")


@csrf_exempt
@require_POST
def research(request):
    try:
        body = json.loads(request.body)
        topic = body.get("topic", "").strip()
    except (json.JSONDecodeError, AttributeError):
        topic = request.POST.get("topic", "").strip()

    if not topic:
        return JsonResponse({"error": "topic is required"}, status=400)

    if len(topic) > 300:
        return JsonResponse({"error": "topic must be under 300 characters"}, status=400)

    try:
        result = run_research_pipeline(topic)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    total_in = sum(s["prompt_tokens"] for s in result["usage"].values())
    total_out = sum(s["completion_tokens"] for s in result["usage"].values())
    result["total_usage"] = {"prompt_tokens": total_in, "completion_tokens": total_out}

    return JsonResponse(result)
