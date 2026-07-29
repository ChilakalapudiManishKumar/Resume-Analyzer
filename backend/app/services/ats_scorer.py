"""
ATS (Applicant Tracking System) scoring — deliberately rule-based, not ML.

Real ATS systems (Workday, Greenhouse, etc.) work this way too: they check
for parseable sections, keyword density, and formatting — they don't run
a trained model per company. Rule-based also means every point of the
score is explainable to the user, which matters more here than a marginal
accuracy gain from a black-box model would.

Category weights sum to 100:
- Keywords / skills matched: 30
- Standard resume sections present: 25
- Action verbs used: 20
- Length / formatting sanity: 15
- Contact info completeness: 10
"""
import re

ACTION_VERBS = [
    "led", "built", "designed", "developed", "managed", "implemented", "created",
    "optimized", "improved", "launched", "architected", "automated", "delivered",
    "reduced", "increased", "analyzed", "deployed", "engineered", "mentored",
    "collaborated", "spearheaded", "streamlined",
]

SECTION_KEYWORDS = {
    "skills": ["skills", "technical skills"],
    "education": ["education", "b.tech", "bachelor", "university", "college", "m.tech", "degree"],
    "experience_or_projects": ["experience", "projects", "internship", "work history"],
    "certifications": ["certification", "certificate", "certified"],
}


def _score_keywords(matched_skills: list[str]) -> tuple[int, str | None]:
    # 8+ distinct skills -> full marks; scales down below that.
    count = len(matched_skills)
    score = min(30, round((count / 8) * 30))
    suggestion = None if count >= 8 else f"Only {count} recognizable skill keywords found — list more relevant technical skills explicitly."
    return score, suggestion


def _score_sections(raw_text_lower: str) -> tuple[int, list[str]]:
    present = []
    missing = []
    for section, keywords in SECTION_KEYWORDS.items():
        if any(kw in raw_text_lower for kw in keywords):
            present.append(section)
        else:
            missing.append(section)
    score = round((len(present) / len(SECTION_KEYWORDS)) * 25)
    suggestions = [f"Add a clear '{m.replace('_', ' ').title()}' section." for m in missing]
    return score, suggestions


def _score_action_verbs(raw_text_lower: str) -> tuple[int, str | None]:
    count = sum(1 for verb in ACTION_VERBS if re.search(rf"\b{verb}\b", raw_text_lower))
    score = min(20, round((count / 6) * 20))
    suggestion = None if count >= 6 else "Use more strong action verbs (e.g. 'built', 'led', 'optimized') to describe your work."
    return score, suggestion


def _score_formatting(raw_text: str) -> tuple[int, str | None]:
    word_count = len(raw_text.split())
    if 250 <= word_count <= 900:
        return 15, None
    if word_count < 250:
        return round(15 * (word_count / 250)), "Resume looks quite short — consider adding more detail on projects and experience."
    return 10, "Resume looks long — consider tightening it to the most relevant, recent experience."


def _score_contact_info(extracted_data: dict) -> tuple[int, list[str]]:
    score = 0
    suggestions = []
    if extracted_data.get("email"):
        score += 5
    else:
        suggestions.append("No email address detected — make sure it's clearly visible near the top.")
    if extracted_data.get("phone"):
        score += 5
    else:
        suggestions.append("No phone number detected — add one near your contact details.")
    return score, suggestions


def score_resume(raw_text: str, extracted_data: dict) -> dict:
    raw_text_lower = raw_text.lower()
    matched_skills = extracted_data.get("skills", [])

    keyword_score, kw_suggestion = _score_keywords(matched_skills)
    section_score, section_suggestions = _score_sections(raw_text_lower)
    verb_score, verb_suggestion = _score_action_verbs(raw_text_lower)
    format_score, format_suggestion = _score_formatting(raw_text)
    contact_score, contact_suggestions = _score_contact_info(extracted_data)

    overall = keyword_score + section_score + verb_score + format_score + contact_score

    suggestions = section_suggestions + contact_suggestions
    for s in (kw_suggestion, verb_suggestion, format_suggestion):
        if s:
            suggestions.append(s)

    return {
        "overall_score": overall,
        "category_scores": {
            "keywords": keyword_score,
            "sections": section_score,
            "action_verbs": verb_score,
            "formatting": format_score,
            "contact_info": contact_score,
        },
        "suggestions": suggestions,
    }
