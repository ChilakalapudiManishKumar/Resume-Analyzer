# Deployment Guide

## Honesty note up front
I built and validated the Docker/Alembic setup in this environment using a
locally-installed PostgreSQL (no Docker daemon available here to run
`docker compose up` itself). What IS verified for real:
- The Alembic migration runs successfully against actual PostgreSQL (not just SQLite) and creates the correct schema, including genuine `jsonb` columns
- The FastAPI app boots and successfully registers a user against that real Postgres database
- `docker-compose.yml` is valid YAML with the structure Docker Compose expects

What's NOT verified here (you should run this yourself and tell me if anything breaks): the actual `docker build` / `docker compose up` command, since no Docker daemon exists in this sandbox.

---

## Option 1 — Local Docker Compose (recommended first step)

```bash
# from the project root
docker compose up --build
```

This starts three containers:
- `db` — PostgreSQL 16
- `api` — FastAPI backend (runs `alembic upgrade head` automatically via `entrypoint.sh`, then serves on :8000)
- `frontend` — Streamlit (serves on :8501)

Open http://localhost:8501 once all three are healthy. Backend Swagger docs: http://localhost:8000/docs.

To stop: `docker compose down` (add `-v` to also wipe the Postgres volume).

---

## Option 2 — Render (backend + PostgreSQL)

1. **Create a PostgreSQL instance**: Render dashboard → New → PostgreSQL. Copy the generated "Internal Database URL".
2. **Create a Web Service** for the backend:
   - Connect your GitHub repo
   - Environment: **Docker**
   - Dockerfile path: `backend/Dockerfile`
   - Docker build context: repository root (`.`) — this matters, since the Dockerfile copies the shared `data/` folder from outside `backend/`
   - Environment variables:
     - `DATABASE_URL` = the Internal Database URL from step 1 (change `postgresql://` prefix to `postgresql+psycopg2://` if Render gives the plain form)
     - `SECRET_KEY` = generate one (`python -c "import secrets; print(secrets.token_hex(32))"`) — never reuse the dev default
     - `DEBUG` = `false`
3. Deploy. Render will build the image, run migrations via `entrypoint.sh`, and start the API. Check `https://<your-service>.onrender.com/health`.

---

## Option 3 — Streamlit Community Cloud (frontend)

1. Push the repo to GitHub (public, or a private repo Streamlit Cloud has access to).
2. On https://share.streamlit.io → New app:
   - Repository: your repo
   - Branch: main
   - Main file path: `frontend/streamlit_app.py`
3. Add a secret (Settings → Secrets) for the backend URL:
   ```toml
   API_BASE_URL = "https://<your-render-backend>.onrender.com/api/v1"
   ```
   Note: `components/api_client.py` reads `API_BASE_URL` from an environment variable, not `st.secrets`, directly — Streamlit Cloud does expose secrets as env vars automatically, so this works as-is, but confirm this behavior hasn't changed if you hit issues (check Streamlit's current docs).
4. Deploy. The app will be live at `https://<your-app-name>.streamlit.app`.

---

## Environment variables reference

| Variable | Where | Purpose |
|---|---|---|
| `DATABASE_URL` | backend | SQLite locally by default, PostgreSQL in Docker/Render |
| `SECRET_KEY` | backend | JWT signing key — must be a real secret in production |
| `APP_DATA_DIR` | backend | Overrides the shared `data/` folder path (set automatically to `/app/data` in the Docker image) |
| `API_BASE_URL` | frontend | Where the frontend points for API calls — `http://127.0.0.1:8000/api/v1` locally, `http://api:8000/api/v1` in docker-compose, the Render URL on Streamlit Cloud |

## Next: Phase 6 — Testing
Broaden test coverage (currently 19 backend tests covering auth/resume/predictions/ATS/skill-gap/roadmap/interview/dashboard), add CI (GitHub Actions running pytest on push).
