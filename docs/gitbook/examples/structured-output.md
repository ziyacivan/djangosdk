# Structured Output

**Source:** [`examples/04-structured-output/`](https://github.com/ziyacivan/djangosdk/tree/master/examples/04-structured-output)

A resume parser that extracts structured JSON from free-form text using a Pydantic schema — no regex, no prompt engineering hacks.

## What it demonstrates

- Defining a Pydantic `BaseModel` as `output_schema`
- Accessing `response.structured` as a typed Python object
- OpenAI JSON mode (activated automatically when `output_schema` is set with `gpt-4.1`)

## Setup

```bash
cd examples/04-structured-output
pip install djangosdk python-decouple
cp .env.example .env   # set OPENAI_API_KEY
python manage.py migrate
python manage.py runserver
```

## Key Code

```python
from pydantic import BaseModel, Field
from djangosdk.agents import Agent

class ResumeProfile(BaseModel):
    full_name: str
    email: str | None = None
    years_of_experience: int
    skills: list[str]
    current_title: str | None = None
    education: str | None = None
    summary: str

class ResumeExtractorAgent(Agent):
    provider = "openai"
    model = "gpt-4.1"
    output_schema = ResumeProfile
    system_prompt = "You are a precise resume parser."
```

**In your view:**

```python
agent = ResumeExtractorAgent()
response = agent.handle(f"Extract from:\n\n{resume_text}")

profile: ResumeProfile = response.structured
print(profile.full_name)           # "Jane Smith"
print(profile.years_of_experience) # 7
print(profile.skills)              # ["Python", "Django", ...]
```

## API

```bash
curl -X POST http://localhost:8000/extract/ \
  -H "Content-Type: application/json" \
  -d '{"resume": "Jane Smith\njane@email.com\n7 years Python..."}'
```

Response:

```json
{
  "extracted": {
    "full_name": "Jane Smith",
    "email": "jane@email.com",
    "years_of_experience": 7,
    "skills": ["Python", "Django", "PostgreSQL"],
    "current_title": "Senior Software Engineer",
    "summary": "..."
  }
}
```
