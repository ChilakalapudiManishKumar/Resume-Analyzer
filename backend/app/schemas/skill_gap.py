from pydantic import BaseModel


class SkillGapOut(BaseModel):
    target_role: str
    readiness_percent: int
    matching_skills: list[str]
    missing_skills: list[str]
    learning_order: list[str]
