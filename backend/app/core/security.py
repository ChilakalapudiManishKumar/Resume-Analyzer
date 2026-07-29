"""
Password hashing and JWT creation/verification.

Two separate concerns live here:
1. Hashing passwords (bcrypt via passlib) — for storage/comparison.
2. Issuing and decoding JWTs (python-jose) — for stateless session auth.
"""
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()

# We call bcrypt directly rather than going through passlib's CryptContext.
# passlib is effectively unmaintained and has a known incompatibility with
# bcrypt >= 4.1 (its internal version-detection logic breaks and raises a
# spurious "password cannot be longer than 72 bytes" error). bcrypt itself
# is still actively maintained, so we use it as-is.
_BCRYPT_MAX_BYTES = 72  # bcrypt's own hard limit — truncate longer inputs safely


def hash_password(plain_password: str) -> str:
    password_bytes = plain_password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_bytes = plain_password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))


def create_access_token(subject: str | int, expires_delta: timedelta | None = None) -> str:
    """
    Build a signed JWT.
    `subject` is normally the user's id — it goes into the 'sub' claim,
    which is the JWT-standard field for "who is this token about".
    """
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode: dict[str, Any] = {"sub": str(subject), "exp": expire}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any] | None:
    """
    Verify signature + expiry. Returns the payload dict on success,
    or None if the token is invalid/expired/tampered with.
    """
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
