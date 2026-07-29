# Phase 2 — Backend (Auth + Resume Upload)

## What's included and verified working
- User registration + login with JWT (bcrypt password hashing)
- Protected route pattern (`/users/me`) via FastAPI dependency injection
- Resume upload (PDF / DOCX / TXT) with:
  - Safe file handling (extension whitelist, size limit, UUID filenames)
  - Text extraction (pdfplumber / python-docx)
  - Structured field extraction (email, phone, guessed name, skill matching against `data/skills_taxonomy.json`)
- SQLAlchemy ORM models matching the Phase 1 ER diagram (SQLite for local dev, same code works against PostgreSQL by changing one env var)
- 10 passing pytest tests covering register/login/auth-failure/protected-routes/resume-upload/rejection cases

## Run it yourself

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env

uvicorn app.main:app --reload
```

Then open **http://127.0.0.1:8000/docs** — FastAPI's interactive Swagger UI.
Try it in order: `POST /api/v1/auth/register` → `POST /api/v1/auth/login` (click "Authorize" with the token) → `POST /api/v1/resumes/upload`.

## Run the tests

```bash
python -m pytest tests/ -v
```
All 10 tests should pass (verified in this build).

## Known limitation (intentional, flagged honestly)
Name/skill extraction is currently regex + keyword-matching, not spaCy NER — it works but is naive (e.g. name detection assumes the candidate's name is near the top of the resume, which is true for the vast majority of resumes but not guaranteed). This gets upgraded in Phase 3 alongside the ML models, since that's when we're already deep in the NLP/feature-engineering work.

## What's deliberately deferred from the original spec
- Email verification (needs an SMTP/SendGrid account you'd have to provide credentials for)
- Alembic migrations (using `create_all` for now — fine pre-launch, we'll add Alembic once the schema stabilizes so future changes don't require dropping tables)

## Next: Phase 3 — Machine Learning
Synthetic dataset generation, job-role classifier (multi-class), salary regressor, model comparison — same workflow as your placement-prediction project.
