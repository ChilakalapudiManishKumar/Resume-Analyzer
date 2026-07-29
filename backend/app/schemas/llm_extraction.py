"""
Schema for what we ask the LLM to return, and validate its response against.
Having this as a strict Pydantic model means a malformed/hallucinated LLM
response gets caught immediately (raises a validation error we can catch),
rather than silently propagating bad data into the database.
"""
from pydantic import BaseModel, Field


class ExtractedSkill(BaseModel):
    name: str
    confidence: int = Field(ge=0, le=100)


class ExtractedEducation(BaseModel):
    institution: str
    degree: str | None = None
    confidence: int = Field(ge=0, le=100)


class ExtractedProject(BaseModel):
    title: str
    technologies: list[str] = []
    confidence: int = Field(ge=0, le=100)


class LLMExtractionResult(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    skills: list[ExtractedSkill] = []
    education: list[ExtractedEducation] = []
    projects: list[ExtractedProject] = []
    experience_summary: str | None = None
    recovered_percentage: int = Field(ge=0, le=100)
