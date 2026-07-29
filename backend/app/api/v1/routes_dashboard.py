"""
Aggregates the user's most recently uploaded resume with its ATS score
and prediction (if generated) into one response — saves the frontend from
making 3 separate calls just to render the dashboard page.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.database.models import ATSScore, Prediction, Resume, User
from app.database.session import get_db
from app.schemas.dashboard import DashboardOut

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/latest", response_model=DashboardOut)
def latest_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardOut:
    resume = (
        db.query(Resume)
        .filter(Resume.user_id == current_user.id)
        .order_by(Resume.uploaded_at.desc())
        .first()
    )
    if resume is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No resume uploaded yet.",
        )

    ats_score = db.query(ATSScore).filter(ATSScore.resume_id == resume.id).first()
    prediction = db.query(Prediction).filter(Prediction.resume_id == resume.id).first()

    return DashboardOut(
        resume_id=resume.id,
        original_filename=resume.original_filename,
        uploaded_at=resume.uploaded_at,
        extracted_data=resume.extracted_data,
        ats_score=ats_score,
        prediction=prediction,
    )
