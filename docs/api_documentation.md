# API Documentation

Generated from the live `/openapi.json` schema of the running backend
(Phase 7) — not hand-written from memory, so it can't have drifted from
the actual code. The full interactive version (try-it-out included) is
always available at `http://localhost:8000/docs` when the server is running.

Base URL: `/api/v1` (e.g. `http://localhost:8000/api/v1`)

All endpoints except `/auth/register`, `/auth/login`, and `/health` require
a Bearer token: `Authorization: Bearer <token>` (obtained from `/auth/login`).

---

## Auth

### `POST /auth/register`
Create a new account.

**Request body**
```json
{ "email": "you@example.com", "password": "min8characters", "full_name": "Your Name" }
```
**Response** `201` — `UserOut` (id, email, full_name, created_at). Password/hash never returned.
**Errors**: `409` if email already registered.

### `POST /auth/login`
Form-encoded (not JSON) — `username` (your email) + `password`, per OAuth2 convention.

**Response** `200`
```json
{ "access_token": "eyJ...", "token_type": "bearer" }
```
**Errors**: `401` on wrong email/password.

---

## Users

### `GET /users/me`
Returns the currently authenticated user (`UserOut`). `401` if the token is missing/invalid/expired, or belongs to a user that no longer exists.

---

## Resumes

### `POST /resumes/upload`
Multipart file upload (`file` field). Accepts `.pdf`, `.docx`, `.txt` — max 5MB by default.

**Response** `201` — `ResumeOut`:
```json
{
  "id": 1,
  "original_filename": "resume.pdf",
  "uploaded_at": "2026-07-27T12:00:00",
  "extracted_data": {
    "name": "...", "email": "...", "phone": "...",
    "skills": ["python", "sql", "..."],
    "education_lines": ["..."],
    "experience_years_estimate": null
  }
}
```
Note: `experience_years_estimate` is always `null` currently — the parser doesn't compute this yet (flagged honestly in Phase 2/4 READMEs), which is why the prediction endpoint asks for experience separately.

**Errors**: `400` for unsupported extension or file over the size limit.

### `GET /resumes/{resume_id}`
Returns a previously uploaded resume — only if it belongs to the requesting user. `404` otherwise (including when the resume exists but belongs to someone else — this is deliberate, not a bug, so IDs can't be enumerated to snoop on other users' resumes).

---

## Predictions

### `POST /predictions/generate`
Generates (or regenerates) role + salary predictions.

**Request body** (`PredictionRequest`):
| Field | Type | Constraints |
|---|---|---|
| `resume_id` | int | must belong to you |
| `experience_years` | float | 0–50 |
| `education` | enum | `Bachelors`, `Masters`, `PhD` |
| `num_projects` | int | 0–100 |
| `certifications` | int | 0–50 |
| `location_tier` | enum | `Tier-1`, `Tier-2`, `Tier-3` |
| `company_type` | enum | `Startup`, `Product-based`, `Service-based`, `Enterprise` |

**Response** `201` — `PredictionOut`: `predicted_role`, `role_probabilities` (dict of all 14 roles → probability), `confidence`, `salary_min`/`salary_avg`/`salary_max` (LPA).

Calling this again for the same `resume_id` **updates** the existing prediction rather than creating a duplicate (verified in Phase 6 tests).

**Errors**: `404` if the resume doesn't exist or isn't yours.

---

## ATS Scoring

### `POST /ats/score/{resume_id}`
Runs the rule-based ATS scorer (see `docs/architecture.md` for the scoring breakdown).

**Response** `201`:
```json
{
  "id": 1, "overall_score": 78,
  "category_scores": {"keywords": 26, "sections": 20, "action_verbs": 14, "formatting": 13, "contact_info": 10},
  "suggestions": ["Add a clear 'Certifications' section.", "..."],
  "created_at": "..."
}
```
**Errors**: `404` if resume not found/not yours.

---

## Skill Gap

### `GET /skill-gap/roles`
Returns the list of all 14 supported role names (for populating a dropdown).

### `GET /skill-gap/{resume_id}?target_role=<role>`
**Response** `200`: `target_role`, `readiness_percent`, `matching_skills`, `missing_skills`, `learning_order`.
**Errors**: `400` for an unrecognized role, `404` if resume not found/not yours.

---

## Roadmap

### `GET /roadmap/{resume_id}?target_role=<role>`
Builds on skill-gap — returns detailed resources for each missing skill (description, importance, estimated time, free/paid resources, YouTube, practice sites, difficulty).
**Errors**: same as skill-gap.

---

## Interview Prep

### `GET /interview/{role}`
Returns curated Q&A across `technical`, `coding`, `hr`, `behavioral`, `scenario`, `system_design`. `technical`/`coding`/`system_design` are empty arrays (not an error) for a role with no recognized group — HR/behavioral/scenario pools are universal.

---

## Dashboard

### `GET /dashboard/latest`
Aggregates your most recently uploaded resume + its ATS score + its prediction (either may be `null` if not yet generated) into one response, so the frontend dashboard needs one call instead of three.
**Errors**: `404` if you haven't uploaded any resume yet.

---

## Health

### `GET /health`
No auth required. `{"status": "ok", "app": "AI Career Intelligence Platform"}` — used by Docker healthchecks and CI smoke tests.
