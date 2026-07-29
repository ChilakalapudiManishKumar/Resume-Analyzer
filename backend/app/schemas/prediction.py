from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    """
    Fields the NLP resume parser doesn't reliably extract (experience years,
    location tier, company type) are provided by the user here rather than
    guessed — a wrong guess on these would silently corrupt both predictions,
    so we ask rather than fabricate.
    """
    resume_id: int
    experience_years: float = Field(ge=0, le=50)
    education: Literal["Bachelors", "Masters", "PhD"]
    num_projects: int = Field(ge=0, le=100)
    certifications: int = Field(ge=0, le=50)
    location_tier: Literal["Tier-1", "Tier-2", "Tier-3"]
    company_type: Literal["Startup", "Product-based", "Service-based", "Enterprise"]


class PredictionOut(BaseModel):
    id: int
    predicted_role: str
    role_probabilities: dict[str, float]
    confidence: float
    salary_min: float
    salary_avg: float
    salary_max: float
    created_at: datetime

    model_config = {"from_attributes": True}
