from datetime import datetime

from pydantic import BaseModel


class ATSScoreOut(BaseModel):
    id: int
    overall_score: int
    category_scores: dict[str, int]
    suggestions: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}
