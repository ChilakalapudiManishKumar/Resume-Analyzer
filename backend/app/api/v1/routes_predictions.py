"""
Generates (or regenerates) role + salary predictions for a resume.
Upserts: calling this again for the same resume replaces the old prediction
rather than creating duplicates, since PREDICTIONS.resume_id is unique
(1:1 with a resume, per the Phase 1 ER design).
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.database.models import Prediction, Resume, User
from app.database.session import get_db
from app.schemas.prediction import PredictionOut, PredictionRequest
from app.services.ml_predictor import predict_role, predict_salary

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.post("/generate", response_model=PredictionOut, status_code=201)
def generate_prediction(
    request: PredictionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Prediction:
    resume = (
        db.query(Resume)
        .filter(Resume.id == request.resume_id, Resume.user_id == current_user.id)
        .first()
    )
    if resume is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

    skills = resume.extracted_data.get("skills", []) if resume.extracted_data else []

    role_result = predict_role(
        skills=skills,
        experience_years=request.experience_years,
        education=request.education,
        num_projects=request.num_projects,
        certifications=request.certifications,
        location_tier=request.location_tier,
        company_type=request.company_type,
    )
    salary_result = predict_salary(
        skills=skills,
        experience_years=request.experience_years,
        education=request.education,
        num_projects=request.num_projects,
        certifications=request.certifications,
        location_tier=request.location_tier,
        company_type=request.company_type,
    )

    existing = db.query(Prediction).filter(Prediction.resume_id == resume.id).first()
    if existing:
        prediction = existing
    else:
        prediction = Prediction(resume_id=resume.id)
        db.add(prediction)

    prediction.predicted_role = role_result["predicted_role"]
    prediction.role_probabilities = role_result["role_probabilities"]
    prediction.confidence = role_result["confidence"]
    prediction.salary_min = salary_result["salary_min"]
    prediction.salary_avg = salary_result["salary_avg"]
    prediction.salary_max = salary_result["salary_max"]

    db.commit()
    db.refresh(prediction)
    logger.info("Prediction generated for resume_id=%s: %s", resume.id, prediction.predicted_role)
    return prediction
