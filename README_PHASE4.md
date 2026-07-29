# Phase 4 — Frontend + Full-Stack Integration

## What changed

Two things happened this phase, not just "build the frontend":

1. **Backend got new endpoints** — Phase 2/3 only had auth + resume upload + trained models sitting in a folder. This phase added the API layer that actually serves them: predictions, ATS scoring, skill gap, roadmap, interview questions, and a dashboard aggregator.
2. **Streamlit multi-page frontend** built on top of those endpoints — Dashboard, Resume Upload, Skill Gap, Salary Insights, Roadmap, Interview Prep, with a dark theme, Plotly charts, and JWT session handling.

## Real bugs found and fixed this phase (not hidden)

1. **Skill-matching bug (Phase 2 regression)**: the resume parser matched skills via naive substring search, so single-letter skills like `"c"` and `"r"` matched inside *any* word containing that letter (`Computer`, `University`, `Science`...). Fixed with word-boundary regex. This was silently corrupting ATS scores, skill-gap results, and predictions for every resume — found via a `sklearn` warning during testing, not by inspection.
2. **Dependency conflict**: installing Streamlit and FastAPI in the same environment breaks — Streamlit pulls a newer `starlette` than FastAPI supports. This is *why* `backend/requirements.txt` and `frontend/requirements.txt` are separate — run each in its own virtual environment (see below). This isn't optional advice, it's a real conflict I hit while testing.
3. **Model/library version mismatch**: the saved `.joblib` models are tied to the exact `scikit-learn`/`xgboost` versions used at training time. `requirements.txt` is now pinned to those exact versions (1.8.0 / 3.3.0) — an unpinned or differently-pinned install will still *work* but silently risks different behavior, which is why pickled models should always travel with a version-pinned environment.

## Verified working (not just "should work")
- Full backend test suite: **19/19 passing**, run in a clean, isolated virtual environment matching `requirements.txt` exactly
- Frontend imports cleanly in its own isolated virtual environment
- Both servers actually booted together and a full integration script exercised every single page's real API calls (register → login → upload → predict → ATS score → skill gap → roadmap → interview questions → dashboard) against the live backend — all 8 steps passed

## Run it yourself

**Terminal 1 — backend:**
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

**Terminal 2 — frontend (separate venv — see dependency conflict note above):**
```bash
cd frontend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Open the Streamlit URL (usually http://localhost:8501), register, log in, then go to **Resume Upload** first (Dashboard depends on having a resume + prediction already generated).

## Known limitations (flagged honestly)
- Experience years / location tier / company type are entered manually on the upload page — the resume parser can't reliably infer these from free text (see Phase 2 notes), so we ask rather than guess.
- The frontend calls the backend via plain HTTP with no retry/loading-skeleton polish yet — fine for a portfolio demo, would need hardening for real users.

## Next: Phase 5 — Deployment
Docker + docker-compose (API + Postgres + Streamlit in one command), then deployment instructions for Render (backend) and Streamlit Community Cloud (frontend).
