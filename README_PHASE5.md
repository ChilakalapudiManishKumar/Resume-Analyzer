# Phase 5 — Deployment

## What's included

1. **Alembic migrations** (finally added — deferred since Phase 2 "once the schema stabilized," and it has been stable through Phases 3-4)
   - `alembic upgrade head` reads `DATABASE_URL` from the same `Settings` the app uses — no duplicated config
   - Verified against a **real PostgreSQL 16 instance** (installed locally in this environment for exactly this purpose), not just SQLite

2. **Docker**
   - `backend/Dockerfile` — builds from the **project root** as context (not `backend/` alone), so it can copy in the shared `data/` folder
   - `backend/entrypoint.sh` — runs migrations, then starts uvicorn
   - `frontend/Dockerfile` — Streamlit, standalone
   - `docker-compose.yml` — wires `db` (Postgres) + `api` (FastAPI) + `frontend` (Streamlit) together, with a health-check gate so the API waits for Postgres to actually be ready

3. **`docs/deployment_guide.md`** — Local Docker Compose, Render (backend+Postgres), Streamlit Community Cloud (frontend), with an environment variable reference table

## Real issues found and fixed this phase

1. **Inaccurate claim from Phase 2**: a code comment claimed JSON columns "automatically become JSONB" on PostgreSQL. Checked it against a real Postgres instance — they were plain `json`, not `jsonb` (worse indexing). Fixed with an explicit `.with_variant(JSONB(), "postgresql")`, then re-verified the column type is genuinely `jsonb` in a live database.
2. **Docker path-resolution bug**: four services located the shared `data/` folder using a path relative to their own source file. That breaks the moment the container's directory layout differs from local dev's. Fixed with an env-overridable resolver (`APP_DATA_DIR`), set automatically in the Docker image.
3. **Alembic autogenerate quirk**: the generated migration used `postgresql.JSONB(astext_type=Text())` but didn't import `Text` — caught by actually running the migration against Postgres, not just eyeballing the generated file.

## Verified, not assumed
- Alembic migration applied successfully to a real PostgreSQL 16 database, producing correct tables, foreign keys, indexes, and genuine `jsonb` columns
- FastAPI app booted against that real Postgres instance and successfully registered a user, end to end
- Full backend test suite (19/19) re-run and still passing after all path/schema changes
- `docker-compose.yml` validated as well-formed, correctly-structured YAML

## Honestly NOT verified here
No Docker daemon exists in this sandbox, so `docker build` / `docker compose up` itself was never actually run. Please run it yourself — if the build fails, share the error and I'll fix it immediately rather than guessing.

## Next: Phase 6 — Testing
Expand test coverage, add a GitHub Actions CI workflow running pytest (and ideally a docker-compose based integration test) on every push.
