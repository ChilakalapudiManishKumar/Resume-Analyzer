"""
Shared feature engineering for role classification + salary regression.

Why one shared module instead of duplicating this in each training script:
at inference time (when a real resume comes in through the API), we need
to encode it into features EXACTLY the same way both models were trained —
same skill vocabulary, same column order, same categorical encoding. Having
one function used by training, evaluation, and (later) the prediction
service guarantees that instead of hoping two copies stay in sync.

Encoding choices:
- Skills -> multi-hot (MultiLabelBinarizer). Skills are a variable-length
  set per candidate, not ordinal or single-valued, so one binary column
  per skill ("has_python", "has_sql", ...) is the standard approach.
- education / location_tier / company_type -> one-hot (OneHotEncoder).
  These are categorical with no meaningful order, and one-hot keeps both
  tree-based models (RF/XGBoost) and the linear baseline comparable.
- experience_years / num_projects / certifications -> used as-is (numeric).
"""
from pathlib import Path

import joblib
import pandas as pd
from sklearn.preprocessing import MultiLabelBinarizer, OneHotEncoder

ARTIFACTS_DIR = Path(__file__).resolve().parents[1] / "artifacts"

NUMERIC_COLS = ["experience_years", "num_projects", "certifications"]
CATEGORICAL_COLS = ["education", "location_tier", "company_type"]


def _split_skills(skills_str: str) -> list[str]:
    if not skills_str or pd.isna(skills_str):
        return []
    return skills_str.split("|")


def fit_encoders(df: pd.DataFrame) -> dict:
    """Fit encoders on the training dataset. Returns a dict of fitted encoders."""
    skill_lists = df["skills"].apply(_split_skills)

    mlb = MultiLabelBinarizer()
    mlb.fit(skill_lists)

    ohe = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    ohe.fit(df[CATEGORICAL_COLS])

    return {"skill_binarizer": mlb, "categorical_encoder": ohe}


def transform_features(df: pd.DataFrame, encoders: dict) -> pd.DataFrame:
    """Apply fitted encoders to produce the final numeric feature matrix."""
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


def save_encoders(encoders: dict, filename: str = "feature_encoders.joblib") -> Path:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    path = ARTIFACTS_DIR / filename
    joblib.dump(encoders, path)
    return path


def load_encoders(filename: str = "feature_encoders.joblib") -> dict:
    return joblib.load(ARTIFACTS_DIR / filename)
