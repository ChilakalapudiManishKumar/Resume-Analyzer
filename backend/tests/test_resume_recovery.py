"""
Tests for resume_recovery.py — the orchestrator deciding when to call the
LLM at all, and how rule-based + LLM results get merged. These use a real
clean/messy resume text through the ACTUAL rule-based parser (not mocked),
and mock only the LLM call itself.
"""
from types import SimpleNamespace
from unittest.mock import patch

from app.schemas.llm_extraction import ExtractedEducation, ExtractedProject, ExtractedSkill, LLMExtractionResult
from app.services.resume_recovery import recover_resume_data

CLEAN_RESUME = """Jane Doe
jane.doe@example.com
9876543210
Skills: Python, SQL, Machine Learning, Docker
Education: B.Tech Computer Science, ABC University
"""

MESSY_RESUME = "I know Python and built a Hospital Management System during college at VIT."


def test_clean_resume_skips_llm_entirely():
    # Should never even check is_llm_available for a clean resume — the
    # whole point is not spending API cost when rule-based already worked.
    with patch("app.services.resume_recovery.is_llm_available") as mock_available:
        result = recover_resume_data(CLEAN_RESUME)
        mock_available.assert_not_called()

    assert result["used_llm"] is False
    assert result["recovered_percentage"] == 100
    assert "python" in result["skills"]
    assert result["skill_confidence"]["python"] == 100


def test_messy_resume_without_llm_key_falls_back_honestly():
    with patch("app.services.resume_recovery.is_llm_available", return_value=False):
        result = recover_resume_data(MESSY_RESUME)

    assert result["used_llm"] is False
    assert result["recovered_percentage"] == 50  # honest partial-recovery signal, not silently claiming 100%


def test_messy_resume_with_llm_merges_new_skills_and_projects():
    fake_llm_result = LLMExtractionResult(
        name="Anonymous Student",
        email=None,
        phone=None,
        skills=[ExtractedSkill(name="Python", confidence=95), ExtractedSkill(name="Project Management", confidence=60)],
        education=[ExtractedEducation(institution="VIT", degree=None, confidence=75)],
        projects=[ExtractedProject(title="Hospital Management System", technologies=["Python"], confidence=85)],
        experience_summary=None,
        recovered_percentage=65,
    )

    with patch("app.services.resume_recovery.is_llm_available", return_value=True), \
         patch("app.services.resume_recovery.extract_resume_with_llm", return_value=fake_llm_result):
        result = recover_resume_data(MESSY_RESUME)

    assert result["used_llm"] is True
    assert result["recovered_percentage"] == 65
    # "python" already found by rule-based (word-boundary match) keeps confidence 100,
    # NOT overwritten by the LLM's 95 — rule-based exact matches are trusted as-is.
    assert result["skill_confidence"]["python"] == 100
    # "Project Management" was NOT found by rule-based — comes from the LLM,
    # keeps the LLM's own confidence.
    assert any(s.lower() == "project management" for s in result["skills"])
    assert result["skill_confidence"]["Project Management"] == 60
    assert result["projects"][0]["title"] == "Hospital Management System"
    assert result["name"] == "Anonymous Student"  # rule-based found no name here, LLM's is used


def test_messy_resume_llm_failure_falls_back_gracefully():
    from app.services.llm_resume_engine import LLMExtractionFailedError

    with patch("app.services.resume_recovery.is_llm_available", return_value=True), \
         patch("app.services.resume_recovery.extract_resume_with_llm", side_effect=LLMExtractionFailedError("boom")):
        result = recover_resume_data(MESSY_RESUME)

    assert result["used_llm"] is False
    assert result["recovered_percentage"] == 50
    # Rule-based data should still be present even though the LLM path failed.
    assert "python" in result["skills"]


def test_upload_endpoint_returns_new_fields_end_to_end(client):
    """Full route -> orchestrator -> DB -> response flow, not just the
    orchestrator function in isolation — proves the new schema fields
    (skill_confidence, projects, used_llm, recovered_percentage) actually
    serialize correctly through the real API."""
    import io

    client.post(
        "/api/v1/auth/register",
        json={"email": "recoveryapi@example.com", "password": "SecurePass123", "full_name": "Recovery API"},
    )
    login = client.post(
        "/api/v1/auth/login", data={"username": "recoveryapi@example.com", "password": "SecurePass123"}
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    fake_resume = io.BytesIO(MESSY_RESUME.encode())
    with patch("app.services.resume_recovery.is_llm_available", return_value=False):
        response = client.post(
            "/api/v1/resumes/upload",
            headers=headers,
            files={"file": ("messy.txt", fake_resume, "text/plain")},
        )

    assert response.status_code == 201
    data = response.json()["extracted_data"]
    assert "skill_confidence" in data
    assert "projects" in data
    assert data["used_llm"] is False
    assert data["recovered_percentage"] == 50
