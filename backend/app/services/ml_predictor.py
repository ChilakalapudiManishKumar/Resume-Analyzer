"""
ML prediction service — loads the trained models once (cached) and exposes
simple predict functions for the API routes to call.
"""
from functools import lru_cache

import pandas as pd

from app.services.feature_encoding import load_role_artifacts, load_salary_artifacts, transform_features


@lru_cache
def _role_artifacts() -> dict:
    return load_role_artifacts()


@lru_cache
def _salary_artifacts() -> dict:
    return load_salary_artifacts()


def _candidate_frame(
    skills: list[str],
    experience_years: float,
    education: str,
    num_projects: int,
    certifications: int,
    location_tier: str,
    company_type: str,
) -> pd.DataFrame:
    return pd.DataFrame([{
        "skills": skills,
        "experience_years": experience_years,
        "education": education,
        "num_projects": num_projects,
        "certifications": certifications,
        "location_tier": location_tier,
        "company_type": company_type,
    }])


def predict_role(**candidate_fields) -> dict:
    artifacts = _role_artifacts()
    df = _candidate_frame(**candidate_fields)
    X = transform_features(df, artifacts["encoders"]).reindex(
        columns=artifacts["feature_columns"], fill_value=0
    )
    probs = artifacts["model"].predict_proba(X)[0]
    label_encoder = artifacts["label_encoder"]

    role_probabilities = {
        label_encoder.classes_[i]: round(float(p), 4) for i, p in enumerate(probs)
    }
    top_idx = probs.argmax()

    return {
        "predicted_role": label_encoder.classes_[top_idx],
        "confidence": round(float(probs[top_idx]), 4),
        "role_probabilities": dict(
            sorted(role_probabilities.items(), key=lambda kv: kv[1], reverse=True)
        ),
    }


def predict_salary(**candidate_fields) -> dict:
    artifacts = _salary_artifacts()
    df = _candidate_frame(**candidate_fields)
    X = transform_features(df, artifacts["encoders"]).reindex(
        columns=artifacts["feature_columns"], fill_value=0
    )
    predicted = float(artifacts["model"].predict(X)[0])

    # +/- 15% band presented as min/max — mirrors the noise magnitude we
    # baked into the synthetic dataset, so the range is honest about the
    # model's actual uncertainty rather than an arbitrary-looking spread.
    return {
        "salary_min": round(predicted * 0.85, 2),
        "salary_avg": round(predicted, 2),
        "salary_max": round(predicted * 1.15, 2),
    }
