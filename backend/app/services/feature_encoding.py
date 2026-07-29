"""
Feature encoding for inference — must exactly match ml/training/feature_engineering.py's
encoding logic, since the models were trained on features built that way.

Why this is duplicated rather than imported from ml/training:
in a real deployment, the backend API and the ML training pipeline are
typically separate deployables (the training pipeline doesn't even need to
exist in production — it only produces artifacts). The *contract* between
them is the saved encoders + feature column order, not shared code. If you
retrain the models, you only need to re-copy the .joblib artifacts here —
you don't need the training code available at all in the API's environment.
"""
from pathlib import Path

import joblib
import pandas as pd
from sklearn.preprocessing import MultiLabelBinarizer, OneHotEncoder

MODELS_DIR = Path(__file__).resolve().parents[1] / "ml_models"

NUMERIC_COLS = ["experience_years", "num_projects", "certifications"]
CATEGORICAL_COLS = ["education", "location_tier", "company_type"]


def _split_skills(skills: list[str] | str) -> list[str]:
    if isinstance(skills, list):
        return skills
    if not skills or pd.isna(skills):
        return []
    return skills.split("|")


def transform_features(df: pd.DataFrame, encoders: dict) -> pd.DataFrame:
    mlb: MultiLabelBinarizer = encoders["skill_binarizer"]
    ohe: OneHotEncoder = encoders["categorical_encoder"]

    skill_lists = df["skills"].apply(_split_skills)
    skill_matrix = pd.DataFrame(
        mlb.transform(skill_lists),
        columns=[f"skill_{s}" for s in mlb.classes_],
        index=df.index,
    )
    cat_matrix = pd.DataFrame(
        ohe.transform(df[CATEGORICAL_COLS]),
        columns=ohe.get_feature_names_out(CATEGORICAL_COLS),
        index=df.index,
    )
    numeric_matrix = df[NUMERIC_COLS].reset_index(drop=True)
    numeric_matrix.index = df.index

    return pd.concat([numeric_matrix, cat_matrix, skill_matrix], axis=1)


def load_role_artifacts() -> dict:
    return {
        "encoders": joblib.load(MODELS_DIR / "feature_encoders.joblib"),
        "model": joblib.load(MODELS_DIR / "role_classifier.joblib"),
        "label_encoder": joblib.load(MODELS_DIR / "role_label_encoder.joblib"),
        "feature_columns": joblib.load(MODELS_DIR / "role_feature_columns.joblib"),
    }


def load_salary_artifacts() -> dict:
    return {
        "encoders": joblib.load(MODELS_DIR / "salary_feature_encoders.joblib"),
        "model": joblib.load(MODELS_DIR / "salary_regressor.joblib"),
        "feature_columns": joblib.load(MODELS_DIR / "salary_feature_columns.joblib"),
    }
