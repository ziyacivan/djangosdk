import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .agents import ResumeExtractorAgent

SAMPLE_RESUME = """
Jane Smith
jane.smith@email.com | LinkedIn: linkedin.com/in/janesmith

EXPERIENCE
Senior Software Engineer — TechCorp (2020–present)
  - Led migration of monolithic Django app to microservices
  - Reduced API latency by 40% through query optimization and caching

Software Engineer — StartupXYZ (2017–2020)
  - Built REST APIs with Django REST Framework
  - Deployed on AWS using Docker and Kubernetes

EDUCATION
BSc Computer Science — MIT, 2017

SKILLS
Python, Django, PostgreSQL, Redis, Docker, Kubernetes, AWS, React, TypeScript
Strong communication, team leadership, agile methodologies
"""


@csrf_exempt
@require_POST
def extract(request):
    try:
        body = json.loads(request.body)
        resume_text = body.get("resume", SAMPLE_RESUME)
    except (json.JSONDecodeError, AttributeError):
        resume_text = request.POST.get("resume", SAMPLE_RESUME)

    agent = ResumeExtractorAgent()
    response = agent.handle(f"Extract information from this resume:\n\n{resume_text}")

    profile = response.structured
    return JsonResponse({
        "extracted": profile.model_dump(),
        "usage": {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
        },
    })


def sample(request):
    """Returns the built-in sample resume for testing."""
    return JsonResponse({"resume": SAMPLE_RESUME.strip()})
