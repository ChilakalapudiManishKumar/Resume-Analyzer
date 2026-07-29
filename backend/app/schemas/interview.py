from pydantic import BaseModel


class QAItem(BaseModel):
    question: str
    answer: str


class InterviewQuestionsOut(BaseModel):
    role: str
    technical: list[QAItem] = []
    coding: list[QAItem] = []
    hr: list[QAItem] = []
    behavioral: list[QAItem] = []
    scenario: list[QAItem] = []
    system_design: list[QAItem] = []
