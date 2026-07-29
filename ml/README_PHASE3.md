# Phase 3 — Machine Learning

**Updated after the initial build**: dataset size was increased from 200 to
2,000 records per role (2,800 → 28,000 total) after discussing whether 200
was sufficient. Real before/after comparison, not assumed:

| Model | Metric | @200/role | @2000/role |
|---|---|---|---|
| Role classifier (Logistic Regression) | Accuracy / Macro F1 | 95.5% / 0.9554 | 95.5% / 0.9546 (flat) |
| Salary regressor (XGBoost) | R² / RMSE | 0.922 / 1.556 | **0.949 / 1.337** (improved) |

**Honest finding**: more data improved salary regression noticeably but left
role classification essentially unchanged — including the Cloud
Engineer/DevOps Engineer confusion pair (still ~74-76% precision). This
makes sense: that confusion comes from genuine skill-set overlap baked into
the role definitions themselves, not from having too few examples — more
data of the same distribution can't separate two classes whose *features*
overlap. Salary, by contrast, is a smoother numeric relationship that
benefits from more examples to average out noise. Worth knowing the
difference between a data-quantity problem and a feature-overlap problem.

## What's included and verified working

### 1. Synthetic dataset (`ml/datasets/career_dataset_synthetic.csv`)
- 28,000 records across 14 job roles (2,000 each)
- Features: skills (multi-label), experience, education, projects, certifications, location tier, company type
- Salary (LPA) computed from an explicit, explainable formula — not scraped, not arbitrary
- Deliberate skill overlap between adjacent roles (e.g. Cloud Engineer / DevOps Engineer) to make the classification problem genuinely realistic, the same way the placement dataset used deliberate noise

Regenerate anytime: `python ml/training/generate_dataset.py`

### 2. Job Role Classifier
Compared Logistic Regression, Random Forest, XGBoost — selected by **macro-F1** (not plain accuracy, since it fairly weighs harder-to-separate roles).

| Model | Accuracy | Macro F1 |
|---|---|---|
| **Logistic Regression (winner)** | 95.46% | 0.9546 |
| Random Forest | 95.45% | 0.9544 |
| XGBoost | 95.34% | 0.9534 |

Notable, honest finding: Cloud Engineer and DevOps Engineer remain the two weakest classes (precision/recall ~0.74–0.78) even at 10x the data — because their skill sets (Docker, Kubernetes, Terraform, AWS, CI/CD) genuinely overlap in real life too. This is a good talking point in an interview, not a flaw to hide.

### 3. Salary Regressor
Compared Linear Regression, Random Forest, XGBoost — selected by R².

| Model | RMSE (LPA) | MAE (LPA) | R² |
|---|---|---|---|
| **XGBoost (winner)** | 1.337 | 0.953 | 0.9485 |
| Random Forest | 1.834 | 1.299 | 0.9031 |
| Linear Regression | 1.999 | 1.396 | 0.8848 |

Typical prediction is within ~₹0.95–1.3 lakhs of actual — improved from ~₹1.1–1.5 lakhs at the smaller dataset size.

### 4. Explainability (lightweight, built into the models)
Top salary drivers: product-management skill, ML/deep-learning skills, experience, location tier, company type — all sensible. Full SHAP/LIME deferred to the bonus phase (Phase 1 scope note) since built-in feature importances already give an honest, interview-ready explanation without adding dependency overhead now.

### 5. End-to-end sanity check
`ml/predict_sample.py` loads both saved models and predicts on a fake candidate — proves the full train → save → load → predict pipeline works, not just that training completes.

## Run it yourself
```bash
cd ml
pip install scikit-learn xgboost pandas numpy joblib
python training/generate_dataset.py
cd training && python train_role_classifier.py && python train_salary_regressor.py
cd ../evaluation && python compare_models.py
cd .. && python predict_sample.py
```

## Files produced
```
ml/
├── datasets/career_dataset_synthetic.csv
├── artifacts/
│   ├── role_classifier.joblib, role_label_encoder.joblib, role_feature_columns.joblib
│   ├── salary_regressor.joblib, salary_feature_columns.joblib
│   ├── feature_encoders.joblib, salary_feature_encoders.joblib
│   └── role_model_comparison.csv, salary_model_comparison.csv
```

## Next: Phase 4 — Frontend
Wire these saved models + the Phase 2 FastAPI backend into a multi-page Streamlit app (Dashboard, Resume Upload, Skill Gap, Salary Insights, Roadmap, Interview Prep) with Plotly charts.
