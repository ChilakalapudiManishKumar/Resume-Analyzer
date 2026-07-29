"""
LLM-assisted resume recovery.

This is deliberately opt-in and gracefully degrading: if ANTHROPIC_API_KEY
isn't set, is_llm_available() returns False and callers fall back to the
pure rule-based parser (resume_parser.py) — the app must keep working
without this, since it's an optional paid external dependency, not a
hard requirement.

I could not run this against the real Anthropic API in the sandbox this
was built in (no API key available there) — the logic here is covered by
unit tests that mock the API client, but a live smoke test with a real
key is still owed before trusting this in production. See
tests/test_llm_resume_engine.py for what IS verified: prompt construction,
JSON-parsing/validation of the response, and fallback behavior on
errors — everything except "does the real Claude API actually return
good extractions," which only a live key can confirm.
"""
import json
import logging

from anthropic import Anthropic, APIError

from app.core.config import get_settings
from app.schemas.llm_extraction import LLMExtractionResult

logger = logging.getLogger(__name__)


class LLMUnavailableError(Exception):
    """Raised when no API key is configured — callers should catch this
    and fall back to rule-based extraction rather than erroring out."""


class LLMExtractionFailedError(Exception):
    """Raised when the API call succeeds but the response can't be parsed
    into a valid extraction result (bad JSON, failed validation, etc.)."""


def is_llm_available() -> bool:
    return bool(get_settings().ANTHROPIC_API_KEY)


def _get_client() -> Anthropic:
    settings = get_settings()
    if not settings.ANTHROPIC_API_KEY:
        raise LLMUnavailableError("ANTHROPIC_API_KEY is not configured.")
    return Anthropic(api_key=settings.ANTHROPIC_API_KEY)


_EXTRACTION_PROMPT_TEMPLATE = """You are extracting structured information from a resume that may be poorly \
formatted, missing section headings, or written as loose paragraphs rather than clean sections.

Read the ENTIRE resume text below carefully, including sentences that mix multiple kinds of information \
together (e.g. "I know Python, SQL and built a Hospital Management System during college at VIT" contains \
a skill, a project, AND an education institution all in one sentence — extract all three).

Return ONLY a single JSON object (no markdown code fences, no commentary before or after) matching exactly \
this shape:

{{
  "name": string or null,
  "email": string or null,
  "phone": string or null,
  "skills": [{{"name": string, "confidence": integer 0-100}}],
  "education": [{{"institution": string, "degree": string or null, "confidence": integer 0-100}}],
  "projects": [{{"title": string, "technologies": [string], "confidence": integer 0-100}}],
  "experience_summary": string or null (a 1-2 sentence summary of their work experience, if any is mentioned),
  "recovered_percentage": integer 0-100 (your honest estimate of what fraction of a "complete resume's worth" \
of usable information you were able to recover from this text — a clean, thorough resume should score high; \
a single vague sentence should score low)
}}

Confidence should reflect how certain you are that this is a real, correctly-identified skill/institution/\
project — NOT how good the resume is. An explicitly stated skill like "Python" gets high confidence (95-100). \
Something you're inferring loosely from context should get lower confidence (50-70).

Resume text:
---
{resume_text}
---

Return ONLY the JSON object."""


def extract_resume_with_llm(raw_text: str) -> LLMExtractionResult:
    """
    Calls Claude to extract structured fields from raw resume text, with
    per-field confidence scores. Raises LLMUnavailableError if no key is
    configured, or LLMExtractionFailedError if the call fails or the
    response can't be validated — callers should catch both and fall back
    to the rule-based parser.
    """
    client = _get_client()
    settings = get_settings()
    prompt = _EXTRACTION_PROMPT_TEMPLATE.format(resume_text=raw_text[:12000])  # cap input size

    try:
        response = client.messages.create(
            model=settings.LLM_MODEL,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
    except APIError as e:
        logger.error("LLM extraction API call failed: %s", e)
        raise LLMExtractionFailedError(f"API call failed: {e}") from e

    raw_response_text = "".join(
        block.text for block in response.content if getattr(block, "type", None) == "text"
    ).strip()

    # Defensive: strip markdown code fences if the model wraps its JSON in
    # ```json ... ``` despite being asked not to — models don't always
    # follow formatting instructions perfectly.
    if raw_response_text.startswith("```"):
        raw_response_text = raw_response_text.strip("`")
        if raw_response_text.startswith("json"):
            raw_response_text = raw_response_text[4:]
        raw_response_text = raw_response_text.strip()

    try:
        parsed = json.loads(raw_response_text)
        return LLMExtractionResult(**parsed)
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        logger.error("LLM extraction response failed validation: %s | raw=%r", e, raw_response_text[:500])
        raise LLMExtractionFailedError(f"Could not parse/validate LLM response: {e}") from e
