import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.database.models import ATSScore, Resume, User
from app.database.session import get_db
from app.schemas.ats import ATSScoreOut
from app.services.ats_scorer import score_resume

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ats", tags=["ats"])


@router.post("/score/{resume_id}", response_model=ATSScoreOut, status_code=201)
def score(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ATSScore:
    resume = (
        db.query(Resume)
        .filter(Resume.id == resume_id, Resume.user_id == current_user.id)
        .first()
    )
    if resume is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

    result = score_resume(resume.raw_text or "", resume.extracted_data or {})

    existing = db.query(ATSScore).filter(ATSScore.resume_id == resume.id).first()
    ats_score = existing or ATSScore(resume_id=resume.id)
    ats_score.overall_score = result["overall_score"]
    ats_score.category_scores = result["category_scores"]
    ats_score.suggestions = result["suggestions"]

    if not existing:
        db.add(ats_score)
    db.commit()
    db.refresh(ats_score)
    logger.info("ATS score computed for resume_id=%s: %s", resume.id, ats_score.overall_score)
    return ats_score
