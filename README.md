# AI Career Intelligence Platform

A full-stack career intelligence platform: upload a resume and get an ATS
score, a predicted job role and salary range (ML-driven), a skill-gap
analysis against any of 14 roles, a personalized learning roadmap, and
role-specific interview prep — all backed by a real FastAPI + PostgreSQL
backend and a Streamlit dashboard.

Built in 7 phases (architecture → backend → ML → frontend → deployment →
testing → documentation), with an explicit design principle: **every
feature that exists actually works**, verified with real tests against
real databases — rather than a wide surface of half-built features. See
`docs/project_report.md` for the full build story, including bugs found
and fixed along the way.

## Features

| Feature | How it works |
|---|---|
| Resume parsing (PDF/DOCX/TXT) | regex + curated skills taxonomy |
| ATS scoring | rule-based, 5 explainable categories |
| Job role prediction | ML — 14-class classifier (Logistic Regression, 95.5% accuracy) |
| Salary prediction | ML — regression (XGBoost, R²=0.92) |
| Skill gap analysis | lookup against a role→skills map |
| Learning roadmap | curated resources per missing skill |
| Interview prep | curated Q&A, filtered by role |
| Dashboard | aggregated view with Plotly charts |

*(Only role/salary prediction are genuinely ML — see `docs/architecture.md` for why the rest don't need to be.)*

## Tech stack
FastAPI · PostgreSQL/SQLite · SQLAlchemy · Alembic · Streamlit · scikit-learn · XGBoost · Docker · pytest · GitHub Actions

## Quick start

```bash
docker compose up --build
```
Then open http://localhost:8501. See `docs/installation_guide.md` for
running without Docker, and `docs/deployment_guide.md` for Render/Streamlit
Cloud deployment.

## Documentation
- [`docs/architecture.md`](docs/architecture.md) — system design, tech choices, what changed from the original plan and why
- [`docs/er_diagram.md`](docs/er_diagram.md) — database schema, verified against a live PostgreSQL instance
- [`docs/flowchart.md`](docs/flowchart.md) — user journey through the app
- [`docs/api_documentation.md`](docs/api_documentation.md) — all endpoints, generated from the live OpenAPI schema
- [`docs/user_guide.md`](docs/user_guide.md) — how to use each page
- [`docs/installation_guide.md`](docs/installation_guide.md) — local dev setup
- [`docs/deployment_guide.md`](docs/deployment_guide.md) — Docker/Render/Streamlit Cloud
- [`docs/project_report.md`](docs/project_report.md) — full build summary, ML results, bugs found and fixed, honest limitations

## Testing
Backend: 37 tests, 98% coverage. ML pipeline: 6 tests. CI runs backend
tests against a real PostgreSQL service container on every push (see
`.github/workflows/ci.yml`).

```bash
cd backend && python -m pytest tests/ --cov=app --cov-report=term-missing
```

## Project structure
```
ai-career-intelligence/
├── backend/       # FastAPI app, Alembic migrations, tests
├── frontend/      # Streamlit multi-page app
├── ml/            # training pipeline (dataset gen, model comparison, tests)
├── data/          # shared taxonomies/resources (skills, roles, interview Qs)
├── docs/          # everything linked above
└── docker-compose.yml
```

## License
MIT — see [LICENSE](LICENSE).
