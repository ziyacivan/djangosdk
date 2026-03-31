from pydantic import BaseModel, Field
from djangosdk.agents import Agent


class ResumeProfile(BaseModel):
    full_name: str = Field(description="Candidate's full name")
    email: str | None = Field(default=None, description="Email address if present")
    years_of_experience: int = Field(description="Total years of professional experience")
    skills: list[str] = Field(description="Technical and soft skills mentioned")
    current_title: str | None = Field(default=None, description="Most recent job title")
    education: str | None = Field(default=None, description="Highest degree and field")
    summary: str = Field(description="2-sentence professional summary")


class ResumeExtractorAgent(Agent):
    provider = "openai"
    model = "gpt-4.1"
    output_schema = ResumeProfile
    system_prompt = (
        "You are a precise resume parser. Extract structured information from the resume text. "
        "If a field is not mentioned in the resume, use null. "
        "For skills, extract all technical tools, languages, frameworks, and relevant soft skills."
    )
