"""
Roadmap engine — templated content per skill, no ML/training involved.
Curated resources exist for common skills; anything not curated gets a
sensible generic template rather than an empty/broken response.
"""
import json

from app.core.paths import get_data_dir

DATA_DIR = get_data_dir()

with open(DATA_DIR / "skill_resources.json", encoding="utf-8") as f:
    SKILL_RESOURCES = json.load(f)


def _generic_template(skill: str) -> dict:
    return {
        "description": f"Core skill relevant to your target role: {skill}.",
        "importance": "Relevant to your target role based on the skill-gap analysis.",
        "estimated_time": "2-4 weeks (varies by prior background)",
        "difficulty": "Intermediate",
        "free_resources": [f"Search '{skill} tutorial' on freeCodeCamp / official docs"],
        "paid_resources": [f"Search '{skill}' on Coursera or Udemy"],
        "youtube": [f"Search '{skill} full course' on YouTube"],
        "practice_sites": ["Kaggle", "LeetCode", "GitHub sample projects"],
    }


def build_roadmap(missing_skills: list[str]) -> list[dict]:
    roadmap = []
    for skill in missing_skills:
        entry = SKILL_RESOURCES.get(skill, _generic_template(skill))
        roadmap.append({"skill": skill, **entry})
    return roadmap
