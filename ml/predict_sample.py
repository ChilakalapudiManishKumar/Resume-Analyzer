"""
Quick end-to-end sanity check: build a fake candidate, run both trained
models, and print the predictions with confidence — proves the full
train -> save -> load -> predict pipeline actually works, the same way
predict.py did for the placement project.

Edit the `candidate` dict below and re-run to try different profiles.
"""
from pathlib import Path

import joblib
import pandas as pd

ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent / "training"))
from feature_engineering import transform_features  # noqa: E402

candidate = {
    "experience_years": 2.5,
    "education": "Masters",
    "num_projects": 5,
    "certifications": 1,
    "location_tier": "Tier-1",
    "company_type": "Product-based",
    "skills": "python|scikit-learn|tensorflow|machine learning|deep learning|sql",
}


def predict_role(df: pd.DataFrame) -> None:
    encoders = joblib.load(ARTIFACTS_DIR / "feature_encoders.joblib")
    model = joblib.load(ARTIFACTS_DIR / "role_classifier.joblib")
    label_encoder = joblib.load(ARTIFACTS_DIR / "role_label_encoder.joblib")
    feature_columns = joblib.load(ARTIFACTS_DIR / "role_feature_columns.joblib")

    X = transform_features(df, encoders).reindex(columns=feature_columns, fill_value=0)
    probs = model.predict_proba(X)[0]
    pred_idx = probs.argmax()

    print("\n--- Job Role Prediction ---")
    print(f"Predicted role: {label_encoder.classes_[pred_idx]}  (confidence: {probs[pred_idx]:.1%})")
    top3_idx = probs.argsort()[::-1][:3]
    print("Top 3 probabilities:")
    for i in top3_idx:
        print(f"  {label_encoder.classes_[i]:<28} {probs[i]:.1%}")


def predict_salary(df: pd.DataFrame) -> None:
    encoders = joblib.load(ARTIFACTS_DIR / "salary_feature_encoders.joblib")
    model = joblib.load(ARTIFACTS_DIR / "salary_regressor.joblib")
    feature_columns = joblib.load(ARTIFACTS_DIR / "salary_feature_columns.joblib")

    X = transform_features(df, encoders).reindex(columns=feature_columns, fill_value=0)
    pred = model.predict(X)[0]

    print("\n--- Salary Prediction ---")
    print(f"Predicted salary: {pred:.2f} LPA  (range estimate: {pred * 0.85:.2f} - {pred * 1.15:.2f} LPA)")


if __name__ == "__main__":
    df = pd.DataFrame([candidate])
    print("Candidate profile:", candidate)
    predict_role(df)
    predict_salary(df)
