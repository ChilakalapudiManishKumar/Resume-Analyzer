# AI Career Intelligence Platform

A resume analyzer that goes beyond a basic keyword scanner. Upload a resume and it parses your details, scores it against ATS-style rules, predicts a likely job role and salary range using a trained ML model, shows you what skills you're missing for a target role, and puts together a small learning roadmap and interview prep list based on that.

I built this to go deeper than a typical "train a model on Kaggle data and call it done" project. There's a real backend, a real database, an actual frontend people can click through, and it's tested and containerized like something you'd actually ship.

## What it does

- Upload a resume (PDF, DOCX, or TXT) and get your name, email, phone, and skills pulled out automatically
- Get an ATS score out of 100 with a breakdown of what's hurting it
- Get a predicted job role (out of 14 tracks) and a salary range, both from a trained model
- Compare your skills against any role and see exactly what's missing
- Get a roadmap of resources for each missing skill
- Practice with role-specific interview questions
- If your resume is messy or badly formatted, there's an optional AI-assisted fallback (using Claude) that tries to recover information the regular parser would miss

## Why only two features are actually ML

Role prediction and salary prediction are the only parts backed by a trained model. Everything else — ATS scoring, skill gap, the roadmap, interview questions — is rule-based. That's on purpose. You only need ML when the input-to-output mapping is too messy to write down as a rule, and most of what people call "AI resume tools" don't actually need a model for half of what they do.

## Tech stack

Backend: FastAPI, PostgreSQL (SQLite for local dev), SQLAlchemy, Alembic, JWT + bcrypt for auth
ML: scikit-learn, XGBoost, pandas
Frontend: Streamlit, Plotly
AI integration: Anthropic Claude API (optional, for messy resume recovery)
Other: Docker, GitHub Actions for CI, pytest

## How it's put together

```
backend/     FastAPI app — auth, resume upload, predictions, ATS scoring, skill gap, roadmap, interview endpoints
frontend/    Streamlit app — Resume Upload, Dashboard, Skill Gap, Salary Insights, Roadmap, Interview Prep pages
ml/          dataset generation, model training scripts, evaluation, and the ML pipeline's own tests
data/        shared JSON: skills taxonomy, role-to-skills mapping, learning resources, interview questions
docs/        extra reference material (architecture notes, ER diagram, API reference) — none of this is required to run the app, it's just background reading
```

Request flow, roughly: you upload a resume through Streamlit, it hits the FastAPI backend, gets parsed (regex + a skills taxonomy, with an optional Claude fallback for messy ones), gets saved to Postgres/SQLite, and then separate endpoints handle ATS scoring, the ML predictions, skill gap, roadmap, and interview questions — each one pulling from either a trained model or the shared JSON data.

Database is simple: users have resumes, and each resume has one ATS score and one prediction tied to it (1:1, enforced with a unique foreign key, not just app logic).

## The ML part

Role classifier: Logistic Regression came out ahead of Random Forest and XGBoost, at about 95.5% accuracy across 14 roles.
Salary regressor: XGBoost, R² of 0.95.

Worth knowing if you look at the numbers closely: Cloud Engineer and DevOps Engineer get confused with each other a lot more than the other roles (around 75% precision instead of 95%+). That's not a bug — those two roles genuinely share almost the same skill set in real life, so the model struggling there actually makes sense. I tried fixing it by generating way more training data (10x, from 200 to 2,000 records per role) and it barely moved, which told me it's a real overlap in the data, not something more data was going to fix. Salary prediction, on the other hand, did improve noticeably with more data — a good reminder that "get more data" doesn't fix every kind of problem.

The dataset itself is synthetic — I generated it rather than scraping real job postings, since most public salary datasets are messy and biased toward US listings anyway. It's realistic in structure (skills, experience, education, location, company type all feed into the salary), but the actual numbers aren't pulled from real postings. Worth saying plainly if anyone asks.

## API endpoints, quick reference

All under `/api/v1`, JWT-protected except register/login/health.

- `POST /auth/register`, `POST /auth/login`
- `GET /users/me`
- `POST /resumes/upload`, `GET /resumes/{id}`
- `POST /predictions/generate`
- `POST /ats/score/{resume_id}`
- `GET /skill-gap/roles`, `GET /skill-gap/{resume_id}?target_role=`
- `GET /roadmap/{resume_id}?target_role=`
- `GET /interview/{role}`
- `GET /dashboard/latest`
- `GET /health`

Full interactive docs (try-it-out included) are always at `/docs` once the backend is running.

## Running it locally, from scratch

You need Python 3.12 and VS Code (or any editor, but these steps assume VS Code).

**Get the code**: unzip the project somewhere simple, not inside OneDrive/Dropbox/Google Drive — synced folders cause slow installs and can corrupt files mid-write. Open the folder in VS Code (File → Open Folder).

