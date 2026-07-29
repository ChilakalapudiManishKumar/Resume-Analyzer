"""
Pydantic schemas for user-related requests/responses.

Why separate from the ORM model in database/models.py?
The ORM model represents what's in the DATABASE (includes hashed_password).
These schemas represent what the API accepts/returns — UserOut deliberately
excludes hashed_password, so there's no risk of a password hash ever
leaking into an API response, even by accident.
"""
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    created_at: datetime

    model_config = {"from_attributes": True}  # lets this build directly from an ORM object
