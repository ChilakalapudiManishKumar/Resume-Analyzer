"""
Hybrid resume recovery: rule-based extraction runs first (free, fast,
already reliable for well-formatted resumes — see resume_parser.py). The
LLM is only invoked when the resume actually looks messy, both to save
cost and because that's genuinely when it's needed — a well-formatted
resume with a clear "Skills:" line doesn't need an LLM to read it.

Design choices worth knowing:
- email/phone: rule-based regex is trusted as-is when found — regex is
  already highly reliable for these, no need for LLM re-extraction.
- skills: MERGED. Rule-based matches get confidence=100 (they're exact,
  deterministic word-boundary matches against the taxonomy — trustworthy
  by construction). LLM-only additions (skills the regex missed) keep
  the LLM's own confidence score.
- The existing `skills: list[str]` contract is UNCHANGED so every
  downstream consumer (ATS scorer, skill-gap, ML predictor, roadmap)
  keeps working exactly as before with zero changes — confidence and
  the new `projects` field are purely additive.
- If the LLM call fails for any reason (no key, API error, bad response),
  this falls back to rule-based-only silently at the data level, but
  `used_llm` and `recovered_percentage` in the response tell the truth
  about what actually happened — the user isn't told "AI recovery"
  occurred when it didn't.
"""
import logging

from app.services.llm_resume_engine import (
    LLMExtractionFailedError,
    LLMUnavailableError,
    extract_resume_with_llm,
    is_llm_available,
)
from app.services.resume_parser import extract_structured_data

logger = logging.getLogger(__name__)

# Heuristic for "this resume looks messy enough to need LLM recovery" —
# deliberately simple and explainable rather than another trained model:
# well-formatted resumes reliably yield 3+ recognized skills and a
# plausible name guess via the rule-based parser; falling short of that
# is a reasonable, cheap signal that structure/wording is hurting extraction.
MIN_SKILLS_FOR_CONFIDENT_RULE_BASED = 3


def _looks_messy(rule_based: dict) -> bool:
    return len(rule_based.get("skills", [])) < MIN_SKILLS_FOR_CONFIDENT_RULE_BASED or not rule_based.get("name")


def recover_resume_data(raw_text: str) -> dict:
    rule_based = extract_structured_data(raw_text)

    result = {
        "name": rule_based.get("name"),
        "email": rule_based.get("email"),
        "phone": rule_based.get("phone"),
        "skills": list(rule_based.get("skills", [])),
        "skill_confidence": {s: 100 for s in rule_based.get("skills", [])},
        "education_lines": rule_based.get("education_lines", []),
        "projects": [],
        "experience_years_estimate": rule_based.get("experience_years_estimate"),
        "recovered_percentage": 100,
        "used_llm": False,
    }

    if not _looks_messy(rule_based):
        return result  # clean resume, rule-based was enough — skip the LLM call entirely

    if not is_llm_available():
        # Messy resume, but no LLM configured — be honest that recovery
        # was attempted-but-unavailable rather than silently claiming 100%.
        result["recovered_percentage"] = 50
        return result

    try:
        llm_result = extract_resume_with_llm(raw_text)
    except (LLMUnavailableError, LLMExtractionFailedError) as e:
        logger.warning("LLM recovery failed, falling back to rule-based only: %s", e)
        result["recovered_percentage"] = 50
        return result

    # Merge — rule-based email/phone win if present (regex is reliable);
    # otherwise take the LLM's.
    result["name"] = result["name"] or llm_result.name
    result["email"] = result["email"] or llm_result.email
    result["phone"] = result["phone"] or llm_result.phone

    existing_skills_lower = {s.lower() for s in result["skills"]}
    for skill in llm_result.skills:
        if skill.name.lower() not in existing_skills_lower:
            result["skills"].append(skill.name)
            result["skill_confidence"][skill.name] = skill.confidence
            existing_skills_lower.add(skill.name.lower())

    result["education_lines"] = result["education_lines"] or [
        f"{e.institution}" + (f" — {e.degree}" if e.degree else "") for e in llm_result.education
    ]
    result["projects"] = [
        {"title": p.title, "technologies": p.technologies, "confidence": p.confidence}
        for p in llm_result.projects
    ]
    result["recovered_percentage"] = llm_result.recovered_percentage
    result["used_llm"] = True

    return result
