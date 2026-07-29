"""
ORM models — these map directly to the ER diagram from Phase 1.
See JSONType below for the JSON/JSONB column note.
"""
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy import JSON as SAJSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base

# Generic JSON on SQLite (dev), native JSONB on PostgreSQL (prod) — JSONB
# supports indexing and containment queries that plain JSON doesn't.
# Note: this required an explicit .with_variant(); SQLAlchemy's generic
# JSON type does NOT automatically become JSONB on Postgres on its own.
JSONType = SAJSON().with_variant(JSONB(), "postgresql")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    resumes: Mapped[list["Resume"]] = relationship(back_populates="owner", cascade="all, delete-orphan")


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=True)
    extracted_data: Mapped[dict] = mapped_column(JSONType, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    owner: Mapped["User"] = relationship(back_populates="resumes")
    ats_score: Mapped["ATSScore"] = relationship(back_populates="resume", uselist=False, cascade="all, delete-orphan")


class ATSScore(Base):
    __tablename__ = "ats_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id"), nullable=False, unique=True)
    overall_score: Mapped[int] = mapped_column(Integer, nullable=False)
    category_scores: Mapped[dict] = mapped_column(JSONType, nullable=False)
    suggestions: Mapped[dict] = mapped_column(JSONType, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    resume: Mapped["Resume"] = relationship(back_populates="ats_score")


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id"), nullable=False, unique=True)
    predicted_role: Mapped[str] = mapped_column(String(100), nullable=False)
    role_probabilities: Mapped[dict] = mapped_column(JSONType, nullable=False)
    salary_min: Mapped[float] = mapped_column(Float, nullable=False)
    salary_avg: Mapped[float] = mapped_column(Float, nullable=False)
    salary_max: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
