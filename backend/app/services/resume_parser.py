"""
Resume parsing service.

Phase 2 scope (deliberately simple, fully working):
- Extract raw text from PDF / DOCX / TXT
- Regex-based extraction: email, phone
- Skill extraction: keyword match against data/skills_taxonomy.json
- Very rough "name" guess: first non-empty line of the resume (common
  convention — resumes almost always lead with the candidate's name)

Deferred to Phase 3: spaCy NER for more robust name/organization/date
extraction, and section-aware parsing (education vs experience blocks).
Flagging this honestly rather than silently faking a "smart NLP" result.
"""
import json
import re
from pathlib import Path

import docx  # python-docx
import pdfplumber

from app.core.paths import get_data_dir

_TAXONOMY_PATH = get_data_dir() / "skills_taxonomy.json"
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_PHONE_RE = re.compile(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3,5}\)?[-.\s]?\d{3}[-.\s]?\d{3,4}")


def _load_skills() -> list[str]:
    with open(_TAXONOMY_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data["skills"]


_SKILLS = _load_skills()


def extract_text(file_path: str, original_filename: str) -> str:
    """Dispatch to the right extractor based on file extension."""
    ext = Path(original_filename).suffix.lower()

    if ext == ".pdf":
        text_parts = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n".join(text_parts)

    if ext == ".docx":
        document = docx.Document(file_path)
        return "\n".join(p.text for p in document.paragraphs if p.text.strip())

    if ext == ".txt":
        return Path(file_path).read_text(encoding="utf-8", errors="ignore")

    raise ValueError(f"Unsupported file extension: {ext}")


def extract_structured_data(raw_text: str) -> dict:
    """Pull name/email/phone/skills out of raw resume text."""
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

    email_match = _EMAIL_RE.search(raw_text)
    phone_match = _PHONE_RE.search(raw_text)

    lower_text = raw_text.lower()

    # Word-boundary matching, not naive substring "in" checks. Naive
    # substring matching means a skill like "c" or "r" would match inside
    # ANY word containing that letter ("Computer", "University", "Barista")
    # — this was silently polluting every resume's skill list. The lookaround
    # (not preceded/followed by an alphanumeric char) correctly handles
    # both plain words and skills with special characters like "c++" or
    # "ci/cd", since '+' and '/' aren't alphanumeric either.
    found_skills = sorted({
        skill for skill in _SKILLS
        if re.search(rf"(?<![a-z0-9]){re.escape(skill)}(?![a-z0-9])", lower_text)
    })

    # Naive name guess: first line that isn't an email/phone/URL and is
    # short enough to plausibly be a name (not a paragraph of text).
    guessed_name = None
    for line in lines[:5]:
        if _EMAIL_RE.search(line) or _PHONE_RE.search(line):
            continue
        if len(line.split()) <= 5 and len(line) < 60:
            guessed_name = line
            break

    return {
        "name": guessed_name,
        "email": email_match.group(0) if email_match else None,
        "phone": phone_match.group(0) if phone_match else None,
        "skills": found_skills,
        "education_lines": [
            line for line in lines
            if any(kw in line.lower() for kw in ("b.tech", "bachelor", "university", "college", "m.tech", "degree"))
        ],
        "experience_years_estimate": None,  # computed properly once we add date-range parsing in Phase 3
    }
