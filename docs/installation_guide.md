# Installation Guide (Local Development)

Every command below has actually been run and verified during this
project's build — this isn't a guessed set of steps.

## Prerequisites
- Python 3.12
- (Optional but recommended) Docker + Docker Compose — see `docs/deployment_guide.md` for the one-command version
- (If not using Docker) PostgreSQL 16, or just use the SQLite default for local dev

## 1. Clone and set up the backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install email-validator     # required by Pydantic's EmailStr, easy to miss
cp .env.example .env
```

By default `DATABASE_URL` in `.env` points to a local SQLite file — no
Postgres setup needed to get started.

**Run migrations, then start the server:**
```bash
python -m alembic upgrade head
uvicorn app.main:app --reload
```

Visit http://localhost:8000/docs for interactive API docs, or http://localhost:8000/health as a quick check.

**Run the backend tests:**
```bash
python -m pytest tests/ -v
# or, with coverage:
pip install pytest-cov
python -m pytest tests/ --cov=app --cov-report=term-missing
```
Expected: 37 passed, ~98% coverage.

## 2. Set up the frontend (separate virtual environment — see below)

```bash
cd ../frontend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

**Important**: use a *separate* virtual environment from the backend.
Installing Streamlit and FastAPI in the same environment causes a real
dependency conflict (Streamlit pulls a newer `starlette` than FastAPI
supports) — this was hit and confirmed during this project's own testing,
not a hypothetical warning.

Visit http://localhost:8501.

## 3. (Optional) Set up the ML pipeline

Only needed if you want to regenerate the dataset or retrain the models —
the trained `.joblib` artifacts are already included in `backend/app/ml_models/`.

```bash
cd ../ml
pip install scikit-learn==1.8.0 xgboost==3.3.0 pandas numpy joblib pytest
python training/generate_dataset.py
cd training && python train_role_classifier.py && python train_salary_regressor.py
cd ../evaluation && python compare_models.py
cd .. && python predict_sample.py    # end-to-end sanity check
cd tests && python -m pytest -v      # 6 ML pipeline tests
```

If you retrain, copy the new artifacts into the backend:
```bash
cp ml/artifacts/*.joblib backend/app/ml_models/
```

## 4. (Optional) PostgreSQL instead of SQLite

```bash
createdb career_platform
export DATABASE_URL="postgresql+psycopg2://<user>:<password>@localhost:5432/career_platform"
cd backend && python -m alembic upgrade head
```
This exact flow was verified against a real local PostgreSQL 16 instance during Phase 5/7 — including confirming JSON columns come out as genuine `jsonb`, not plain `json`.

## Troubleshooting
- **`ModuleNotFoundError: email_validator`** — `pip install email-validator` (not bundled with Pydantic by default).
- **Streamlit import errors mentioning `starlette`** — you installed backend and frontend deps in the same environment; use separate venvs (see step 2).
- **`scikit-learn`/`xgboost` version warnings when loading models** — make sure you installed the exact pinned versions in `backend/requirements.txt` (1.8.0 / 3.3.0); the models were trained with those exact versions.
