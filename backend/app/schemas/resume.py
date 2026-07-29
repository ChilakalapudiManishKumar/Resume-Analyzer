from datetime import datetime

from pydantic import BaseModel


class ExtractedProject(BaseModel):
    title: str
    technologies: list[str] = []
    confidence: int = 100


class ExtractedResumeData(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    skills: list[str] = []
    # Additive fields (Path A: LLM-assisted messy-resume recovery). The
    # existing `skills: list[str]` contract above is UNCHANGED on purpose —
    # every downstream consumer (ATS scorer, skill-gap, ML predictor,
    # roadmap) keeps reading it exactly as before with zero changes needed.
    skill_confidence: dict[str, int] = {}
    projects: list[ExtractedProject] = []
    recovered_percentage: int = 100
    used_llm: bool = False
    education_lines: list[str] = []
    experience_years_estimate: float | None = None


class ResumeOut(BaseModel):
    id: int
    original_filename: str
    uploaded_at: datetime
    extracted_data: ExtractedResumeData

    model_config = {"from_attributes": True}
