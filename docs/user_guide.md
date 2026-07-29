# User Guide

## Getting started

1. Open the app (locally: http://localhost:8501, or your deployed Streamlit Cloud URL).
2. **Register** on the landing page (email, password, full name), then switch to the **Log in** tab and log in.
3. Go to **Resume Upload** in the sidebar.

## 1. Resume Upload
- Upload a `.pdf`, `.docx`, or `.txt` resume (max 5MB).
- The app extracts your name, email, phone, and recognized skills automatically — review these before continuing (automatic extraction isn't perfect).
- Fill in the fields the parser can't reliably read from free text: **years of experience, education level, number of projects, certifications, location tier** (Tier-1 = Bangalore/Hyderabad/Pune/Mumbai/Delhi-NCR etc.), and **target company type**.
- Click **Generate Prediction + ATS Score**.

## 2. Dashboard
- Shows your ATS score, predicted job role (with confidence %), and predicted salary range (LPA) as headline metric cards.
- Below that: a role-probability chart (how confident the model is across all 14 roles, not just the top pick) and a salary range chart.
- An expandable **Improvement suggestions** section lists concrete ATS fixes (e.g. missing sections, too few action verbs).

## 3. Skill Gap
- Pick any target role from the dropdown (doesn't have to match your predicted role — useful if you're considering a pivot).
- Shows a readiness percentage, which of your skills match, which are missing, and a suggested learning order.

## 4. Salary Insights
- A more detailed view of the salary prediction: min/average/max, and a short explanation of what factors drove the estimate.

## 5. Roadmap
- For your chosen target role's missing skills, get a study plan per skill: description, why it matters, estimated learning time, difficulty, and curated free/paid resources, YouTube channels, and practice sites.

## 6. Interview Prep
- Defaults to your predicted role, but you can pick any role.
- Questions are grouped into tabs: Technical, Coding, HR, Behavioral, Scenario, System Design. Click a question to reveal a model answer.
- Note: Coding and System Design tabs are empty for non-engineering roles (Product Manager, UI/UX Designer, Business Analyst) — deliberate, not a bug, since those question types aren't relevant there.

## Tips
- You can re-run **Generate Prediction** anytime with updated inputs (e.g. after gaining more experience) — it updates your existing prediction rather than creating a duplicate.
- The ATS score and skill gap are both explainable by design — every point/gap traces back to a specific, visible rule, not a black-box model.
