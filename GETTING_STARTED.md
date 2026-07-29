# Getting Started — Complete Walkthrough (Zero to Deployed)

This assumes you have NOT opened any of the project folders yet. Follow
this top to bottom.

---

## Part 0 — Install what you need (one-time setup)

1. **Install Python 3.12** — go to https://python.org/downloads, download,
   install. On the installer, **check the box "Add Python to PATH"**
   before clicking Install (Windows) — easy to miss, causes problems later.
2. **Install VS Code** — https://code.visualstudio.com, download, install.
3. Open VS Code. Go to the Extensions icon on the left sidebar (four
   squares icon) and install **"Python"** (by Microsoft).

Check it worked: open a terminal in VS Code (menu: **Terminal → New
Terminal**, or `` Ctrl+` ``) and type:
```bash
python --version
```
You should see `Python 3.12.x`. If you see "command not found," Python
isn't on PATH — reinstall and check that box.

---

## Part 1 — Get the project into VS Code

1. Download `ai_career_intelligence_platform_COMPLETE.zip` (the file I shared).
2. Extract/unzip it somewhere easy to find, e.g. `Desktop/ai-career-intelligence`.
3. In VS Code: **File → Open Folder** → select that extracted folder.
4. You'll see this in the Explorer sidebar (left side):
   ```
   ai-career-intelligence/
   ├── backend/     <- the API server (does all the work)
   ├── frontend/    <- the website you'll actually see and click around
   ├── ml/          <- machine learning training code (you don't need to touch this — models are already trained)
   ├── data/        <- shared reference files (skills lists etc.)
   ├── docs/        <- documentation
   └── README.md    <- start here if you want the short version
   ```

You now have two things to run: **backend** (the engine) and **frontend**
(the dashboard). Backend must be running for frontend to work.

---

## Part 2 — Run the backend

Open a terminal in VS Code (**Terminal → New Terminal**). By default it
opens at the project root. Type these commands **one at a time**, pressing
Enter after each:

```bash
cd backend
python -m venv venv
```
This creates an isolated Python environment just for the backend (a
"virtual environment" — keeps this project's packages separate from
everything else on your computer).

**Activate it:**
- Mac/Linux: `source venv/bin/activate`
- Windows (PowerShell): `venv\Scripts\Activate.ps1`
- Windows (Command Prompt): `venv\Scripts\activate.bat`

You'll know it worked because your terminal line now starts with `(venv)`.

**Install the packages:**
```bash
pip install -r requirements.txt
pip install email-validator
```
This takes a minute or two — it's downloading FastAPI, the ML libraries,
etc.

**Set up the config file:**
```bash
cp .env.example .env
```
(Windows Command Prompt: use `copy .env.example .env` instead)

**Set up the database** (creates the tables, uses a simple local file — no separate database install needed):
```bash
python -m alembic upgrade head
```

**Start the backend server:**
```bash
uvicorn app.main:app --reload
```

You should see something like `Uvicorn running on http://127.0.0.1:8000`.
**Leave this terminal running** — don't close it. Open your browser and go to:
- http://127.0.0.1:8000/health → should show `{"status":"ok",...}`
- http://127.0.0.1:8000/docs → interactive API documentation

If you see those, your backend works. ✅

---

## Part 3 — Run the frontend (in a NEW, separate terminal)

**Important**: don't reuse the backend terminal — open a **second**
terminal (VS Code: click the `+` icon in the terminal panel, or
**Terminal → New Terminal** again). This second terminal needs its own
virtual environment — mixing frontend and backend packages in the same
environment causes real errors (I hit this myself while building it).

In the new terminal:
```bash
cd frontend
python -m venv venv
```
Activate it (same commands as before, just run from inside `frontend`):
- Mac/Linux: `source venv/bin/activate`
- Windows: `venv\Scripts\Activate.ps1` (or `.bat` for Command Prompt)

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Your browser should auto-open to http://localhost:8501 — that's the app.
**Register** an account, **log in**, go to **Resume Upload**, upload a
resume, fill in the extra fields, click **Generate Prediction + ATS Score**,
then check the **Dashboard**.

You now have both pieces running locally at the same time (2 terminals,
both left open).

---

## Part 4 — Stopping and restarting later

To stop either server: click in its terminal and press `Ctrl+C`.

To start again later (you don't need to reinstall anything, just activate
+ run):
```bash
# Terminal 1
cd backend
source venv/bin/activate   # or venv\Scripts\Activate.ps1 on Windows
uvicorn app.main:app --reload

# Terminal 2
cd frontend
source venv/bin/activate
streamlit run streamlit_app.py
```

---

## Part 5 — Deploying so others can access it online

This puts your backend on **Render** (free tier available) and your
frontend on **Streamlit Community Cloud** (free). You'll need a GitHub
account and to push this project to a GitHub repo first.

### 5a. Push to GitHub
1. Create a new repo on https://github.com (e.g. `ai-career-intelligence`).
2. In VS Code terminal, at the project root:
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<your-username>/<repo-name>.git
git push -u origin main
```
(If `git` isn't installed: https://git-scm.com/downloads)

### 5b. Deploy the backend on Render
1. Go to https://render.com, sign up/log in, connect your GitHub.
2. **New → PostgreSQL** — create a free Postgres database. Copy the
   **Internal Database URL** it gives you.
3. **New → Web Service** — connect your repo.
   - Environment: **Docker**
   - Dockerfile path: `backend/Dockerfile`
   - Docker build context directory: `.` (the repo root — important, don't leave it as `backend`)
   - Add environment variables:
     - `DATABASE_URL` = the Internal Database URL from step 2 (if it starts with `postgresql://`, change that prefix to `postgresql+psycopg2://`)
     - `SECRET_KEY` = any long random string (or generate one: run `python -c "import secrets; print(secrets.token_hex(32))"` locally and paste the result)
     - `DEBUG` = `false`
4. Click **Create Web Service**. Wait for it to build and deploy.
5. Once live, note your backend's URL, e.g. `https://ai-career-backend.onrender.com`. Test it: visit `https://ai-career-backend.onrender.com/health`.

### 5c. Deploy the frontend on Streamlit Community Cloud
1. Go to https://share.streamlit.io, sign in with GitHub.
2. **New app** → pick your repo, branch `main`.
3. **Main file path**: `frontend/streamlit_app.py`
4. Before deploying, click **Advanced settings → Secrets** and add:
   ```toml
   API_BASE_URL = "https://ai-career-backend.onrender.com/api/v1"
   ```
   (use YOUR actual Render URL from step 5b.5, with `/api/v1` on the end)
5. Click **Deploy**. Your app will be live at `https://<something>.streamlit.app` — share that link with anyone.

---

## If something goes wrong
- **"command not found: python"** → Python isn't installed or not on PATH — see Part 0.
- **"ModuleNotFoundError"** → you probably forgot to activate the virtual environment (check your terminal starts with `(venv)`), or forgot `pip install -r requirements.txt`.
- **Frontend shows connection errors** → make sure the backend terminal (Part 2) is still running.
- **Streamlit import errors mentioning "starlette"** → you installed frontend and backend packages in the same environment — make sure you created a SEPARATE `venv` inside `frontend/` (Part 3), not reused the backend's.
- Anything else — copy the exact error message and send it to me, I'll tell you exactly what to fix.

Full reference docs (more detail than this quick-start) are in the `docs/`
folder if you want to go deeper on any part.
