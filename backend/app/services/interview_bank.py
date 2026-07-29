"""
Interview question service — curated content filtered by role, no live LLM
calls (kept as a deferred bonus feature per the Phase 1 scope trim, since
it would need an external API key you'd have to provide and pay for).
"""
import json

from app.core.paths import get_data_dir

DATA_DIR = get_data_dir()

with open(DATA_DIR / "interview_questions.json", encoding="utf-8") as f:
    _BANK = json.load(f)

ROLE_GROUPS = _BANK["role_groups"]


def get_questions(role: str, categories: list[str] | None = None) -> dict:
    group = ROLE_GROUPS.get(role)
    all_categories = ["technical", "coding", "hr", "behavioral", "scenario", "system_design"]
    categories = categories or all_categories

    result = {}
    for category in categories:
        if category == "technical":
            result["technical"] = _BANK["technical"].get(group, []) if group else []
        elif category in ("coding", "system_design") and group not in ("data_ml", "software", "cloud_devops"):
            # Coding/system-design questions are less relevant for
            # non-engineering roles (PM/UX/BA) — skip rather than force-fit.
            result[category] = []
        else:
            result[category] = _BANK.get(category, [])
    return result
