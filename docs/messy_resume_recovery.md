# Messy Resume Recovery (Path A: LLM-assisted)

## What this is

The original resume parser (Phase 2) works well on well-formatted resumes
with clear "Skills:" lines and section headers, but fails quietly on messy,
unstructured, or paragraph-style resumes — e.g. a sentence like *"I know
Python, SQL and built a Hospital Management System during college at VIT"*
mixes a skill, a project, and an education institution together, which
regex/keyword matching can't reliably pull apart.

This feature adds an **optional**, cost-conscious LLM fallback for exactly
that case.

## How it decides whether to call the LLM at all

```
Upload resume
   │
   ▼
Rule-based extraction (free, instant) — resume_parser.py
   │
   ▼
Looks messy? (< 3 skills found, OR no name detected)
   │
   ├── No  → done. recovered_percentage=100, used_llm=false. LLM never called.
   │
   └── Yes → is an ANTHROPIC_API_KEY configured?
              │
              ├── No  → recovered_percentage=50, used_llm=false (honest,
              │         not silently claiming success)
              │
              └── Yes → call Claude, merge results:
                        - rule-based email/phone kept as-is (regex is reliable)
                        - skills MERGED: rule-based matches keep confidence=100,
                          LLM-only additions keep the LLM's own confidence
                        - projects, education, recovered_percentage come from the LLM
                        - used_llm=true
```

This means: **a well-formatted resume never triggers an API call or cost**
— the LLM is specifically a recovery mechanism for messy input, not an
always-on replacement for the existing parser.

## What's verified vs. what isn't

**Verified** (unit + integration tests, `tests/test_llm_resume_engine.py` and `tests/test_resume_recovery.py`, 13 tests total, all passing):
- Prompt construction
- JSON response parsing and Pydantic validation (including rejecting a hallucinated out-of-range confidence score)
- The messy/clean decision logic and the cost-saving skip
- The merge logic (rule-based vs. LLM-sourced skills, confidence handling)
- Every fallback path (no key, API error, malformed response) degrades gracefully to rule-based-only rather than crashing
- The full route → orchestrator → database → API response flow, end-to-end, via FastAPI's TestClient

**NOT verified** — because no Anthropic API key was available in the
sandbox this was built in: whether the *real* Claude API actually returns
good-quality extractions on genuinely messy resumes. The tests above prove
the surrounding code is correct; they mock the API call itself. **You need
to set `ANTHROPIC_API_KEY` in your `.env` and try a few real messy resumes
yourself** to confirm extraction quality before relying on this.

## Setup
1. Get an API key: https://console.anthropic.com
2. In `backend/.env`: `ANTHROPIC_API_KEY=sk-ant-...`
3. Restart the backend. No code changes needed — it activates automatically.
4. Try uploading a deliberately messy/paragraph-style resume and check the response's `extracted_data.used_llm` and `recovered_percentage` fields.

## API response shape (additive — nothing existing removed)
```json
{
  "extracted_data": {
    "name": "...", "email": "...", "phone": "...",
    "skills": ["python", "sql", "project management"],
    "skill_confidence": {"python": 100, "sql": 100, "project management": 60},
    "projects": [{"title": "Hospital Management System", "technologies": ["Python"], "confidence": 85}],
    "education_lines": ["VIT"],
    "recovered_percentage": 65,
    "used_llm": true
  }
}
```
`skills` (plain list of strings) is **unchanged** from before this feature —
every existing consumer (ATS scorer, skill-gap analysis, ML predictions,
roadmap) keeps working exactly as it did, with zero changes required.
`skill_confidence`, `projects`, `recovered_percentage`, and `used_llm` are
new, additive fields.

## Cost note
Only messy resumes trigger a call, and only one call per upload (not per
field). Actual cost depends on your Anthropic pricing tier and resume
length — check current pricing before high-volume use.

## Still to come (deferred, not built yet)
Requirements #2 (dedicated Resume Quality Analyzer — broader than the
existing ATS score), #5 (personalized improvement suggestions), #7 (AI
resume rebuilder), #8 (resume version comparison), and #9 (explain why a
prediction changed) from the original spec are not part of this slice —
this covers requirements #1, #3, and #4 (intelligent recovery,
confidence-based extraction, and continuing predictions with recovered
data).
