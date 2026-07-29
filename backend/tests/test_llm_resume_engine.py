"""
These tests mock the Anthropic client — they verify OUR logic (prompt
construction, response parsing, validation, error handling, fallback
behavior), not that the real Claude API returns good extractions. That
last part needs a real API key and a live smoke test, which this sandbox
doesn't have. Be honest about that distinction when reading these as
"proof it works" — they prove the code is correct, not that the LLM's
actual judgment is good, which can only be confirmed live.
"""
import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from anthropic import APIError

from app.services.llm_resume_engine import (
    LLMExtractionFailedError,
    LLMUnavailableError,
    extract_resume_with_llm,
    is_llm_available,
)


def _fake_settings(api_key):
    return SimpleNamespace(ANTHROPIC_API_KEY=api_key, LLM_MODEL="claude-sonnet-4-5")


def _fake_response(json_payload: dict, wrap_in_fences: bool = False):
    text = json.dumps(json_payload)
    if wrap_in_fences:
        text = f"```json\n{text}\n```"
    block = SimpleNamespace(type="text", text=text)
    return SimpleNamespace(content=[block])


VALID_PAYLOAD = {
    "name": "Priya Sharma",
    "email": "priya@example.com",
    "phone": "9876543210",
    "skills": [{"name": "Python", "confidence": 95}, {"name": "SQL", "confidence": 90}],
    "education": [{"institution": "VIT University", "degree": None, "confidence": 80}],
    "projects": [{"title": "Hospital Management System", "technologies": ["Python"], "confidence": 85}],
    "experience_summary": None,
    "recovered_percentage": 70,
}


def test_is_llm_available_false_when_no_key():
    with patch("app.services.llm_resume_engine.get_settings", return_value=_fake_settings(None)):
        assert is_llm_available() is False


def test_is_llm_available_true_when_key_set():
    with patch("app.services.llm_resume_engine.get_settings", return_value=_fake_settings("sk-fake-key")):
        assert is_llm_available() is True


def test_extract_raises_unavailable_without_key():
    with patch("app.services.llm_resume_engine.get_settings", return_value=_fake_settings(None)):
        with pytest.raises(LLMUnavailableError):
            extract_resume_with_llm("some resume text")


def test_extract_parses_valid_response_correctly():
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _fake_response(VALID_PAYLOAD)

    with patch("app.services.llm_resume_engine.get_settings", return_value=_fake_settings("sk-fake-key")), \
         patch("app.services.llm_resume_engine.Anthropic", return_value=mock_client):
        result = extract_resume_with_llm(
            "I know Python, SQL and built a Hospital Management System during college at VIT."
        )

    assert result.name == "Priya Sharma"
    assert result.skills[0].name == "Python"
    assert result.skills[0].confidence == 95
    assert result.projects[0].title == "Hospital Management System"
    assert result.education[0].institution == "VIT University"
    assert result.recovered_percentage == 70


def test_extract_handles_markdown_fenced_response():
    # Models don't always follow "no code fences" instructions perfectly —
    # this must not break parsing.
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _fake_response(VALID_PAYLOAD, wrap_in_fences=True)

    with patch("app.services.llm_resume_engine.get_settings", return_value=_fake_settings("sk-fake-key")), \
         patch("app.services.llm_resume_engine.Anthropic", return_value=mock_client):
        result = extract_resume_with_llm("some text")

    assert result.name == "Priya Sharma"


def test_extract_raises_on_api_error():
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = APIError(
        message="rate limited", request=MagicMock(), body=None
    )

    with patch("app.services.llm_resume_engine.get_settings", return_value=_fake_settings("sk-fake-key")), \
         patch("app.services.llm_resume_engine.Anthropic", return_value=mock_client):
        with pytest.raises(LLMExtractionFailedError):
            extract_resume_with_llm("some text")


def test_extract_raises_on_malformed_json():
    mock_client = MagicMock()
    block = SimpleNamespace(type="text", text="this is not json at all")
    mock_client.messages.create.return_value = SimpleNamespace(content=[block])

    with patch("app.services.llm_resume_engine.get_settings", return_value=_fake_settings("sk-fake-key")), \
         patch("app.services.llm_resume_engine.Anthropic", return_value=mock_client):
        with pytest.raises(LLMExtractionFailedError):
            extract_resume_with_llm("some text")


def test_extract_raises_when_confidence_out_of_range():
    # Validates that Pydantic's Field(ge=0, le=100) constraint actually
    # rejects an out-of-range confidence rather than silently accepting it —
    # matters because a hallucinated confidence of e.g. 150 should be
    # treated as an invalid response, not passed through to the database.
    bad_payload = dict(VALID_PAYLOAD)
    bad_payload["skills"] = [{"name": "Python", "confidence": 150}]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _fake_response(bad_payload)

    with patch("app.services.llm_resume_engine.get_settings", return_value=_fake_settings("sk-fake-key")), \
         patch("app.services.llm_resume_engine.Anthropic", return_value=mock_client):
        with pytest.raises(LLMExtractionFailedError):
            extract_resume_with_llm("some text")
