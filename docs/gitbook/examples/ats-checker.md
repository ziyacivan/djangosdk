# ATS Checker

**Source:** [github.com/ziyacivan/ats-checker](https://github.com/ziyacivan/ats-checker)

Upload a CV and a job description — get a structured ATS compatibility score, keyword gap analysis, and actionable rewrite suggestions in seconds.

## What it demonstrates

- `HasStructuredOutput` with a multi-section Pydantic schema
- Parsing free-form text (PDF/plain-text CVs) into typed Python objects
- Prompt templating with `Promptable` for dynamic system prompts
- OpenAI JSON mode activated automatically via `output_schema`

## Setup

```bash
git clone https://github.com/ziyacivan/ats-checker.git
cd ats-checker
pip install -r requirements.txt
cp .env.example .env   # set OPENAI_API_KEY
python manage.py migrate
python manage.py runserver
```

## Key Code

```python
from pydantic import BaseModel, Field
from djangosdk.agents import Agent
from djangosdk.agents.mixins import HasStructuredOutput, Promptable

class KeywordAnalysis(BaseModel):
    matched: list[str]
    missing: list[str]

class ATSReport(BaseModel):
    overall_score: int = Field(ge=0, le=100, description="ATS compatibility score")
    keyword_analysis: KeywordAnalysis
    strengths: list[str]
    gaps: list[str]
    suggestions: list[str]
    summary: str

class ATSCheckerAgent(Agent, HasStructuredOutput, Promptable):
    provider = "openai"
    model = "gpt-4.1"
    output_schema = ATSReport
    system_prompt = (
        "You are an expert ATS (Applicant Tracking System) consultant. "
        "Analyse the provided CV against the job description and produce a "
        "detailed compatibility report. Be specific and actionable."
    )
```

**In the view:**

```python
agent = ATSCheckerAgent()
prompt = f"CV:\n{cv_text}\n\nJob Description:\n{jd_text}"
response = agent.handle(prompt)

report: ATSReport = response.structured
print(report.overall_score)        # 72
print(report.keyword_analysis.missing)  # ["Kubernetes", "CI/CD", "Terraform"]
print(report.suggestions[0])       # "Add a Skills section listing cloud platforms..."
```

## API

```bash
curl -X POST http://localhost:8000/check/ \
  -F "cv=@my_resume.pdf" \
  -F "job_description=We are looking for a senior DevOps engineer..."
```

Response:

```json
{
  "overall_score": 72,
  "keyword_analysis": {
    "matched": ["Python", "Docker", "AWS"],
    "missing": ["Kubernetes", "Terraform", "CI/CD"]
  },
  "strengths": ["Strong Python background", "AWS experience"],
  "gaps": ["No mention of container orchestration"],
  "suggestions": [
    "Add Kubernetes to your Skills section",
    "Describe any CI/CD pipelines you've built"
  ],
  "summary": "Good technical foundation but missing key DevOps toolchain keywords."
}
```

## Supported Input Formats

- Plain text (`.txt`)
- PDF via `pypdf` — install with `pip install pypdf`
- Paste directly via JSON body (`"cv_text"` field)