**Backend** — open a terminal (Terminal → New Terminal):
```bash
cd backend
python -m venv venv
venv\Scripts\activate.bat        # Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
pip install email-validator
copy .env.example .env           # Mac/Linux: cp .env.example .env
python -m alembic upgrade head
uvicorn app.main:app --reload
```
Check it worked: open `http://127.0.0.1:8000/health` in a browser, should show `{"status":"ok",...}`.

Leave that terminal running. Optional: if you want the AI-assisted messy resume recovery, open `.env` and add `ANTHROPIC_API_KEY=sk-ant-...` (get one at console.anthropic.com) before starting uvicorn. Skip it entirely if you don't need it — everything else works without it.

**Frontend** — open a second, separate terminal (don't touch the backend one):
```bash
cd frontend
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
streamlit run streamlit_app.py
```
It should open `http://localhost:8501` in your browser automatically.

Important: backend and frontend need their **own separate virtual environments**. Installing both sets of dependencies into one environment breaks things — Streamlit pulls in a different version of a library FastAPI depends on, and they conflict.

**Using it**: register an account, log in, go to Resume Upload, upload a resume, fill in the fields it asks for (experience, education, etc. — the parser can't reliably guess these from free text so it asks instead), click Generate Prediction + ATS Score, then check the Dashboard.

**Stopping and restarting later**: Ctrl+C in each terminal to stop. To start again, you don't need to redo any of the install steps — just reactivate each venv and rerun the start command:
```bash
cd backend && venv\Scripts\activate.bat && uvicorn app.main:app --reload
cd frontend && venv\Scripts\activate.bat && streamlit run streamlit_app.py
```

**If something goes wrong**:
- `ModuleNotFoundError: email_validator` — run `pip install email-validator`, it's not bundled with Pydantic by default.
- Errors mentioning `starlette` when running the frontend — you installed backend and frontend packages into the same environment. Use separate venvs.
- A model fails to load with an error like "input stream corrupted" — this can happen if the `.joblib` model files got mangled somewhere along the way (I've seen it happen with OneDrive-synced folders specifically). Fix: retrain them yourself, it only takes a minute —
```bash
cd ml/training
pip install pandas numpy
python generate_dataset.py
python train_role_classifier.py
python train_salary_regressor.py
```
then copy everything from `ml/artifacts/` over the matching files in `backend/app/ml_models/`, and restart the backend.

**With Docker instead**, if you have it installed:
```bash
docker compose up --build
```
This starts Postgres, the API, and the frontend together. Backend at `localhost:8000`, frontend at `localhost:8501`.

## Deploying it

**Push to GitHub first**, from the project root:
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<your-username>/<repo-name>.git
git push -u origin main
```
Keep backend and frontend in this one repo, not split into two — the Docker setup and both deployment steps below assume one shared repo with a `data/` folder both sides can see.

**Backend on Render**:
1. Render dashboard → New → PostgreSQL, create a free instance, copy the Internal Database URL.
2. New → Web Service, connect your repo. Environment: Docker. Dockerfile path: `backend/Dockerfile`. Build context: repo root (not `backend` — the Dockerfile needs to reach the `data/` folder next to it).
3. Environment variables: `DATABASE_URL` (from step 1, change `postgresql://` to `postgresql+psycopg2://` if needed), `SECRET_KEY` (generate one with `python -c "import secrets; print(secrets.token_hex(32))"`), `DEBUG=false`, and optionally `ANTHROPIC_API_KEY`.
4. Deploy, then check `https://<your-service>.onrender.com/health`.

**Frontend on Streamlit Community Cloud**:
1. share.streamlit.io → New app → pick your repo, branch `main`.
2. Main file path: `frontend/streamlit_app.py`.
3. Advanced settings → Secrets, add: `API_BASE_URL = "https://<your-render-backend>.onrender.com/api/v1"`.
4. Deploy. You get a link at `<something>.streamlit.app`.

## Testing

37 backend tests, 6 for the ML pipeline, sitting at 98% coverage on the backend. Covers the real stuff, not just happy paths — real PDF/DOCX parsing (not just plain text), auth edge cases like tampered tokens, a user not being able to access someone else's resume by guessing an ID, and the dataset generator actually being reproducible on repeated runs. Runs automatically on push through GitHub Actions, including against a real Postgres instance, not just SQLite.

```bash
cd backend
python -m pytest tests/ --cov=app --cov-report=term-missing
```

## A few things worth knowing if this comes up in an interview

- The resume parser can't reliably guess your years of experience, location, or target company type from free text, so those are entered manually rather than guessed — a wrong guess would quietly wreck both ML predictions.
- The salary/role dataset is synthetic, not scraped real postings — see the ML section above.
- The Claude-assisted messy resume recovery only kicks in when the regular parser finds fewer than 3 skills or no name — a well-formatted resume never triggers an API call, which keeps the feature from costing anything unless it's actually needed.
- No live chatbot, SHAP/LIME explainability, or resume rebuilder yet — deliberately left out rather than half-built.

## License

MIT
