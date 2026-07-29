"""
Resume upload endpoint.

Flow: receive file -> save safely to disk -> extract text -> extract
structured fields -> persist Resume row -> return the parsed result so
the frontend can show an editable "confirm your details" screen (NLP
extraction is never 100% reliable, so letting the user correct it before
we run ATS scoring / predictions on top of it matters).
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.database.models import Resume, User
from app.database.session import get_db
from app.schemas.resume import ResumeOut
from app.services.resume_parser import extract_text
from app.services.resume_recovery import recover_resume_data
from app.utils.file_handling import save_upload

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.post("/upload", response_model=ResumeOut, status_code=201)
def upload_resume(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Resume:
    file_path, original_filename = save_upload(file)

    raw_text = extract_text(file_path, original_filename)
    # Rule-based first (free); LLM recovery only kicks in if the resume
    # looks messy AND a key is configured — see resume_recovery.py.
    structured = recover_resume_data(raw_text)

    resume = Resume(
        user_id=current_user.id,
        file_path=file_path,
        original_filename=original_filename,
        raw_text=raw_text,
        extracted_data=structured,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    logger.info(
        "Resume uploaded for user_id=%s: %s (recovered=%s%%, used_llm=%s)",
        current_user.id, original_filename,
        structured["recovered_percentage"], structured["used_llm"],
    )
    return resume


@router.get("/{resume_id}", response_model=ResumeOut)
def get_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Resume:
    resume = (
        db.query(Resume)
        .filter(Resume.id == resume_id, Resume.user_id == current_user.id)
        .first()
    )
    if resume is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    return resume
