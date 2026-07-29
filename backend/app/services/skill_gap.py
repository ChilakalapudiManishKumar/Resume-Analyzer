"""
Skill gap analysis — pure lookup/set-difference against the role_skill_map,
no ML involved (see Phase 1/discussion: this doesn't need a trained model).
"""
import json

from app.core.paths import get_data_dir

DATA_DIR = get_data_dir()

with open(DATA_DIR / "role_skill_map.json", encoding="utf-8") as f:
    ROLE_SKILL_MAP = json.load(f)["roles"]


def available_roles() -> list[str]:
    return list(ROLE_SKILL_MAP.keys())


def analyze_skill_gap(candidate_skills: list[str], target_role: str) -> dict:
    if target_role not in ROLE_SKILL_MAP:
        raise ValueError(f"Unknown role '{target_role}'. Available: {available_roles()}")

    candidate_set = {s.lower() for s in candidate_skills}
    core_skills = ROLE_SKILL_MAP[target_role]["core_skills"]
    overlap_skills = ROLE_SKILL_MAP[target_role]["overlap_pool"]

    matching_core = [s for s in core_skills if s in candidate_set]
    missing_core = [s for s in core_skills if s not in candidate_set]
    matching_overlap = [s for s in overlap_skills if s in candidate_set]

    # Priority/learning order: missing core skills first, in the order the
    # taxonomy lists them (core skills are curated roughly by foundational
    # importance already — e.g. "python" before "docker" for an ML role).
    learning_order = missing_core

    readiness_pct = round((len(matching_core) / len(core_skills)) * 100) if core_skills else 0

    return {
        "target_role": target_role,
        "readiness_percent": readiness_pct,
        "matching_skills": matching_core + matching_overlap,
        "missing_skills": missing_core,
        "learning_order": learning_order,
    }
