"""
Shared FastAPI dependencies.

get_current_user is used by any route that needs to know "who is making
this request". FastAPI runs it before the route body, extracts the
Bearer token via OAuth2PasswordBearer, decodes it, and loads the matching
User row — or raises 401 if anything about the token is wrong.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database.models import User
from app.database.session import get_db

# tokenUrl points at the login endpoint — used only for Swagger UI's
# "Authorize" button, not for actual request routing.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_error

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_error

    user = db.get(User, int(user_id))
    if user is None:
        raise credentials_error

    return user
