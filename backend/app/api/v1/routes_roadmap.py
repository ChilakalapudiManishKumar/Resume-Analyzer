from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.database.models import Resume, User
from app.database.session import get_db
from app.schemas.roadmap import RoadmapOut
from app.services.roadmap_engine import build_roadmap
from app.services.skill_gap import analyze_skill_gap

router = APIRouter(prefix="/roadmap", tags=["roadmap"])


@router.get("/{resume_id}", response_model=RoadmapOut)
def get_roadmap(
    resume_id: int,
    target_role: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RoadmapOut:
    resume = (
        db.query(Resume)
        .filter(Resume.id == resume_id, Resume.user_id == current_user.id)
        .first()
    )
    if resume is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

    skills = resume.extracted_data.get("skills", []) if resume.extracted_data else []
    try:
        gap = analyze_skill_gap(skills, target_role)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    roadmap = build_roadmap(gap["learning_order"])
    return RoadmapOut(target_role=target_role, roadmap=roadmap)
