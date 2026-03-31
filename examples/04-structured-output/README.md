# 04 — Structured Output

A resume parser that extracts structured JSON from free-form text using a Pydantic schema.

## What it demonstrates

- `output_schema` class attribute with a Pydantic `BaseModel`
- `response.structured` returning a typed Pydantic instance
- OpenAI JSON mode (automatic with `gpt-4.1` + `output_schema`)

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
python manage.py migrate
python manage.py runserver
```

## API endpoints

### Extract from sample resume

```bash
curl -X POST http://localhost:8000/extract/ \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Extract from custom resume

```bash
curl -X POST http://localhost:8000/extract/ \
  -H "Content-Type: application/json" \
  -d '{"resume": "John Doe\njohn@email.com\n5 years Python..."}'
```

### Example response

```json
{
  "extracted": {
    "full_name": "Jane Smith",
    "email": "jane.smith@email.com",
    "years_of_experience": 7,
    "skills": ["Python", "Django", "PostgreSQL", "Redis", "Docker", "Kubernetes", "AWS", "React"],
    "current_title": "Senior Software Engineer",
    "education": "BSc Computer Science",
    "summary": "Senior software engineer with 7 years..."
  }
}
```

## Key files

| File | Purpose |
|------|---------|
| `extractor/agents.py` | `ResumeProfile` Pydantic schema + `ResumeExtractorAgent` |
| `extractor/views.py` | POST endpoint, accesses `response.structured` |
