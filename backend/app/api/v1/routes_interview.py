from fastapi import APIRouter, Depends

from app.api.v1.deps import get_current_user
from app.database.models import User
from app.schemas.interview import InterviewQuestionsOut
from app.services.interview_bank import get_questions

router = APIRouter(prefix="/interview", tags=["interview"])


@router.get("/{role}", response_model=InterviewQuestionsOut)
def interview_questions(
    role: str,
    current_user: User = Depends(get_current_user),
) -> InterviewQuestionsOut:
    questions = get_questions(role)
    return InterviewQuestionsOut(role=role, **questions)
