# Phase 6 — Testing

## What's included

**Backend: 37 tests, 98% coverage** (up from 19 tests / 94% coverage at end of Phase 4)

New test files this phase:
- `test_resume_formats.py` — real PDF and DOCX resumes generated and parsed (previously **only TXT was ever tested**, despite PDF/DOCX being advertised in the spec since Phase 1)
- `test_auth_edge_cases.py` — invalid/tampered/malformed tokens, tokens for deleted users, missing Bearer prefix
- `test_endpoint_edge_cases.py` — GET /resumes/{id} (never tested before), cross-user access denial, skill-gap roles listing, unknown interview role, oversized file rejection, prediction regeneration (upsert not duplicate), roadmap error paths

**ML pipeline: 6 new tests** (`ml/tests/test_ml_pipeline.py`) — dataset shape/balance, determinism, salary bounds, skill sampling, feature engineering robustness to unseen categories.

**CI: `.github/workflows/ci.yml`** — 3 jobs:
1. `backend-tests` — runs pytest against a real PostgreSQL **service container** (not SQLite-only), plus runs the Alembic migration and a Postgres boot smoke-test
2. `ml-tests` — runs the ML pipeline tests
3. `frontend-import-check` — real imports of `components/` (api_client, charts, cards), syntax-check for `pages/` (which need a live Streamlit context to fully import-test — noted honestly rather than faking a full check)

## Real bugs found and fixed this phase (not just added tests for show)

1. **Dataset generation reproducibility bug**: `generate_dataset()` seeded the RNG once at module import time. Calling it twice in the same process (exactly what a test does) silently produced a *different* dataset the second time — undermining the "same seed → same dataset" claim made since Phase 3. Fixed by reseeding inside the function itself. Verified the actual shipped CSV's hash is unchanged (same single-call behavior as before), so the trained models are still valid.
2. Confirmed (via the new cross-user access test) that a user genuinely cannot fetch another user's resume by ID — this was implicitly true from the `WHERE user_id == current_user.id` filter since Phase 2, but had never been explicitly tested until now.

## Verified, not assumed
- Full backend suite (37/37) passing locally
- Frontend `components/` import cleanly in an isolated venv (confirmed after hitting the same Streamlit/starlette conflict from Phase 4 again — a reminder of why CI runs each job in its own fresh environment)
- CI YAML validated as well-formed with the expected 3 jobs

## Honestly not verified here
The GitHub Actions workflow itself has not been run on actual GitHub infrastructure (no GitHub repo/Actions runner available in this sandbox) — push this to your repo and check the Actions tab; send me any failures.

## Next: Phase 7 — Documentation
Final README, architecture/ER/flowchart diagrams, API documentation, user guide, installation guide — pulling together everything from Phases 1-6 into the portfolio-ready package.
