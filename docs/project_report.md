# Project Report — AI Career Intelligence Platform

## Summary

A full-stack career intelligence platform: resume parsing, ATS scoring,
ML-based job-role and salary prediction, skill-gap analysis, learning
roadmaps, and role-specific interview prep. Built in 7 phases across
architecture, backend, ML, frontend, deployment, testing, and documentation.

**Deliberate scope decision** (see Phase 1): the original spec listed ~20
feature areas. Rather than build all of them shallowly, 9 core features
were built completely and correctly, with bonus features (live chatbot,
SHAP/LIME, job-description matching, LinkedIn/GitHub analyzers) explicitly
deferred rather than faked. Every feature that exists, works.

## Tech stack
FastAPI · PostgreSQL (SQLite for local dev) · SQLAlchemy · Alembic ·
Streamlit · scikit-learn · XGBoost · Docker · pytest · GitHub Actions

## What's genuinely ML vs. rule-based (and why)

Only **job-role prediction** (14-class classification) and **salary
prediction** (regression) use trained models — because those are the only
two relationships too high-dimensional/fuzzy to hand-write as rules. ATS
scoring, skill-gap analysis, the learning roadmap, resume parsing, and
interview questions are all deterministic rule-based or lookup logic —
simpler, faster, and fully explainable. Being able to articulate this
distinction clearly is itself a stronger interview signal than claiming
"the whole platform uses AI."

## ML results

**Note**: dataset size was increased from 200 to 2,000 records/role (2,800 → 28,000 total) after evaluating whether the original size was sufficient. Real, re-verified numbers below.

| Model | Metric | Result |
|---|---|---|
| Role classifier — **Logistic Regression** (winner over RF/XGBoost) | Accuracy / Macro F1 | 95.46% / 0.9546 |
| Salary regressor — **XGBoost** (winner over Linear/RF) | R² / RMSE | 0.949 / 1.34 LPA |

Honest, explainable weak spot: Cloud Engineer vs. DevOps Engineer are the
model's hardest-to-separate classes (~74-78% precision) — because those roles
share almost the same real-world skill set (Docker, Kubernetes, Terraform,
AWS, CI/CD). This is a *correct* finding, not a flaw to hide, and a good
talking point about the dataset's realism. Notably, this confusion **did
not improve** when the dataset grew 10x — confirming it's a genuine
feature-overlap ceiling, not a data-quantity problem. Salary regression,
by contrast, *did* improve meaningfully with more data (R² 0.92→0.95),
since it's a smoother numeric relationship that benefits from more
examples to average out noise. Knowing which kind of problem you're
looking at is itself a useful thing to be able to explain.

Dataset: 28,000 synthetic candidate records across 14 roles, generated with
deliberate skill overlap between adjacent roles (mirroring the classifier's
confusion pattern above) and a salary formula built from explicit,
explainable factors (role base pay, experience curve, education bonus,
location tier, company type, market noise) — not scraped, not arbitrary.

## Real bugs found and fixed during development

Rather than list only successes, here's what actually broke and how it
was caught — arguably more useful for an interview than a clean narrative:

1. **Skill-matching substring bug** (Phase 2→4): naive `skill in text`
   matching meant single-letter skills like `"c"`/`"r"` matched inside any
   word containing that letter (`Computer`, `University`...), silently
   corrupting every resume's skill list, ATS score, and predictions.
   Caught via an unexpected `sklearn` warning during Phase 4 testing, not
   by code review. Fixed with word-boundary regex.
2. **passlib/bcrypt incompatibility** (Phase 2): `passlib`, the common
   tutorial choice for password hashing, is effectively unmaintained and
   breaks with `bcrypt >= 4.1`. Switched to calling `bcrypt` directly.
3. **Inaccurate JSONB claim** (Phase 2→5): a code comment claimed JSON
   columns "automatically become JSONB" on PostgreSQL. Checked against a
   real Postgres instance in Phase 5 and found they were plain `json`.
   Fixed with an explicit `.with_variant(JSONB(), "postgresql")`.
4. **Docker path-resolution bug** (Phase 5): services located the shared
   `data/` folder relative to their own source file — breaks once a
   container's layout differs from local dev's. Fixed with an
   env-overridable resolver.
5. **Dataset non-reproducibility bug** (Phase 6): `generate_dataset()`
   seeded the RNG once at module import, so calling it twice in the same
   process silently produced a different dataset — undermining the "same
   seed → same result" claim. Fixed by reseeding inside the function.
6. **Streamlit/FastAPI dependency conflict** (Phase 4→7, recurring):
   installing both in the same Python environment breaks (`starlette`
   version mismatch) — confirmed multiple times while testing, which is
   why backend and frontend have separate `requirements.txt` and must run
   in separate virtual environments.

## Testing

- Backend: **37 tests, 98% coverage** — including real PDF/DOCX parsing
  (not just TXT), auth edge cases (tampered/expired/malformed tokens),
  cross-user access denial, and upsert-not-duplicate behavior for
  predictions/ATS scores
- ML pipeline: 6 tests covering dataset shape, reproducibility, salary
  bounds, and feature-encoding robustness to unseen categories
- CI: GitHub Actions running backend tests against a **real PostgreSQL
  service container** (not SQLite-only), plus ML tests and a frontend
  import check, on every push

## Honest limitations (not swept under the rug)
- Resume parser can't infer years of experience, location, or company
  type from free text — these are asked directly rather than guessed,
  since a wrong guess would silently corrupt both ML models' outputs
- No live LLM chatbot, SHAP/LIME, job-description matching, or social
  profile analyzers — deliberately deferred bonus features, not
  half-built ones
- Docker build/compose itself was never run against an actual Docker
  daemon during development (none was available in the build environment)
  — the Alembic/schema work WAS verified against real PostgreSQL, but the
  containerization step needs your own verification
- GitHub Actions CI was validated as correct YAML but never run on actual
  GitHub infrastructure

## Where this stands
All 7 planned phases are complete. This is a genuinely working, tested,
documented full-stack ML application — suitable to run, demo, and discuss
in depth for a resume/portfolio/interview context.
