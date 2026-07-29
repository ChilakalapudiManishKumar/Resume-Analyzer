"""
Safe file upload handling.

Two security-relevant things happen here that are easy to skip and easy
to get burned by later:
1. Extension whitelist check — never trust the client's declared content type.
2. A generated filename (uuid) instead of the user's original filename —
   prevents path traversal (e.g. someone naming a file "../../etc/passwd")
   and filename collisions between users.
"""
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import get_settings

settings = get_settings()


def save_upload(file: UploadFile) -> tuple[str, str]:
    """
    Validates and saves an uploaded file to disk.
    Returns (saved_file_path, original_filename).
    """
    original_filename = file.filename or "unknown"
    ext = Path(original_filename).suffix.lower()

    if ext not in settings.ALLOWED_RESUME_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Allowed: {sorted(settings.ALLOWED_RESUME_EXTENSIONS)}",
        )

    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    safe_name = f"{uuid.uuid4().hex}{ext}"
    destination = upload_dir / safe_name

    contents = file.file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > settings.MAX_UPLOAD_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large ({size_mb:.1f}MB). Max is {settings.MAX_UPLOAD_SIZE_MB}MB.",
        )

    destination.write_bytes(contents)
    return str(destination), original_filename
