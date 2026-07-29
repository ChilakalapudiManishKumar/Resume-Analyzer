from datetime import datetime

from pydantic import BaseModel

from app.schemas.ats import ATSScoreOut
from app.schemas.prediction import PredictionOut
from app.schemas.resume import ExtractedResumeData


class DashboardOut(BaseModel):
    resume_id: int
    original_filename: str
    uploaded_at: datetime
    extracted_data: ExtractedResumeData
    ats_score: ATSScoreOut | None = None
    prediction: PredictionOut | None = None
